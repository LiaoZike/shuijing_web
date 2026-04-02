from django.urls import path
from . import views

app_name = 'guide'

urlpatterns = [
    path('', views.guide_home, name='home'),
    path('category/<str:category>/', views.guide_category, name='category'),
    path('<slug:slug>/', views.guide_detail, name='detail'),
]