"""
Unit tests for notifications application views.

Tests the notification list, mark-as-read, and mark-all-as-read views
including authentication requirements.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notifications.models import Notification

User = get_user_model()


class NotificationListViewTest(TestCase):
    """Tests for the notification list view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='notif_list_user',
            email='notiflist@test.com',
            password='testpass123',
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type='enrollment',
            title='Test Notification',
            message='This is a test notification.',
            link='/courses/1/',
        )
        self.client.login(username='notif_list_user', password='testpass123')

    def test_notification_list_loads(self):
        """Notification list should load and show notifications."""
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Notification')

    def test_notification_list_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, 302)


class MarkNotificationReadViewTest(TestCase):
    """Tests for marking notifications as read."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mark_read_user',
            email='markread@test.com',
            password='testpass123',
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type='new_material',
            title='Unread Notification',
            message='This should be marked as read.',
            link='/courses/1/',
        )
        self.client.login(username='mark_read_user', password='testpass123')

    def test_mark_single_read(self):
        """Clicking a notification should mark it as read and redirect."""
        url = reverse('notification-read', kwargs={'pk': self.notification.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        """Mark-all-read should update all unread notifications."""
        # Create additional unread notifications
        Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='Second Unread',
            message='Also unread.',
        )
        url = reverse('notification-read-all')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        unread_count = Notification.objects.filter(
            recipient=self.user,
            is_read=False,
        ).count()
        self.assertEqual(unread_count, 0)


class NotificationAPITest(TestCase):
    """Tests for the notification API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='notif_api_user',
            email='notifapi@test.com',
            password='testpass123',
        )
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)

        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type='enrollment',
            title='API Test Notification',
            message='Testing the notification API.',
        )

    def test_list_notifications_api(self):
        """Authenticated user can list their notifications via API."""
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, 200)

    def test_unread_count_api(self):
        """Unread count endpoint should return correct count."""
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        response = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 1)
