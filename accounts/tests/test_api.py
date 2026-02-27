"""
Unit tests for accounts application REST API endpoints.

Tests the user list, registration, profile, and status update
API ViewSets including authentication and permission checks.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class UserAPITest(APITestCase):
    """Tests for the User API endpoints."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='api_teacher',
            email='apiteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='api_student',
            email='apistudent@test.com',
            password='testpass123',
            role='student',
        )
        self.token = Token.objects.create(user=self.teacher)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_user_list(self):
        """Authenticated user can list all users."""
        response = self.client.get('/api/v1/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_list_filter_by_role(self):
        """User list can be filtered by role query parameter."""
        response = self.client.get('/api/v1/accounts/users/?role=teacher')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All results should be teachers
        for user in response.data['results']:
            self.assertEqual(user['role'], 'teacher')

    def test_user_detail(self):
        """Authenticated user can view user details."""
        response = self.client.get(f'/api/v1/accounts/users/{self.student.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'api_student')

    def test_current_user_endpoint(self):
        """The /me/ endpoint should return the authenticated user."""
        response = self.client.get('/api/v1/accounts/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'api_teacher')

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests should be denied."""
        self.client.credentials()
        response = self.client.get('/api/v1/accounts/users/')
        # SessionAuthentication returns 403 when no session exists
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


class RegistrationAPITest(APITestCase):
    """Tests for the registration API endpoint."""

    def test_successful_registration(self):
        """Valid data should create a user and return a token."""
        data = {
            'username': 'newapi_user',
            'email': 'newapi@test.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'role': 'student',
        }
        response = self.client.post('/api/v1/accounts/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_registration_password_mismatch(self):
        """Mismatched passwords should return a validation error."""
        data = {
            'username': 'newapi_user',
            'email': 'newapi@test.com',
            'password': 'securepass123',
            'password_confirm': 'differentpass',
            'role': 'student',
        }
        response = self.client.post('/api/v1/accounts/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Duplicate email should return a validation error."""
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='testpass123',
        )
        data = {
            'username': 'newapi_user',
            'email': 'existing@test.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'role': 'student',
        }
        response = self.client.post('/api/v1/accounts/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StatusUpdateAPITest(APITestCase):
    """Tests for the status update API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='status_api_user',
            email='statusapi@test.com',
            password='testpass123',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_status_update(self):
        """Authenticated user can create a status update via API."""
        response = self.client.post(
            '/api/v1/accounts/status-updates/',
            {'content': 'API status update!'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'API status update!')

    def test_list_status_updates(self):
        """Authenticated user can list status updates."""
        response = self.client.get('/api/v1/accounts/status-updates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
