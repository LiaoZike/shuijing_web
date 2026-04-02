from django.urls import path
from core import views

urlpatterns = [
    path('', views.home, name='home'),
    path('events/', views.event_list, name='event_list'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/register/', views.event_register, name='event_register'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
