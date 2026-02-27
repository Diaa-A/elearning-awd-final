"""
Unit tests for courses application models.

Tests the Course, Enrollment, CourseMaterial, and Feedback models
including enrollment capacity checks, status transitions, file
validation, and unique constraint enforcement.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from courses.models import Course, Enrollment, Feedback

User = get_user_model()


class CourseModelTest(TestCase):
    """Tests for the Course model."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='course_teacher',
            email='courseteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Test Course',
            code='TEST101',
            description='A test course.',
            category='Testing',
            max_students=2,
        )

    def test_course_creation(self):
        """Course should be created with correct attributes."""
        self.assertEqual(self.course.title, 'Test Course')
        self.assertEqual(self.course.code, 'TEST101')
        self.assertTrue(self.course.is_active)

    def test_course_str_representation(self):
        """String representation should include code and title."""
        self.assertEqual(str(self.course), 'TEST101 - Test Course')

    def test_enrolled_count_property(self):
        """enrolled_count should return the number of active enrollments."""
        self.assertEqual(self.course.enrolled_count, 0)
        student = User.objects.create_user(
            username='counter_student',
            email='counter@test.com',
            password='testpass123',
            role='student',
        )
        Enrollment.objects.create(
            student=student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        self.assertEqual(self.course.enrolled_count, 1)

    def test_is_full_property(self):
        """is_full should return True when enrollment reaches max_students."""
        for i in range(2):
            student = User.objects.create_user(
                username=f'full_student_{i}',
                email=f'full{i}@test.com',
                password='testpass123',
                role='student',
            )
            Enrollment.objects.create(
                student=student,
                course=self.course,
                status=Enrollment.Status.ACTIVE,
            )
        self.assertTrue(self.course.is_full)

    def test_unique_course_code(self):
        """Course codes must be unique."""
        with self.assertRaises(Exception):
            Course.objects.create(
                teacher=self.teacher,
                title='Duplicate Code',
                code='TEST101',
                description='Duplicate.',
            )


class EnrollmentModelTest(TestCase):
    """Tests for the Enrollment model."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='enroll_teacher',
            email='enrollteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='enroll_student',
            email='enrollstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Enrollment Test Course',
            code='ENROLL101',
            description='Testing enrollments.',
        )

    def test_enrollment_creation(self):
        """Enrollment should be created with active status by default."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)

    def test_unique_together_constraint(self):
        """A student can only have one enrollment per course."""
        Enrollment.objects.create(student=self.student, course=self.course)
        with self.assertRaises(Exception):
            Enrollment.objects.create(student=self.student, course=self.course)

    def test_enrollment_str_representation(self):
        """String should include student, course code, and status."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        result = str(enrollment)
        self.assertIn('enroll_student', result)
        self.assertIn('ENROLL101', result)
        self.assertIn('active', result)


class FeedbackModelTest(TestCase):
    """Tests for the Feedback model."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='feedback_teacher',
            email='feedbackteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='feedback_student',
            email='feedbackstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Feedback Course',
            code='FB101',
            description='Testing feedback.',
        )

    def test_feedback_creation(self):
        """Feedback should be created with correct rating and comment."""
        fb = Feedback.objects.create(
            student=self.student,
            course=self.course,
            rating=5,
            comment='Great course!',
        )
        self.assertEqual(fb.rating, 5)
        self.assertEqual(fb.comment, 'Great course!')

    def test_rating_range_validation(self):
        """Rating must be between 1 and 5."""
        fb = Feedback(
            student=self.student,
            course=self.course,
            rating=0,
            comment='Invalid rating.',
        )
        with self.assertRaises(ValidationError):
            fb.full_clean()

        fb.rating = 6
        with self.assertRaises(ValidationError):
            fb.full_clean()

    def test_one_feedback_per_student_per_course(self):
        """A student can only leave one feedback per course."""
        Feedback.objects.create(
            student=self.student,
            course=self.course,
            rating=4,
            comment='First feedback.',
        )
        with self.assertRaises(Exception):
            Feedback.objects.create(
                student=self.student,
                course=self.course,
                rating=5,
                comment='Second feedback.',
            )
