"""
Models for the notifications application.

Defines the Notification model for in-app notifications triggered by
events such as student enrollment and new course material uploads.
Requirements R1(k) and R1(l).
"""

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    In-app notification delivered to a user.

    Created by Django signals when specific events occur:
    - A student enrols on a course -> notify the teacher (R1(k))
    - A teacher uploads new material -> notify enrolled students (R1(l))

    Each notification has a type, title, message body, read status,
    and an optional link to redirect the user to the relevant page.
    """

    class NotificationType(models.TextChoices):
        ENROLLMENT = 'enrollment', 'New Enrollment'
        NEW_MATERIAL = 'new_material', 'New Course Material'
        FEEDBACK = 'feedback', 'New Feedback'
        GENERAL = 'general', 'General'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL path to redirect the user when the notification is clicked.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'[{self.notification_type}] -> {self.recipient.username}: {self.title}'
