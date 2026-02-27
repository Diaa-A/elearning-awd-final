"""
WebSocket consumers for the chat application.

Implements real-time messaging using Django Channels. Two consumer classes
handle the different chat room types:
- DirectChatConsumer: 1-on-1 direct messages between two users
- GroupChatConsumer: course group chats for all enrolled students and the teacher

Both consumers use Redis as the channel layer backend and persist messages
to the database for history retrieval.
"""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import ChatRoom, Message


class DirectChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for 1-on-1 direct message conversations.

    On connect, verifies the authenticated user is a participant of the
    requested chat room. Messages are saved to the database and broadcast
    to all participants in the room via the channel layer group.
    """

    async def connect(self):
        """Accept the WebSocket connection if the user is a room participant."""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'dm_{self.room_id}'
        self.user = self.scope['user']

        # Reject unauthenticated users
        if self.user.is_anonymous:
            await self.close()
            return

        # Verify the user is a participant of this chat room
        if not await self.is_participant():
            await self.close()
            return

        # Join the channel layer group for this room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Leave the channel layer group on disconnect."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive_json(self, content):
        """
        Handle incoming messages from the WebSocket client.

        Validates the message content, persists it to the database,
        and broadcasts it to all room participants.
        """
        message_text = content.get('message', '').strip()
        if not message_text:
            return

        # Save the message to the database
        message = await self.save_message(message_text)

        # Broadcast tpo all participants in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message_text,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'timestamp': message.timestamp.isoformat(),
            },
        )

    async def chat_message(self, event):
        """Send the broadcast message to the WebSocket client."""
        await self.send_json({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
        })

    @database_sync_to_async
    def is_participant(self):
        """Check if the current user is a participant of this chat room."""
        return ChatRoom.objects.filter(
            id=self.room_id,
            participants=self.user,
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        """Persist a new message to the database and return it."""
        return Message.objects.create(
            room_id=self.room_id,
            sender=self.user,
            content=content,
        )


class GroupChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for course group chat rooms.

    On connect, verifies the authenticated user is either the course
    teacher or an actively enrolled student. Messages are saved to the
    database and broadcast to all group members via the channel layer.
    """

    async def connect(self):
        """Accept the WebSocket connection if the user has access to this course chat."""
        self.course_id = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = f'course_chat_{self.course_id}'
        self.user = self.scope['user']

        # Reject unauthenticated users
        if self.user.is_anonymous:
            await self.close()
            return

        # Verify the user is the course teacher or an enrolled student
        if not await self.has_course_access():
            await self.close()
            return

        # Join the channel layer group for this course chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Leave the channel layer group on disconnect."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive_json(self, content):
        """
        Handle incoming messages from the WebSocket client.

        Validates the message content, persists it to the database,
        and broadcasts it to all course chat members.
        """
        message_text = content.get('message', '').strip()
        if not message_text:
            return

        # Save the message to the database
        message = await self.save_message(message_text)

        # Broadcast to all members in the course chat
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message_text,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'timestamp': message.timestamp.isoformat(),
            },
        )

    async def chat_message(self, event):
        """Send the broadcast message to the WebSocket client."""
        await self.send_json({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
        })

    @database_sync_to_async
    def has_course_access(self):
        """
        Check if the current user is the course teacher or an enrolled student.

        Returns True if the user is authorized to participate in this
        course's group chat, False otherwise.
        """
        from courses.models import Course, Enrollment

        try:
            course = Course.objects.get(id=self.course_id)
        except Course.DoesNotExist:
            return False

        # Course teacher always has acces s
        if course.teacher == self.user:
            return True

        #Check for active student enrollment
        return Enrollment.objects.filter(
            student=self.user,
            course=course,
            status=Enrollment.Status.ACTIVE,
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        """Persist a new message to the database and return it."""
        # Get o r create the chat room for this couirse
        room, _ = ChatRoom.objects.get_or_create(
            course_id=self.course_id,
            room_type=ChatRoom.RoomType.COURSE,
            defaults={'name': f'Course {self.course_id} Chat'},
        )
        return Message.objects.create(
            room=room,
            sender=self.user,
            content=content,
        )
