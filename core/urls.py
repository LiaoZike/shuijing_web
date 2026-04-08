from django.urls import path
from core import views

urlpatterns = [
    path('', views.home, name='home'),
    path('my/registrations/', views.my_registrations, name='my_registrations'),
    path('my/registrations/<int:pk>/', views.my_registration_detail, name='my_registration_detail'),
    path('events/', views.event_list, name='event_list'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/register/', views.event_register, name='event_register'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    path('story/', views.story, name='story'),
    path('usr/', views.usr_page, name='usr'),
    path('search/', views.global_search, name='global_search'),
]
