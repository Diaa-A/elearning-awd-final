"""
Unit tests for courses application REST API endpoints.

Tests the Course, Enrollment, Material, and Feedback API ViewSets
including role-based access control and CRUD operations.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from courses.models import Course, Enrollment

User = get_user_model()


class CourseAPITest(APITestCase):
    """Tests for the Course API endpoints."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='api_course_teacher',
            email='apicourseteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='api_course_student',
            email='apicoursestudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='API Course',
            code='API101',
            description='A course for API testing.',
            category='Testing',
        )
        self.teacher_token = Token.objects.create(user=self.teacher)
        self.student_token = Token.objects.create(user=self.student)

    def test_list_courses_authenticated(self):
        """Authenticated users can list courses."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.student_token.key}'
        )
        response = self.client.get('/api/v1/courses/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_courses_unauthenticated(self):
        """Unauthenticated requests should be denied."""
        response = self.client.get('/api/v1/courses/courses/')
        # SessionAuthentication returns 403 when no session exists
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_teacher_can_create_course(self):
        """Teachers can create courses via API."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.teacher_token.key}'
        )
        data = {
            'title': 'New API Course',
            'code': 'API201',
            'description': 'Created via API.',
            'category': 'Testing',
            'max_students': 25,
        }
        response = self.client.post('/api/v1/courses/courses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(code='API201').exists())

    def test_student_cannot_create_course(self):
        """Students should not be able to create courses."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.student_token.key}'
        )
        data = {
            'title': 'Student Course',
            'code': 'STU101',
            'description': 'Should fail.',
        }
        response = self.client.post('/api/v1/courses/courses/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_detail(self):
        """Authenticated users can view course details."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.student_token.key}'
        )
        response = self.client.get(
            f'/api/v1/courses/courses/{self.course.pk}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'API101')

    def test_teacher_can_update_own_course(self):
        """Course teacher can update their course."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.teacher_token.key}'
        )
        response = self.client.patch(
            f'/api/v1/courses/courses/{self.course.pk}/',
            {'title': 'Updated Title'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Updated Title')

    def test_search_courses(self):
        """Course search should filter by title and code."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.student_token.key}'
        )
        response = self.client.get('/api/v1/courses/courses/?search=API')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class EnrollmentAPITest(APITestCase):
    """Tests for enrollment API endpoints."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='enroll_api_teacher',
            email='enrollapiteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='enroll_api_student',
            email='enrollapistudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Enrollment API Course',
            code='EAPI101',
            description='Testing enrollment API.',
            max_students=30,
        )
        self.student_token = Token.objects.create(user=self.student)
        self.teacher_token = Token.objects.create(user=self.teacher)

    def test_student_can_enroll(self):
        """Students can enroll in a course via API."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.student_token.key}'
        )
        response = self.client.post(
            f'/api/v1/courses/courses/{self.course.pk}/enroll/'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                course=self.course,
            ).exists()
        )

    def test_student_can_unenroll(self):
        """Students can unenroll from a course via API."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.student_token.key}'
        )
        response = self.client.post(
            f'/api/v1/courses/courses/{self.course.pk}/unenroll/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_teacher_can_view_students(self):
        """Course teacher can list enrolled students."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.teacher_token.key}'
        )
        response = self.client.get(
            f'/api/v1/courses/courses/{self.course.pk}/students/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_can_block_student(self):
        """Course teacher can block a student via API."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.teacher_token.key}'
        )
        response = self.client.post(
            f'/api/v1/courses/courses/{self.course.pk}/'
            f'students/{self.student.pk}/block/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollment = Enrollment.objects.get(
            student=self.student,
            course=self.course,
        )
        self.assertEqual(enrollment.status, Enrollment.Status.BLOCKED)
