from django.shortcuts import get_object_or_404, redirect, render
from .models import HeroSlide, Registration,ServiceItem,Activity,Participant
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField, Q
from allauth.account.signals import user_logged_in, user_logged_out
from django.contrib import messages
from django.dispatch import receiver
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings

@receiver(user_logged_in)
def on_login(request, user, **kwargs):
    storage = messages.get_messages(request)
    storage.used = True
    name = user.first_name or user.email
    messages.success(request, f'歡迎回來，{name}！')

@receiver(user_logged_out)
def on_logout(request, user, **kwargs):
    messages.success(request, '已成功登出，期待您再次造訪。')

def home(request):
    slides   = HeroSlide.objects.filter(is_active=True)
    services = ServiceItem.objects.filter(is_active=True)
    today    = timezone.now().date()

    activities = Activity.objects.filter(is_active=True).annotate(
        is_past=Case(
            # 有結束日期 → 看結束日期是否已過
            When(end_date__isnull=False, end_date__lt=today, then=Value(1)),
            # 沒結束日期 → 看開始日期是否已過
            When(end_date__isnull=True, date__lt=today, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by(
        'is_past',
        '-is_featured',
        '-date',
    )[:4]

    return render(request, 'core/home.html', {
        'slides':     slides,
        'services':   services,
        'activities': activities,
        'today':      today,
    })




def event_list(request):
    today = timezone.now().date()
    # 搜尋
    query    = request.GET.get('q', '')
    status   = request.GET.get('status', 'all')

    activities = Activity.objects.filter(is_active=True)

    # 關鍵字搜尋（標題、描述、地點、標籤）
    if query:
        activities = activities.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(tags__icontains=query)
        )

    # 狀態篩選
    if status == 'upcoming':
        activities = activities.filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True, date__gte=today)
        ).order_by('date')
    elif status == 'past':
        activities = activities.filter(
            Q(end_date__lt=today) | Q(end_date__isnull=True, date__lt=today)
        ).order_by('-date')
    else:
        activities = activities.annotate(
            is_past_flag=Case(
                When(Q(end_date__lt=today) | Q(end_date__isnull=True, date__lt=today), then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('is_past_flag', '-is_featured', 'date')

    # 分頁
    paginator = Paginator(activities, settings.ACTIVITIES_PER_PAGE)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)
    return render(request, 'core/event_list.html', {
        'page_obj':  page_obj,
        'query':     query,
        'status':    status,
        'today':     today,
    })


def event_detail(request, pk):
    from django.shortcuts import get_object_or_404
    activity = get_object_or_404(Activity, pk=pk, is_active=True)
    today    = timezone.now().date()

    return render(request, 'core/event_detail.html', {
        'activity': activity,
        'today':    today
    })

@login_required(login_url='/accounts/google/login/')
def event_register(request, pk):
    activity = get_object_or_404(Activity, pk=pk, is_active=True)

    # GET → 顯示表單
    if request.method == 'GET':
        # 先做基本檢查，不能報名就跳回去
        if activity.is_past():
            messages.error(request, '此活動已結束，無法報名。')
            return redirect('event_detail', pk=pk)
        if not activity.is_registration_open():
            messages.error(request, '報名已截止。')
            return redirect('event_detail', pk=pk)
        if Registration.objects.filter(activity=activity, user=request.user).exists():
            messages.warning(request, '你已經報名過此活動了！')
            return redirect('event_detail', pk=pk)
        return render(request, 'core/event_register.html', {
            'activity': activity,
            'user': request.user,
        })
    if request.method != 'POST':
        return redirect('event_detail', pk=pk)
    # ── 報名者本人資料 ──
    name              = request.POST.get('name', '').strip()
    phone             = request.POST.get('phone', '').strip()
    email             = request.POST.get('email', '').strip()
    note              = request.POST.get('note', '').strip()
    # ── 同行人資料（動態列）──
    # 前端傳來 companion_name_1, companion_phone_1, companion_email_1 ...
    companions = []
    i = 1
    while True:
        c_name  = request.POST.get(f'companion_name_{i}', '').strip()
        c_phone = request.POST.get(f'companion_phone_{i}', '').strip()
        c_email = request.POST.get(f'companion_email_{i}', '').strip()
        if not c_name:
            break
        companions.append({'name': c_name, 'phone': c_phone, 'email': c_email})
        i += 1

    participant_count = 1 + len(companions)  # 本人 + 同行人

    # ── 驗證 ──
    if not name or not phone:
        messages.error(request, '姓名和電話為必填。')
        return redirect('event_detail', pk=pk)
    for idx, c in enumerate(companions, 1):
        if not c['phone']:
            messages.error(request, f'第 {idx} 位同行人電話為必填。')
            return redirect('event_detail', pk=pk)
    if activity.is_past():
        messages.error(request, '此活動已結束，無法報名。')
        return redirect('event_detail', pk=pk)
    if not activity.is_registration_open():
        messages.error(request, '報名已截止。')
        return redirect('event_detail', pk=pk)
    if Registration.objects.filter(activity=activity, user=request.user).exists():
        messages.warning(request, '你已經報名過此活動了！')
        return redirect('event_detail', pk=pk)
    if activity.max_participants:
        remaining = activity.remaining_spots()
        if participant_count > remaining:
            messages.error(request, f'剩餘名額只剩 {remaining} 位，無法報名 {participant_count} 人。')
            return redirect('event_detail', pk=pk)

    # ── 建立報名記錄 ──
    registration = Registration.objects.create(
        activity          = activity,
        user              = request.user,
        name              = name,
        phone             = phone,
        email             = email or request.user.email,
        participant_count = participant_count,
        note              = note,
    )

    # ── 建立同行人記錄 ──
    for c in companions:
        Participant.objects.create(
            registration = registration,
            name         = c['name'],
            phone        = c['phone'],
            email        = c['email'],
        )

    messages.success(request, f'已成功報名「{activity.title}」，共 {participant_count} 人！')
    return redirect('event_detail', pk=pk)

def story(request):
    return render(request, 'core/story.html')
def usr_page(request):
    return render(request, 'core/usr.html')

def about(request):
    return render(request, 'core/about.html')
def contact(request):    
    return render(request, 'core/contact.html')
