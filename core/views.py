from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField, Q
from django.contrib import messages
from django.dispatch import receiver
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from allauth.account.signals import user_logged_in, user_logged_out
from .models import (
    HeroSlide,
    Registration,
    ServiceItem,
    Activity,
    Participant,
    ContactMessage,
    AiotProject,
    UsrAchievement,
    Notice,
    RelatedLink,
)
from water.models import Pond
from water.utils import reading_status

import threading


@receiver(user_logged_in)
def on_login(request, user, **kwargs):
    """使用者登入後顯示歡迎訊息。"""
    if request is None:
        return
    storage = messages.get_messages(request)
    storage.used = True
    name = user.first_name or user.email
    messages.success(request, f'歡迎回來，{name}！')


@receiver(user_logged_out)
def on_logout(request, user, **kwargs):
    """使用者登出後顯示提示訊息。"""
    if request is None:
        return
    messages.success(request, '已成功登出，期待您再次造訪。')


def home(request):
    """首頁：顯示輪播圖、服務項目與近期活動。"""
    today = timezone.now().date()

    slides = HeroSlide.objects.filter(is_active=True)
    services = ServiceItem.objects.filter(is_active=True)
    activities = (
        Activity.objects.filter(is_active=True)
        .annotate(
            is_past=Case(
                When(end_date__isnull=False, end_date__lt=today, then=Value(1)),
                When(end_date__isnull=True, date__lt=today, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .order_by('is_past', '-is_featured', '-date')[:4]
    )

    notices = Notice.objects.filter(is_active=True).order_by('-publish_date')[:7]
    achievements = UsrAchievement.objects.filter(is_active=True).order_by('-date')[:3]
    water_preview = []
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            preview_ponds = Pond.objects.all().order_by('name')[:3]
        else:
            preview_ponds = (
                Pond.objects.filter(owners=request.user)
                .distinct()
                .order_by('name')[:3]
            )

        for pond in preview_ponds:
            latest = pond.readings.first()
            water_preview.append({
                'pond': pond,
                'reading': latest,
                'status': reading_status(latest),
            })

    return render(request, 'core/home.html', {
        'slides': slides,
        'services': services,
        'activities': activities,
        'notices': notices,
        'achievements': achievements,
        'water_preview': water_preview,
        'today': today,
    })


def event_list(request):
    """活動列表頁：支援關鍵字搜尋、狀態篩選與分頁。"""
    today = timezone.now().date()
    query = request.GET.get('q', '')
    status = request.GET.get('status', 'upcoming')

    activities = Activity.objects.filter(is_active=True)

    if query:
        activities = activities.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(tags__icontains=query)
        )

    if status == 'upcoming':
        activities = activities.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True, date__gte=today)
        ).order_by('date')

    elif status == 'past':
        activities = activities.filter(
            Q(end_date__lt=today) | Q(end_date__isnull=True, date__lt=today)
        ).order_by('-date')

    else:
        upcoming = activities.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True, date__gte=today)
        ).order_by('-is_featured', 'date')

        past = activities.filter(
            Q(end_date__lt=today) | Q(end_date__isnull=True, date__lt=today)
        ).order_by('-date')

        # 合併：未來在前，已結束在後
        from itertools import chain
        activities = list(chain(upcoming, past))

    paginator = Paginator(activities, settings.ACTIVITIES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'core/event_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'today': today,
    })

def event_detail(request, pk):
    activity = get_object_or_404(Activity, pk=pk, is_active=True)
    today = timezone.now().date()

    user_registration = None
    is_full = False

    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(
            activity=activity, user=request.user
        ).first()

    # 已報名的人不受額滿影響，所以在確認 user_registration 之後再判斷
    if activity.max_participants:
        is_full = activity.remaining_spots() <= 0

    # 候補可用：額滿但仍開放報名，且開放候補
    is_waitlist_available = is_full and activity.is_registration_open() and activity.allow_waitlist

    # 顯示用的報名人數，不超過上限
    displayed_count = None
    if activity.max_participants:
        displayed_count = min(activity.registration_count(), activity.max_participants)

    related = Activity.objects.filter(
        is_active=True
    ).exclude(pk=pk).order_by('-is_featured', 'date')[:3]

    return render(request, 'core/event_detail.html', {
        'activity':              activity,
        'today':                 today,
        'is_full':               is_full,
        'is_waitlist_available':  is_waitlist_available,
        'user_registration':     user_registration,
        'related':               related,
        'displayed_count':       displayed_count,
    })


def _get_companions_from_post(request):
    """從表單中整理同行人資料。"""
    companions = []
    i = 1

    while True:
        name = request.POST.get(f'companion_name_{i}', '').strip()
        phone = request.POST.get(f'companion_phone_{i}', '').strip()
        email = request.POST.get(f'companion_email_{i}', '').strip()

        if not name:
            break

        companions.append({
            'name': name,
            'phone': phone,
            'email': email,
        })
        i += 1

    return companions


def _validate_event_registration(activity, user, name, phone, companions):
    """檢查活動報名資料是否合法（不再檢查名額，名額由 view 判斷 confirmed/waitlist）。"""
    if activity.link_url:
        return '抱歉! 此活動採外部報名（請見詳情頁連結），本站不開放直接報名。'

    if not name or not phone:
        return '抱歉! 姓名和電話為必填。'

    max_per_user = activity.max_per_user
    if max_per_user and len(companions) + 1 > max_per_user:
        return f'抱歉! 每帳號最多報名 {max_per_user} 人。'
    for idx, companion in enumerate(companions, start=1):
        if not companion['phone']:
            return f'抱歉! 第 {idx} 位同行人電話為必填。'

    if activity.is_past():
        return '抱歉! 此活動已結束，無法報名。'

    if not activity.is_registration_open():
        return '抱歉! 報名已截止。'

    if Registration.objects.filter(activity=activity, user=user).exists():
        return '抱歉! 你已經報名過此活動了！'

    participant_count = 1 + len(companions)
    if activity.max_participants:
        remaining = activity.remaining_spots()
        if participant_count > remaining:
            if not getattr(activity, 'allow_waitlist', False):
                return f'抱歉! 剩餘名額只剩 {remaining} 位，無法報名 {participant_count} 人。'

    return None


@login_required(login_url='/accounts/google/login/')
def event_register(request, pk):
    """活動報名頁：GET 顯示表單，POST 建立報名與同行人資料。"""
    activity = get_object_or_404(Activity, pk=pk, is_active=True)

    if request.method == 'GET':
        error_message = _validate_event_registration(
            activity=activity,
            user=request.user,
            name='temp',
            phone='temp',
            companions=[],
        )
        if error_message and error_message != '姓名和電話為必填。':
            if '已經報名過' in error_message:
                messages.warning(request, error_message)
            else:
                messages.error(request, error_message)
            return redirect('event_detail', pk=pk)

        return render(request, 'core/event_register.html', {
            'activity': activity,
            'user': request.user,
        })

    if request.method != 'POST':
        return redirect('event_detail', pk=pk)

    name = request.POST.get('name', '').strip()
    phone = request.POST.get('phone', '').strip()
    email = request.POST.get('email', '').strip()
    note = request.POST.get('note', '').strip()
    companions = _get_companions_from_post(request)

    error_message = _validate_event_registration(
        activity=activity,
        user=request.user,
        name=name,
        phone=phone,
        companions=companions,
    )

    if error_message:
        if '已經報名過' in error_message:
            messages.warning(request, error_message)
        else:
            messages.error(request, error_message)
        return redirect('event_detail', pk=pk)

    participant_count = 1 + len(companions)

    # 決定報名狀態：confirmed or waitlist
    status = 'confirmed'
    if activity.max_participants:
        remaining = activity.remaining_spots()
        if participant_count > remaining:
            status = 'waitlist'

    registration = Registration.objects.create(
        activity=activity,
        user=request.user,
        name=name,
        phone=phone,
        email=email or request.user.email,
        participant_count=participant_count,
        status=status,
        note=note,
    )

    for companion in companions:
        Participant.objects.create(
            registration=registration,
            name=companion['name'],
            phone=companion['phone'],
            email=companion['email'],
        )

    if status == 'waitlist':
        messages.info(request, f'已加入「{activity.title}」候補名單，共 {participant_count} 人。若有名額釋出將通知您！')
    else:
        messages.success(request, f'已成功報名「{activity.title}」，共 {participant_count} 人！')
    return redirect('event_detail', pk=pk)


def story(request):
    """故事頁。"""
    return render(request, 'core/story.html')


def about(request):
    """關於我們頁面。"""
    return render(request, 'core/about.html')


def send_contact_email_async(name, email, phone, subject, message_text):
    """背景寄送聯絡表單通知信，避免阻塞使用者請求。"""
    try:
        send_mail(
            subject=f'【風雲客棧數位平台聯絡表單】{subject}',
            message=(
                f'姓名：{name}\n'
                f'信箱：{email}\n'
                f'電話：{phone or "未填"}\n'
                f'主旨：{subject}\n\n'
                f'訊息內容：\n{message_text}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Error sending email: {e}')


def contact(request):
    """聯絡我們頁面：接收表單、寫入資料庫，並背景寄送通知信。"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not name or not email or not subject or not message_text:
            messages.error(request, '請填寫所有必填欄位。')
            return render(request, 'core/contact.html', {
                'form_data': request.POST
            })

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message_text,
        )

        threading.Thread(
            target=send_contact_email_async,
            args=(name, email, phone, subject, message_text),
            daemon=True,
        ).start()

        messages.success(request, '訊息已送出，我們會盡快與您聯繫！')
        return redirect('contact')

    return render(request, 'core/contact.html', {
        'form_data': {}
    })



@login_required(login_url='/accounts/google/login/')
def my_registrations(request):
    filter_param = request.GET.get('filter', 'all')
    today = timezone.now().date()
 
    registrations = Registration.objects.filter(
        user=request.user
    ).select_related('activity').order_by('activity__date')
 
    if filter_param == 'upcoming':
        registrations = registrations.filter(
            Q(activity__end_date__gte=today) |
            Q(activity__end_date__isnull=True, activity__date__gte=today)
        )
    elif filter_param == 'past':
        registrations = registrations.filter(
            Q(activity__end_date__lt=today) |
            Q(activity__end_date__isnull=True, activity__date__lt=today)
        )
 
    return render(request, 'core/my_registrations.html', {
        'registrations': registrations,
        'filter': filter_param,
    })
 

@login_required(login_url='/accounts/google/login/')
def my_registration_detail(request, pk):
    registration = get_object_or_404(Registration, pk=pk, user=request.user)
    participants = registration.participants.all()
    return render(request, 'core/my_registration_detail.html', {
        'registration': registration,
        'participants': participants,
    })

# USR
def usr_page(request):
    from .models import AiotProject, UsrAchievement, UsrVideo, UsrTeamMember

    aiot_projects = AiotProject.objects.filter(is_active=True).order_by('order')
    achievements = UsrAchievement.objects.filter(is_active=True).order_by('-date')
    videos_list = UsrVideo.objects.filter(is_active=True).prefetch_related('images').order_by('-date')  # ← 加這個
    team_members = UsrTeamMember.objects.filter(is_active=True).order_by('order')

    from django.core.paginator import Paginator
    paginator = Paginator(videos_list, 6)
    page_number = request.GET.get('vpage', 1)
    videos_page = paginator.get_page(page_number)

    context = {
        'page_title': 'USR 成果・虎科大 × 水井村',
        'aiot_projects': aiot_projects,
        'achievements': achievements,
        'videos_page': videos_page,
        'team_members': team_members,
    }
    return render(request, 'usr/usr.html', context)


def global_search(request):
    """全站搜尋：跨資料表查詢活動、AIoT 計畫、USR 師生成果。"""
    query = request.GET.get('q', '').strip()
    today = timezone.now().date()

    activities = []
    aiot_results = []
    usr_results = []
    link_results = []

    if query:
        # 搜尋：活動 (Activity)
        activities = Activity.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(title_2__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-date')[:10]

        # 搜尋：AIoT 科技計畫 (AiotProject)
        aiot_results = AiotProject.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('order')[:8]

        # 搜尋：USR 師生實踐成果 (UsrAchievement)
        usr_results = UsrAchievement.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        ).order_by('-date')[:8]

        # 搜尋：相關連結 (RelatedLink)
        link_results = RelatedLink.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        ).order_by('order')[:8]

    total_count = len(activities) + len(aiot_results) + len(usr_results) + len(link_results)

    return render(request, 'core/search_results.html', {
        'query': query,
        'activities': activities,
        'aiot_results': aiot_results,
        'usr_results': usr_results,
        'link_results': link_results,
        'total_count': total_count,
        'today': today,
    })
# --- 公告 Notice ---
def notice_list(request):
    """公告列表頁，支援分類篩選。"""
    category = request.GET.get('category')
    notices_list = Notice.objects.filter(is_active=True).order_by('-publish_date')
    
    if category and category in dict(Notice.CATEGORY_CHOICES):
        notices_list = notices_list.filter(category=category)
        
    paginator = Paginator(notices_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'core/notice_list.html', {
        'page_obj': page_obj,
        'current_category': category,
        'categories': Notice.CATEGORY_CHOICES
    })
    
def notice_detail(request, pk):
    """公告詳情頁。"""
    notice = get_object_or_404(Notice, pk=pk, is_active=True)
    return render(request, 'core/notice_detail.html', {
        'notice': notice
    })

def related_links_page(request):
    """在地連結頁面：顯示所有在地商家與 USR 相關連結。"""
    links = RelatedLink.objects.filter(is_active=True).order_by('order')
    
    # 也可以在 View 內先分好類，方便前端顯示
    local_links = links.filter(category='local')
    usr_links = links.filter(category='usr')

    return render(request, 'core/related_links.html', {
        'local_links': local_links,
        'usr_links': usr_links,
        'page_title': '在地商家與相關連結',
    })
