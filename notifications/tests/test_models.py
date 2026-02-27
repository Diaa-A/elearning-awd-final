"""
Unit tests for notifications application models.

Tests the Notification model including creation, ordering,
read status, and type classification.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.models import Notification

User = get_user_model()


class NotificationModelTest(TestCase):
    """Tests for the Notification model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='notif_user',
            email='notifuser@test.com',
            password='testpass123',
        )

    def test_create_notification(self):
        """A notification should be created with correct attributes."""
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='enrollment',
            title='New Enrollment',
            message='A student has enrolled in your course.',
            link='/courses/1/',
        )
        self.assertEqual(notif.recipient, self.user)
        self.assertEqual(notif.notification_type, 'enrollment')
        self.assertFalse(notif.is_read)

    def test_notification_ordering(self):
        """Notifications should be ordered newest first."""
        n1 = Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='First',
            message='First notification.',
        )
        n2 = Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='Second',
            message='Second notification.',
        )
        notifications = list(Notification.objects.filter(recipient=self.user))
        self.assertEqual(notifications[0], n2)
        self.assertEqual(notifications[1], n1)

    def test_mark_as_read(self):
        """Notification can be marked as read."""
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='new_material',
            title='New Material',
            message='New material uploaded.',
        )
        self.assertFalse(notif.is_read)
        notif.is_read = True
        notif.save()
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_str_representation(self):
        """String should include type, recipient, and title."""
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='feedback',
            title='New Feedback',
            message='Someone left feedback.',
        )
        result = str(notif)
        self.assertIn('feedback', result)
        self.assertIn('notif_user', result)
        self.assertIn('New Feedback', result)
