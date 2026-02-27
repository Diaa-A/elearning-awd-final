"""
REST API URL configuration for the chat application.

Uses DRF DefaultRouter to generate URL patterns for chat room
and message endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import ChatRoomViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='api-chatroom')
router.register(r'messages', MessageViewSet, basename='api-message')

urlpatterns = [
    path('', include(router.urls)),
]
