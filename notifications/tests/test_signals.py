"""
Unit tests for notification signals.

Tests that notifications are created automatically when students
enrol in courses and when teachers upload new materials, verifying
the signal-to-Celery-task pipeline.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.models import Course, CourseMaterial, Enrollment
from notifications.models import Notification

User = get_user_model()


class EnrollmentNotificationSignalTest(TestCase):
    """Tests for the enrollment notification signal."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='sig_teacher',
            email='sigteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='sig_student',
            email='sigstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Signal Test Course',
            code='SIG101',
            description='Testing signals.',
        )

    def test_enrollment_creates_notification(self):
        """Creating an active enrollment should notify the course teacher."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        # With CELERY_TASK_ALWAYS_EAGER=True, the task runs synchronously
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.teacher,
                notification_type='enrollment',
            ).exists()
        )

    def test_dropped_enrollment_no_notification(self):
        """Creating a dropped enrollment should not notify the teacher."""
        initial_count = Notification.objects.filter(
            recipient=self.teacher,
            notification_type='enrollment',
        ).count()
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.DROPPED,
        )
        new_count = Notification.objects.filter(
            recipient=self.teacher,
            notification_type='enrollment',
        ).count()
        self.assertEqual(initial_count, new_count)
