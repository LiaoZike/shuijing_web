"""
URL configuration for shuijing project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from accounts import views  # 或 from your_app import views
from allauth.socialaccount.providers.google.views import oauth2_login, oauth2_callback

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/login/',views.abort404),
    
    path('accounts/google/login/', oauth2_login, name='google_login'),
    path('accounts/google/login/callback/', oauth2_callback, name='google_callback'),
    path('accounts/logout/', views.logout_view, name='logout'),

    path('', include('core.urls')),
    path('login/', views.login_portal, name='login_portal'),
    path('login/popup-done/', views.popup_done, name='popup_done'),
    path('auth-status/', views.auth_status, name='auth_status'),
    # path('auth/google/popup/', views.google_popup_start, name='google_popup_start'),
]
