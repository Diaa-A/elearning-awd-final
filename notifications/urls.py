"""
URL configuration for the notifications application.

Maps URL patterns to views for notification listing and management.
"""

from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.NotificationListView.as_view(),
        name='notification-list',
    ),
    path(
        '<int:pk>/read/',
        views.mark_read,
        name='notification-read',
    ),
    path(
        'mark-all-read/',
        views.mark_all_read,
        name='notification-read-all',
    ),
]
