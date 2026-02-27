"""
Unit tests for chat application views.

Tests the chat room list, direct message, and course group chat views
including access control and room creation logic.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from chat.models import ChatRoom
from courses.models import Course, Enrollment

User = get_user_model()


class ChatRoomListViewTest(TestCase):
    """Tests for the chat room list view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='chat_list_user',
            email='chatlist@test.com',
            password='testpass123',
            role='student',
        )
        self.client.login(username='chat_list_user', password='testpass123')

    def test_room_list_loads(self):
        """Chat room list should load for authenticated users."""
        response = self.client.get(reverse('chat-room-list'))
        self.assertEqual(response.status_code, 200)

    def test_room_list_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.get(reverse('chat-room-list'))
        self.assertEqual(response.status_code, 302)


class DirectMessageViewTest(TestCase):
    """Tests for the direct message view."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='dm_user1',
            email='dmuser1@test.com',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='dm_user2',
            email='dmuser2@test.com',
            password='testpass123',
        )
        self.client.login(username='dm_user1', password='testpass123')

    def test_dm_creates_room(self):
        """Visiting a DM URL should create a new chat room if none exists."""
        url = reverse('chat-dm', kwargs={'user_id': self.user2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ChatRoom.objects.filter(
                room_type=ChatRoom.RoomType.DIRECT,
                participants=self.user1,
            ).filter(
                participants=self.user2,
            ).exists()
        )

    def test_dm_reuses_existing_room(self):
        """Revisiting a DM should reuse the existing room."""
        url = reverse('chat-dm', kwargs={'user_id': self.user2.pk})
        self.client.get(url)
        room_count_before = ChatRoom.objects.filter(
            room_type=ChatRoom.RoomType.DIRECT,
        ).count()
        self.client.get(url)
        room_count_after = ChatRoom.objects.filter(
            room_type=ChatRoom.RoomType.DIRECT,
        ).count()
        self.assertEqual(room_count_before, room_count_after)


class CourseGroupChatViewTest(TestCase):
    """Tests for the course group chat view."""

    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='group_teacher',
            email='groupteacher@test.com',
            password='testpass123',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='group_student',
            email='groupstudent@test.com',
            password='testpass123',
            role='student',
        )
        self.course = Course.objects.create(
            teacher=self.teacher,
            title='Chat Group Course',
            code='CGC101',
            description='Course for group chat testing.',
        )
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )

    def test_teacher_can_access_group_chat(self):
        """Course teacher should be able to access the group chat."""
        self.client.login(username='group_teacher', password='testpass123')
        url = reverse('chat-course', kwargs={'course_id': self.course.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_enrolled_student_can_access_group_chat(self):
        """Enrolled student should be able to access the group chat."""
        self.client.login(username='group_student', password='testpass123')
        url = reverse('chat-course', kwargs={'course_id': self.course.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_unenrolled_student_denied(self):
        """Unenrolled student should be redirected with an error."""
        other = User.objects.create_user(
            username='other_student',
            email='other@test.com',
            password='testpass123',
            role='student',
        )
        self.client.login(username='other_student', password='testpass123')
        url = reverse('chat-course', kwargs={'course_id': self.course.pk})
        response = self.client.get(url)
        # Should redirect (302) to course list with error message
        self.assertEqual(response.status_code, 302)
