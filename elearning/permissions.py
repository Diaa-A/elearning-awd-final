"""
Custom DRF permission classes for the eLearning platform.

These permissions enforce role-based access control across the REST API,
ensuring that teachers and students can only perform actions appropriate
to their roles.
"""

from rest_framework.permissions import BasePermission

from courses.models import Enrollment


class IsTeacher(BasePermission):
    """
    Allow access only to users with the teacher role.

    Used to restrict endpoints like course creation and material upload
    to teachers only.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_teacher
        )


class IsStudent(BasePermission):
    """
    Allow access only to users with the student role.

    Used to restrict endpoints like enrollment and feedback submission
    to students only.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_student
        )


class IsCourseTeacher(BasePermission):
    """
    Allow access only to the teacher who owns a particular course.

    Checks that the authenticated user is the teacher field on the
    course object. Used for course editing, student management, and
    material upload endpoints.
    """

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Course instance
        return obj.teacher == request.user


class IsEnrolledOrTeacher(BasePermission):
    """
    Allow access to students actively enrolled in the course, or the
    course teacher.

    Used for viewing course details, materials, and chat rooms that
    should only be accessible to course participants.
    """

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Course instance
        if obj.teacher == request.user:
            return True
        return Enrollment.objects.filter(
            student=request.user,
            course=obj,
            status=Enrollment.Status.ACTIVE,
        ).exists()


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: allow write operations only to the object owner.

    Expects the object to have a 'user' attribute (e.g. Profile, StatusUpdate).
    Read operations (GET, HEAD, OPTIONS) are allowed for any authenticated user.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Write permissions require ownership
        owner = getattr(obj, 'user', None) or getattr(obj, 'sender', None)
        return owner == request.user


class IsMessageSender(BasePermission):
    """
    Allow modification only by the sender of a message.

    Used to restrict message deletion/editing to the original sender.
    """

    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user
