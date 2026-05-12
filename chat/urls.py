from django.urls import path

from . import views

urlpatterns = [
    path("", views.chat_page, name="chat-page"),
    path("api/chat/", views.chat_api, name="chat-api"),
    path("api/chat/clear/", views.clear_api, name="chat-clear"),
]
