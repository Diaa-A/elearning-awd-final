"""
URL configuration for the chat application.

Maps URL patterns to views for chat room listing and chat access.
WebSocket URLs are defined separately in routing.py.
"""

from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.ChatRoomListView.as_view(),
        name='chat-room-list',
    ),
    path(
        'dm/<int:user_id>/',
        views.DirectMessageView.as_view(),
        name='chat-dm',
    ),
    path(
        'course/<int:course_id>/',
        views.CourseGroupChatView.as_view(),
        name='chat-course',
    ),
]
