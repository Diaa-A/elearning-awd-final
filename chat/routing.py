"""
WebSocket URL routing for the chat application.

Maps WebSocket connection paths to their corresponding consumer classes.
Direct messages and course group chats each have their own consumer.
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/chat/dm/(?P<room_id>\d+)/$',
        consumers.DirectChatConsumer.as_asgi()
    ),
    re_path(
        r'ws/chat/course/(?P<course_id>\d+)/$',
        consumers.GroupChatConsumer.as_asgi()
    ),
]
