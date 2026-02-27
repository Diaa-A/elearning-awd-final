"""
Unit tests for accounts application views.

Tests registration, login, profile viewing and editing, user search,
and status update creation/deletion.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationViewTest(TestCase):
    """Tests for the user registration view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')

    def test_registration_page_loads(self):
        """GET request should return the registration form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_successful_registration(self):
        """Valid POST should create a user and redirect to home."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch(self):
        """Mismatched passwords should return a form error."""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'role': 'student',
            'password1': 'complexpass123',
            'password2': 'differentpass123',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class LoginViewTest(TestCase):
    """Tests for the login view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logintest',
            email='login@test.com',
            password='testpass123',
        )
        self.url = reverse('login')

    def test_login_page_loads(self):
        """GET request should return the login form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        """Valid credentials should redirect to home."""
        response = self.client.post(self.url, {
            'username': 'logintest',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        """Invalid credentials should not redirect."""
        response = self.client.post(self.url, {
            'username': 'logintest',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)


class ProfileViewTest(TestCase):
    """Tests for profile detail and edit views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@test.com',
            password='testpass123',
            first_name='Profile',
            last_name='User',
        )
        self.client.login(username='profileuser', password='testpass123')

    def test_profile_detail_loads(self):
        """Profile detail page should load for authenticated users."""
        url = reverse('profile-detail', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Template renders full name via get_full_name
        self.assertContains(response, 'Profile User')

    def test_profile_edit_loads(self):
        """Profile edit page should load for the profile owner."""
        url = reverse('profile-edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_profile_edit_submit(self):
        """Valid profile edit should update the profile and redirect."""
        url = reverse('profile-edit')
        response = self.client.post(url, {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'profile@test.com',
            'bio': 'Updated bio text',
            'phone': '555-0199',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_profile_requires_login(self):
        """Unauthenticated users should be redirected to login."""
        self.client.logout()
        url = reverse('profile-edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class UserSearchViewTest(TestCase):
    """Tests for the user search functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='searcher',
            email='searcher@test.com',
            password='testpass123',
        )
        self.teacher = User.objects.create_user(
            username='searchable_teacher',
            email='searchteacher@test.com',
            password='testpass123',
            role='teacher',
            first_name='Searchable',
            last_name='Teacher',
        )
        self.client.login(username='searcher', password='testpass123')

    def test_search_page_loads(self):
        """Search page should load without query."""
        url = reverse('user-search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_search_by_username(self):
        """Search should find users by username."""
        url = reverse('user-search') + '?q=searchable'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Template renders full name via get_full_name, so check for that
        self.assertContains(response, 'Searchable Teacher')

    def test_search_filter_by_role(self):
        """Search should support role filtering."""
        url = reverse('user-search') + '?q=searchable&role=teacher'
        response = self.client.get(url)
        # Template renders full name via get_full_name
        self.assertContains(response, 'Searchable Teacher')


class StatusUpdateViewTest(TestCase):
    """Tests for status update creation and deletion."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='statususer',
            email='statusview@test.com',
            password='testpass123',
        )
        self.client.login(username='statususer', password='testpass123')

    def test_create_status(self):
        """POST should create a new status update."""
        url = reverse('status-create')
        response = self.client.post(url, {'content': 'My new status!'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.user.status_updates.filter(content='My new status!').exists()
        )

    def test_delete_own_status(self):
        """Owner should be able to delete their status update."""
        from accounts.models import StatusUpdate
        status = StatusUpdate.objects.create(
            user=self.user,
            content='To be deleted',
        )
        url = reverse('status-delete', kwargs={'pk': status.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StatusUpdate.objects.filter(pk=status.pk).exists())
