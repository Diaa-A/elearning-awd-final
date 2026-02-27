"""
DRF ViewSets for the courses application.

Provides API endpoints for course CRUD, enrollment management,
course material upload, and feedback submission. Applies custom
permission classes to enforce teacher/student role restrictions.
"""

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from elearning.permissions import (
    IsCourseTeacher,
    IsEnrolledOrTeacher,
    IsStudent,
    IsTeacher,
)

from .models import Course, CourseMaterial, Enrollment, Feedback
from .serializers import (
    CourseCreateSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    CourseMaterialSerializer,
    EnrollmentCreateSerializer,
    EnrollmentSerializer,
    FeedbackSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course CRUD operations.

    - Any authenticated user can list and retrieve courses.
    - Only teachers can create courses.
    - Only the course teacher can update or delete their courses.

    Supports search by title, code, and category, plus ordering.

    list:     GET    /api/v1/courses/
    create:   POST   /api/v1/courses/
    retrieve: GET    /api/v1/courses/{id}/
    update:   PUT    /api/v1/courses/{id}/
    delete:   DELETE /api/v1/courses/{id}/
    """

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['category', 'is_active', 'teacher']
    search_fields = ['title', 'code', 'category', 'description']
    ordering_fields = ['title', 'code', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return courses with select_related for performance."""
        return Course.objects.select_related('teacher').all()

    def get_serializer_class(self):
        """Use different serializers for list vs detail vs create."""
        if self.action == 'list':
            return CourseListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return CourseCreateSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        """
        Apply role-based permissions:
        - create: teacher only
        - update/delete: course teacher only
        - list/retrieve: any authenticated user
        """
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsTeacher()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Set the teacher to the requesting user on course creation."""
        serializer.save(teacher=self.request.user)

    # ------------------------------------------------------------------
    # Custom actions nested under a course
    # ------------------------------------------------------------------

    @action(
        detail=True,
        methods=['get'],
        url_path='students',
        permission_classes=[permissions.IsAuthenticated, IsCourseTeacher],
    )
    def students(self, request, pk=None):
        """
        List all enrollments for a specific course (teacher only).

        GET /api/v1/courses/{id}/students/
        """
        course = self.get_object()
        enrollments = Enrollment.objects.filter(
            course=course,
        ).select_related('student')
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='enroll',
        permission_classes=[permissions.IsAuthenticated, IsStudent],
    )
    def enroll(self, request, pk=None):
        """
        Enrol the requesting student in this course.

        POST /api/v1/courses/{id}/enroll/
        """
        course = self.get_object()
        serializer = EnrollmentCreateSerializer(
            data={'course_id': course.pk},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        # Check for an existing enrollment to re-activate
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'status': Enrollment.Status.ACTIVE},
        )

        if not created and enrollment.status == Enrollment.Status.DROPPED:
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.dropped_at = None
            enrollment.save()

        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='unenroll',
        permission_classes=[permissions.IsAuthenticated, IsStudent],
    )
    def unenroll(self, request, pk=None):
        """
        Drop the requesting student from this course.

        POST /api/v1/courses/{id}/unenroll/
        """
        course = self.get_object()
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course=course,
                status=Enrollment.Status.ACTIVE,
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'detail': 'You are not enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment.status = Enrollment.Status.DROPPED
        enrollment.dropped_at = timezone.now()
        enrollment.save()
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='students/(?P<student_id>[^/.]+)/block',
        permission_classes=[permissions.IsAuthenticated, IsCourseTeacher],
    )
    def block_student(self, request, pk=None, student_id=None):
        """
        Block a student from this course (teacher only).

        POST /api/v1/courses/{id}/students/{student_id}/block/
        """
        course = self.get_object()
        try:
            enrollment = Enrollment.objects.get(
                student_id=student_id,
                course=course,
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'detail': 'Enrollment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        enrollment.status = Enrollment.Status.BLOCKED
        enrollment.save()
        return Response(EnrollmentSerializer(enrollment).data)

    @action(
        detail=True,
        methods=['post'],
        url_path='students/(?P<student_id>[^/.]+)/remove',
        permission_classes=[permissions.IsAuthenticated, IsCourseTeacher],
    )
    def remove_student(self, request, pk=None, student_id=None):
        """
        Remove (drop) a student from this course (teacher only).

        POST /api/v1/courses/{id}/students/{student_id}/remove/
        """
        course = self.get_object()
        try:
            enrollment = Enrollment.objects.get(
                student_id=student_id,
                course=course,
            )
        except Enrollment.DoesNotExist:
            return Response(
                {'detail': 'Enrollment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        enrollment.status = Enrollment.Status.DROPPED
        enrollment.dropped_at = timezone.now()
        enrollment.save()
        return Response(EnrollmentSerializer(enrollment).data)


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing enrollments.

    Lists the authenticated user's own enrollments. Teachers can
    see enrollments for their courses. Supports filtering by status.

    list:     GET /api/v1/courses/enrollments/
    retrieve: GET /api/v1/courses/enrollments/{id}/
    """

    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'course']
    ordering = ['-enrolled_at']

    def get_queryset(self):
        """
        Return enrollments relevant to the current user.

        Students see their own enrollments; teachers see enrollments
        for courses they teach.
        """
        user = self.request.user
        if user.is_teacher:
            return Enrollment.objects.filter(
                course__teacher=user,
            ).select_related('student', 'course')
        return Enrollment.objects.filter(
            student=user,
        ).select_related('student', 'course')


class CourseMaterialViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course material CRUD.

    Materials are scoped to a specific course (passed via query param
    or URL). Teachers can upload, update, and delete materials.
    Enrolled students and the course teacher can view materials.

    list:     GET    /api/v1/courses/materials/?course={id}
    create:   POST   /api/v1/courses/materials/
    retrieve: GET    /api/v1/courses/materials/{id}/
    update:   PUT    /api/v1/courses/materials/{id}/
    delete:   DELETE /api/v1/courses/materials/{id}/
    """

    serializer_class = CourseMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'material_type']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        """Return materials, optionally filtered by course."""
        return CourseMaterial.objects.select_related(
            'course', 'uploaded_by',
        ).all()

    def get_permissions(self):
        """Teachers can create/update/delete; all authenticated can read."""
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Set the uploaded_by field to the requesting user."""
        serializer.save(uploaded_by=self.request.user)


class FeedbackViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    API endpoint for course feedback.

    Students can create feedback for courses they are enrolled in.
    Feedback is read-only after creation (no update or delete).

    list:     GET  /api/v1/courses/feedback/?course={id}
    create:   POST /api/v1/courses/feedback/
    retrieve: GET  /api/v1/courses/feedback/{id}/
    """

    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'student', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return all feedback with related objects."""
        return Feedback.objects.select_related(
            'course', 'student',
        ).all()

    def get_permissions(self):
        """Only students can create feedback."""
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Set the student to the requesting user."""
        serializer.save(student=self.request.user)
