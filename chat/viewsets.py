"""
DRF ViewSets for the chat application.

Provides REST API endpoints for chat room listing, detail views,
and message sending. These endpoints complement the WebSocket
interface for clients that prefer HTTP-based communication.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ChatRoom, Message
from .serializers import (
    ChatRoomDetailSerializer,
    ChatRoomListSerializer,
    MessageSerializer,
    SendMessageSerializer,
)


class ChatRoomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving chat rooms.

    Only returns rooms where the requesting user is a participant.

    list:     GET /api/v1/chat/rooms/
    retrieve: GET /api/v1/chat/rooms/{id}/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only rooms the user participates in."""
        return ChatRoom.objects.filter(
            participants=self.request.user,
        ).select_related('course').prefetch_related('participants')

    def get_serializer_class(self):
        """Use list serializer for list, detail for retrieve."""
        if self.action == 'list':
            return ChatRoomListSerializer
        return ChatRoomDetailSerializer

    @action(
        detail=True,
        methods=['get'],
        url_path='messages',
    )
    def messages(self, request, pk=None):
        """
        List messages for a specific chat room (paginated).

        GET /api/v1/chat/rooms/{id}/messages/
        """
        room = self.get_object()
        messages = room.messages.select_related('sender').order_by('timestamp')
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='send',
    )
    def send_message(self, request, pk=None):
        """
        Send a message to a chat room via REST API.

        This is an alternative to the WebSocket interface for clients
        that cannot maintain persistent connections. The message is
        saved to the database but is NOT broadcast via WebSocket
        (other participants will see it on their next page load or
        WebSocket reconnect).

        POST /api/v1/chat/rooms/{id}/send/
        Body: {"content": "Hello!"}
        """
        room = self.get_object()

        # Verify user is a participant
        if not room.participants.filter(pk=request.user.pk).exists():
            return Response(
                {'detail': 'You are not a participant in this room.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=serializer.validated_data['content'],
        )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='mark-read',
    )
    def mark_read(self, request, pk=None):
        """
        Mark all messages in this room as read for the current user.

        POST /api/v1/chat/rooms/{id}/mark-read/
        """
        room = self.get_object()
        updated = room.messages.filter(
            is_read=False,
        ).exclude(
            sender=request.user,
        ).update(is_read=True)

        return Response({'marked_read': updated})


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving individual messages.

    Scoped to messages in rooms the user participates in.

    list:     GET /api/v1/chat/messages/
    retrieve: GET /api/v1/chat/messages/{id}/
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return messages only from rooms the user is in."""
        user_rooms = ChatRoom.objects.filter(
            participants=self.request.user,
        )
        return Message.objects.filter(
            room__in=user_rooms,
        ).select_related('sender', 'room')
