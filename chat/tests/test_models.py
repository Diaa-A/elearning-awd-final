"""
Unit tests for chat application models.

Tests the ChatRoom and Message models including room creation,
participant management, and message ordering.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from chat.models import ChatRoom, Message

User = get_user_model()


class ChatRoomModelTest(TestCase):
    """Tests for the ChatRoom model."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='chat_user1',
            email='chatuser1@test.com',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='chat_user2',
            email='chatuser2@test.com',
            password='testpass123',
        )

    def test_create_dm_room(self):
        """A direct message room should be created with two participants."""
        room = ChatRoom.objects.create(
            name='user1-user2',
            room_type=ChatRoom.RoomType.DIRECT,
        )
        room.participants.add(self.user1, self.user2)
        self.assertEqual(room.participants.count(), 2)
        self.assertEqual(room.room_type, ChatRoom.RoomType.DIRECT)

    def test_dm_room_str_representation(self):
        """DM room string should show the room name."""
        room = ChatRoom.objects.create(
            name='user1-user2',
            room_type=ChatRoom.RoomType.DIRECT,
        )
        self.assertIn('DM', str(room))

    def test_course_room_str_representation(self):
        """Course room string should reference the course code."""
        from courses.models import Course
        teacher = User.objects.create_user(
            username='chat_teacher',
            email='chatteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        course = Course.objects.create(
            teacher=teacher,
            title='Chat Course',
            code='CHAT101',
            description='Test course for chat.',
        )
        room = ChatRoom.objects.create(
            name='CHAT101 Group',
            room_type=ChatRoom.RoomType.COURSE,
            course=course,
        )
        self.assertIn('CHAT101', str(room))


class MessageModelTest(TestCase):
    """Tests for the Message model."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='msg_user1',
            email='msguser1@test.com',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='msg_user2',
            email='msguser2@test.com',
            password='testpass123',
        )
        self.room = ChatRoom.objects.create(
            name='msg-test-room',
            room_type=ChatRoom.RoomType.DIRECT,
        )
        self.room.participants.add(self.user1, self.user2)

    def test_create_message(self):
        """A message should be created with content and sender."""
        msg = Message.objects.create(
            room=self.room,
            sender=self.user1,
            content='Hello there!',
        )
        self.assertEqual(msg.content, 'Hello there!')
        self.assertEqual(msg.sender, self.user1)
        self.assertFalse(msg.is_read)

    def test_message_ordering(self):
        """Messages should be ordered by timestamp (oldest first)."""
        msg1 = Message.objects.create(
            room=self.room, sender=self.user1, content='First',
        )
        msg2 = Message.objects.create(
            room=self.room, sender=self.user2, content='Second',
        )
        messages = list(Message.objects.filter(room=self.room))
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)

    def test_message_str_representation(self):
        """String should include sender username and truncated content."""
        msg = Message.objects.create(
            room=self.room,
            sender=self.user1,
            content='A test message for string representation',
        )
        self.assertIn('msg_user1', str(msg))
