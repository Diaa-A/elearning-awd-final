"""
Views for the chat application.

Handles chat room listing, direct message initiation, and course
group chat access. The actual messaging happens via WebSockets
defined in consumers.py.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import User
from courses.models import Course, Enrollment

from .models import ChatRoom


class ChatRoomListView(LoginRequiredMixin, View):
    """
    Display a list of chat rooms the user participates in.

    Shows both direct message rooms and course group chat rooms.
    """

    def get(self, request):
        """List all chat rooms for the authenticated user."""
        # Get DM rooms the user participates in
        dm_rooms = ChatRoom.objects.filter(
            room_type=ChatRoom.RoomType.DIRECT,
            participants=request.user,
        ).prefetch_related('participants')

        # Get course group chat rooms the user has access to
        if request.user.is_teacher:
            # Teacher sees chat rooms for courses they teach
            course_rooms = ChatRoom.objects.filter(
                room_type=ChatRoom.RoomType.COURSE,
                course__teacher=request.user,
            ).select_related('course')
        else:
            # Student sees chat rooms for courses they are enrolled in
            enrolled_course_ids = Enrollment.objects.filter(
                student=request.user,
                status=Enrollment.Status.ACTIVE,
            ).values_list('course_id', flat=True)
            course_rooms = ChatRoom.objects.filter(
                room_type=ChatRoom.RoomType.COURSE,
                course_id__in=enrolled_course_ids,
            ).select_related('course')

        context = {
            'dm_rooms': dm_rooms,
            'course_rooms': course_rooms,
        }
        return render(request, 'chat/room_list.html', context)


class DirectMessageView(LoginRequiredMixin, View):
    """
    Open or create a direct message conversation with another user.

    Creates a DM chat room if one does not already exist between
    the two users, then renders the chat interface.
    """

    def get(self, request, user_id):
        """Open the DM chat room with the specified user."""
        other_user = get_object_or_404(User, pk=user_id)

        if other_user == request.user:
            return redirect('chat-room-list')

        # Find an existing DM room between these two users
        room = ChatRoom.objects.filter(
            room_type=ChatRoom.RoomType.DIRECT,
            participants=request.user,
        ).filter(
            participants=other_user,
        ).first()

        # Create a new DM room if none exists
        if not room:
            room = ChatRoom.objects.create(
                name=f'{request.user.username} & {other_user.username}',
                room_type=ChatRoom.RoomType.DIRECT,
            )
            room.participants.add(request.user, other_user)

        # Load message history
        messages_list = room.messages.order_by('timestamp')[:100]

        context = {
            'room': room,
            'other_user': other_user,
            'messages': messages_list,
        }
        return render(request, 'chat/chat_room.html', context)


class CourseGroupChatView(LoginRequiredMixin, View):
    """
    Open the group chat room for a course.

    Creates the course chat room if it does not already exist.
    Only the course teacher and enrolled students can access this chat.
    """

    def get(self, request, course_id):
        """Open the course group chat room."""
        course = get_object_or_404(Course, pk=course_id)

        # Verify the user has access to this course chat
        has_access = (
            course.teacher == request.user
            or Enrollment.objects.filter(
                student=request.user,
                course=course,
                status=Enrollment.Status.ACTIVE,
            ).exists()
        )
        if not has_access:
            return redirect('course-list')

        # Get or create the chat room for this course
        room, created = ChatRoom.objects.get_or_create(
            course=course,
            room_type=ChatRoom.RoomType.COURSE,
            defaults={'name': f'{course.code} - Group Chat'},
        )

        # Ensure the current user is a participant
        if not room.participants.filter(pk=request.user.pk).exists():
            room.participants.add(request.user)

        # Load message history
        messages_list = room.messages.order_by('timestamp')[:100]

        context = {
            'room': room,
            'course': course,
            'messages': messages_list,
        }
        return render(request, 'chat/chat_room.html', context)
