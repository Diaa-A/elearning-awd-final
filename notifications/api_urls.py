"""
REST API URL configuration for the notifications application.

Uses DRF DefaultRouter to generate URL patterns for notification
listing, detail, and mark-as-read endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import NotificationViewSet

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='api-notification')

urlpatterns = [
    path('', include(router.urls)),
]
