from django.shortcuts import render, redirect
from django.http import Http404

# Create your views here.
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import logout


def login_portal(request):
    if request.user.is_authenticated:
        return redirect('home')
    next_url = request.GET.get('next', '/')
    request.session['login_next'] = next_url
    return render(request, 'account/login_portal.html')

def popup_done(request):
    return render(request, 'account/popup_done.html')

def auth_status(request):
    return JsonResponse({'authenticated': request.user.is_authenticated})

def google_popup_start(request):
    from allauth.socialaccount.providers.google.views import oauth2_login
    # popup-done 當作 next，登入完回來就能 window.close()
    request.session['socialaccount_next'] = '/login/popup-done/'
    return oauth2_login(request)

def abort404(request):
    raise Http404("找不到資料")

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('home')