"""
Models for the chat application.

Defines the ChatRoom and Message models for real-time communication.
Supports both direct (1-on-1) messages and course group chats.
Requirement R1(g): Users should be able to chat in real time.
"""

from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    """
    Represents a chat room for real-time messaging.

    Can be either a direct message room (between two users) or a
    course group chat room (linked to a specific course). Course
    group chat rooms are automatically created when a course is created.
    """

    class RoomType(models.TextChoices):
        DIRECT = 'direct', 'Direct Message'
        COURSE = 'course', 'Course Group Chat'

    name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Display name for the chat room.',
    )
    room_type = models.CharField(
        max_length=10,
        choices=RoomType.choices,
    )
    course = models.OneToOneField(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_room',
        help_text='The course this group chat belongs to (null for DMs).',
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chat_rooms',
        help_text='Users who are members of this chat room.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'

    def __str__(self):
        if self.room_type == self.RoomType.COURSE and self.course:
            return f'Course Chat: {self.course.code}'
        return f'DM: {self.name}'


class Message(models.Model):
    """
    A single chat message within a chat room.

    Stores the message content, sender, and timestamp. Messages are
    ordered chronologically and track read status for notification purposes.
    """

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    content = models.TextField(
        max_length=5000,
        help_text='Message text content.',
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f'{self.sender.username} @ {self.timestamp:%H:%M}: {self.content[:40]}'
