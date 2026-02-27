"""
Unit tests for accounts application models.

Tests the User, Profile, and StatusUpdate models including
role-based properties, automatic profile creation via signals,
and model validation.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Profile, StatusUpdate

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def setUp(self):
        """Create test users for each role."""
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@test.com',
            password='testpass123',
            role='teacher',
            first_name='Test',
            last_name='Teacher',
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            role='student',
            first_name='Test',
            last_name='Student',
        )

    def test_teacher_role_property(self):
        """is_teacher should return True for teacher role."""
        self.assertTrue(self.teacher.is_teacher)
        self.assertFalse(self.teacher.is_student)

    def test_student_role_property(self):
        """is_student should return True for student role."""
        self.assertTrue(self.student.is_student)
        self.assertFalse(self.student.is_teacher)

    def test_default_role_is_student(self):
        """New users should default to the student role."""
        user = User.objects.create_user(
            username='default_user',
            email='default@test.com',
            password='testpass123',
        )
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_unique_email(self):
        """Email addresses must be unique across users."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='duplicate_email',
                email='teacher1@test.com',
                password='testpass123',
            )

    def test_str_representation(self):
        """String representation should include full name and role."""
        expected = 'Test Teacher (teacher)'
        self.assertEqual(str(self.teacher), expected)

    def test_user_ordering(self):
        """Users should be ordered by username."""
        users = list(User.objects.values_list('username', flat=True))
        self.assertEqual(users, sorted(users))


class ProfileModelTest(TestCase):
    """Tests for the Profile model and auto-creation signal."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='profile_test',
            email='profile@test.com',
            password='testpass123',
        )

    def test_profile_auto_created(self):
        """A Profile should be automatically created when a User is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_str_representation(self):
        """Profile string should include the username."""
        self.assertEqual(str(self.user.profile), 'Profile of profile_test')

    def test_profile_fields_editable(self):
        """Profile fields should be editable after creation."""
        profile = self.user.profile
        profile.bio = 'Test bio text'
        profile.phone = '555-0100'
        profile.department = 'CS'
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.bio, 'Test bio text')
        self.assertEqual(profile.phone, '555-0100')


class StatusUpdateModelTest(TestCase):
    """Tests for the StatusUpdate model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='status_user',
            email='status@test.com',
            password='testpass123',
        )

    def test_create_status_update(self):
        """A status update should be created with content and timestamp."""
        status = StatusUpdate.objects.create(
            user=self.user,
            content='Hello, this is my first status update!',
        )
        self.assertEqual(status.user, self.user)
        self.assertEqual(status.content, 'Hello, this is my first status update!')
        self.assertIsNotNone(status.created_at)

    def test_status_ordering(self):
        """Status updates should be ordered newest first."""
        s1 = StatusUpdate.objects.create(user=self.user, content='First')
        s2 = StatusUpdate.objects.create(user=self.user, content='Second')
        statuses = list(StatusUpdate.objects.all())
        self.assertEqual(statuses[0], s2)
        self.assertEqual(statuses[1], s1)

    def test_str_representation(self):
        """String representation should include username and truncated content."""
        status = StatusUpdate.objects.create(
            user=self.user,
            content='A' * 100,
        )
        self.assertIn('status_user', str(status))
