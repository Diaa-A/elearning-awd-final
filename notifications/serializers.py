"""
DRF serializers for the notifications application.

Provides serialization for the Notification model, including
display-friendly type labels and read status management.
"""

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notification records.

    Includes the human-readable notification type display value
    and a time_since field for relative timestamps.
    """

    type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True,
    )

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'type_display',
            'title',
            'message',
            'is_read',
            'link',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'link',
            'created_at',
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.

    Accepts an optional list of notification IDs. If no IDs are
    provided, all unread notifications for the user are marked as read.
    """

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='List of notification IDs to mark as read. '
                  'If empty, all unread notifications are marked.',
    )
