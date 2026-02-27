"""
Django admin configuration for the notifications application.

Registers the Notification model with filtering and search support.
"""

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for the Notification model."""
    list_display = [
        'recipient', 'notification_type', 'title', 'is_read', 'created_at',
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
