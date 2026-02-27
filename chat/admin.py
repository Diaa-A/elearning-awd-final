"""
Django admin configuration for the chat application.

Registers ChatRoom and Message models for administrative management.
"""

from django.contrib import admin

from .models import ChatRoom, Message


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """Admin for the ChatRoom model."""
    list_display = ['name', 'room_type', 'course', 'created_at']
    list_filter = ['room_type', 'created_at']
    search_fields = ['name', 'course__title', 'course__code']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin for the Message model."""
    list_display = ['sender', 'room', 'content_preview', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['sender__username', 'content']
    ordering = ['-timestamp']

    def content_preview(self, obj):
        """Return truncated message content for the list display."""
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    content_preview.short_description = 'Content'
