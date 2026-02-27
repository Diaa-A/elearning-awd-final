"""
DRF serializers for the chat application.

Provides serialization for ChatRoom and Message models, including
nested participant l ists and sender information for API consumers.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ChatRoom, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer) :
    """
    Serializer for chat messages.

    Includes the sender's username for display purposes. The sender
    and room fields are set automatically from the request context.
    """

    sender_username = serializers.CharField(
        source='sender.username',
        read_only=True,
    )

    class Meta:
        model = Message
        fields = [
            'id',
            'room',
            'sender',
            'sender_username',
            'content',
            'timestamp',
            'is_read',
        ]
        read_only_fields = ['id', 'room', 'sender', 'timestamp']


class ChatRoomListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for chat room list endpoints.

    Shows room metadata and the number of participants without
    including the full participant list or message history.
    """

    participant_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    course_code = serializers.CharField(
        source='course.code',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'room_type',
            'course',
            'course_code',
            'participant_count',
            'last_message',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_participant_count(self, obj):
        """Return the number of participants in this room."""
        return obj.participants.count()

    def get_last_message(self, obj):
        """Return a summary of the most recent message, or None."""
        msg = obj.messages.order_by('-timestamp').first()
        if msg:
            return {
                'sender': msg.sender.username,
                'content': msg.content[:100],
                'timestamp': msg.timestamp.isoformat(),
            }
        return None


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for a single chat room.

    Includes the list of participant usernames and the recent
    message history (last 50 messages).
    """

    participants = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='username',
    )
    messages = serializers.SerializerMethodField()
    course_code = serializers.CharField(
        source='course.code',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'room_type',
            'course',
            'course_code',
            'participants',
            'messages',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_messages(self, obj):
        """Return the 50 most recent messages in chronological order."""
        recent = obj.messages.select_related('sender').order_by('-timestamp')[:50]
        # Reverse so oldest first
        return MessageSerializer(reversed(list(recent)), many=True).data


class SendMessageSerializer(serializers.Serializer):
    """
    Serializer for sending a message via the REST API.

    This is an alternative to the WebSocket interface for clients
    that cannot maintain persistent connections.
    """

    content = serializers.CharField(
        max_length=5000,
        help_text='Message text content (max 5000 characters ).',
    )
