from django.shortcuts import render
from .models import HeroSlide,ServiceItem,Activity
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from allauth.account.signals import user_logged_in, user_logged_out
from django.contrib import messages
from django.dispatch import receiver


@receiver(user_logged_in)
def on_login(request, user, **kwargs):
    # 清掉 allauth 原本的訊息
    storage = messages.get_messages(request)
    storage.used = True
    # 換成自己的
    name = user.first_name or user.email
    messages.success(request, f'歡迎回來，{name}！')

@receiver(user_logged_out)
def on_logout(request, user, **kwargs):
    messages.success(request, '已成功登出，期待您再次造訪。')
    
# def home(request):
#     slides = HeroSlide.objects.filter(is_active=True)
#     return render(request, 'core/home.html', {'slides': slides})

def home(request):
    slides     = HeroSlide.objects.filter(is_active=True)
    services   = ServiceItem.objects.filter(is_active=True)
    today      = timezone.now().date()
    activities = Activity.objects.filter(
        is_active=True
    ).annotate(
        is_past=Case(
            When(date__lt=today, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('is_past', '-is_featured', 'date')[:4]

    return render(request, 'core/home.html', {
        'slides':     slides,
        'services':   services,
        'activities': activities,
        'today':      today,
    })