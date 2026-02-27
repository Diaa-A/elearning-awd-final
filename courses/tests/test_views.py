"""
Unit tests for courses application views.

Tests course listing, detail, creation, enrollment/unenrollment,
student management, material upload, and feedback submission.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from courses.models import Course, Enrollment, Feedback

User = get_user_model()


class CourseListViewTest(TestCase):
    """Tests for the course listing view."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='list_teacher',
            email='listteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='list_student',
            email='liststudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Visible Course',
            code='VIS101',
            description='A visible course.',
        )
        self.client.login(username='list_student', password='testpass123')

    def test_course_list_loads(self):
        """Course list should load for authenticated users."""
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VIS101')

    def test_course_list_search(self):
        """Search should filter courses by title."""
        response = self.client.get(reverse('course-list') + '?q=Visible')
        self.assertContains(response, 'Visible Course')

    def test_course_list_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, 302)


class CourseDetailViewTest(TestCase):
    """Tests for the course detail view."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='detail_teacher',
            email='detailteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Detail Course',
            code='DET101',
            description='A course for detail testing.',
        )
        self.client.login(username='detail_teacher', password='testpass123')

    def test_course_detail_loads(self):
        """Course detail page should display course info."""
        url = reverse('course-detail', kwargs={'pk': self.course.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DET101')


class CourseCreateViewTest(TestCase):
    """Tests for course creation."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='create_teacher',
            email='createteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='create_student',
            email='createstudent@test.com',
            password='testpass123',
            role='student',
        )

    def test_teacher_can_create_course(self):
        """Teachers should be able to create courses."""
        self.client.login(username='create_teacher', password='testpass123')
        url = reverse('course-create')
        response = self.client.post(url, {
            'title': 'New Course',
            'code': 'NEW101',
            'description': 'A brand new course.',
            'category': 'Testing',
            'max_students': 30,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(code='NEW101').exists())

    def test_student_cannot_create_course(self):
        """Students should not be able to access the create course page."""
        self.client.login(username='create_student', password='testpass123')
        url = reverse('course-create')
        response = self.client.get(url)
        # View returns HttpResponseForbidden (403) for non-teachers
        self.assertEqual(response.status_code, 403)


class EnrollmentViewTest(TestCase):
    """Tests for enrollment and unenrollment views."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='enroll_v_teacher',
            email='enrollvteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='enroll_v_student',
            email='enrollvstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Enrollment Course',
            code='ENR101',
            description='Course for enrollment testing.',
            max_students=30,
        )
        self.client.login(username='enroll_v_student', password='testpass123')

    def test_student_can_enroll(self):
        """Students should be able to enroll in a course."""
        url = reverse('course-enroll', kwargs={'pk': self.course.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                course=self.course,
                status='active',
            ).exists()
        )

    def test_student_can_unenroll(self):
        """Students should be able to unenroll from a course."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        url = reverse('course-unenroll', kwargs={'pk': self.course.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        enrollment = Enrollment.objects.get(
            student=self.student,
            course=self.course,
        )
        self.assertEqual(enrollment.status, Enrollment.Status.DROPPED)


class StudentManagementViewTest(TestCase):
    """Tests for teacher student management (block/remove)."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='mgmt_teacher',
            email='mgmtteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='mgmt_student',
            email='mgmtstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Management Course',
            code='MGT101',
            description='Course for management testing.',
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.login(username='mgmt_teacher', password='testpass123')

    def test_teacher_can_block_student(self):
        """Teacher should be able to block a student."""
        url = reverse('block-student', kwargs={
            'pk': self.course.pk,
            'student_id': self.student.pk,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.BLOCKED)

    def test_teacher_can_remove_student(self):
        """Teacher should be able to remove a student."""
        url = reverse('remove-student', kwargs={
            'pk': self.course.pk,
            'student_id': self.student.pk,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.DROPPED)


class FeedbackViewTest(TestCase):
    """Tests for feedback submission."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='fb_teacher',
            email='fbteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='fb_student',
            email='fbstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Feedback Course',
            code='FBV101',
            description='Course for feedback testing.',
        )
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.login(username='fb_student', password='testpass123')

    def test_student_can_submit_feedback(self):
        """Enrolled student should be able to submit feedback."""
        url = reverse('feedback-create', kwargs={'pk': self.course.pk})
        response = self.client.post(url, {
            'rating': 5,
            'comment': 'Excellent course!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Feedback.objects.filter(
                student=self.student,
                course=self.course,
            ).exists()
        )
