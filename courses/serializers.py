"""
DRF serializers for the courses application.

Provides serialization for Course, Enrollment, CourseMaterial, and
Feedback models. Includes nested teacher data, computed fields for
enrollment counts, and write serializers for creation endpoints.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Course, CourseMaterial, Enrollment, Feedback

User = get_user_model()


class CourseListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for course list endpoints.

    Includes the teacher's username and the current enrollment count
    as computed fields to minimise database queries on list views.
    """

    teacher_name = serializers.CharField(
        source='teacher.get_full_name',
        read_only=True,
    )
    teacher_username = serializers.CharField(
        source='teacher.username',
        read_only=True,
    )
    enrolled_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'code',
            'description',
            'category',
            'max_students',
            'is_active',
            'teacher_name',
            'teacher_username',
            'enrolled_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for course detail endpoints.

    Includes nested materials and feedback counts in addition to all
    the fields from the list serializer.
    """

    teacher_name = serializers.CharField(
        source='teacher.get_full_name',
        read_only=True,
    )
    teacher_username = serializers.CharField(
        source='teacher.username',
        read_only=True,
    )
    enrolled_count = serializers.IntegerField(read_only=True)
    materials_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'code',
            'description',
            'category',
            'max_students',
            'is_active',
            'teacher',
            'teacher_name',
            'teacher_username',
            'enrolled_count',
            'materials_count',
            'average_rating',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'teacher', 'created_at', 'updated_at',
        ]

    def get_materials_count(self, obj):
        """Return the total number of uploaded materials for this course."""
        return obj.materials.count()

    def get_average_rating(self, obj):
        """Return the average feedback rating, or None if no ratings exist."""
        feedbacks = obj.feedbacks.all()
        if not feedbacks.exists():
            return None
        total = sum(f.rating for f in feedbacks)
        return round(total / feedbacks.count(), 1)


class CourseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for course creation.

    The teacher field is automatically set from the request user
    in the viewset's perform_create method.
    """

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'code',
            'description',
            'category',
            'max_students',
            'is_active',
        ]
        read_only_fields = ['id']


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for enrollment records.

    Provides read-only representations of the student and course
    along with the enrollment status and timestamps.
    """

    student_username = serializers.CharField(
        source='student.username',
        read_only=True,
    )
    student_name = serializers.CharField(
        source='student.get_full_name',
        read_only=True,
    )
    course_code = serializers.CharField(
        source='course.code',
        read_only=True,
    )
    course_title = serializers.CharField(
        source='course.title',
        read_only=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'student',
            'student_username',
            'student_name',
            'course',
            'course_code',
            'course_title',
            'status',
            'enrolled_at',
            'dropped_at',
        ]
        read_only_fields = [
            'id', 'student', 'enrolled_at', 'dropped_at',
        ]


class EnrollmentCreateSerializer(serializers.Serializer):
    """
    Serializer for enrollment creation via API.

    Only requires the course ID; the student is taken from the request user.
    Validates that the student is not already enrolled and the course is not full.
    """

    course_id = serializers.IntegerField()

    def validate_course_id(self, value):
        """Ensure the course exists and is active."""
        try:
            course = Course.objects.get(pk=value, is_active=True)
        except Course.DoesNotExist:
            raise serializers.ValidationError(
                'Course not found or is not active.'
            )
        return value

    def validate(self, attrs):
        """Check enrollment eligibility."""
        course = Course.objects.get(pk=attrs['course_id'])
        student = self.context['request'].user

        # Check if already enrolled
        existing = Enrollment.objects.filter(
            student=student,
            course=course,
        ).first()

        if existing:
            if existing.status == Enrollment.Status.ACTIVE:
                raise serializers.ValidationError(
                    'You are already enrolled in this course.'
                )
            if existing.status == Enrollment.Status.BLOCKED:
                raise serializers.ValidationError(
                    'You have been blocked from this course.'
                )

        # Check capacity
        if course.is_full:
            raise serializers.ValidationError(
                'This course has reached its maximum enrollment capacity.'
            )

        attrs['course'] = course
        return attrs


class CourseMaterialSerializer(serializers.ModelSerializer):
    """
    Serializer for course material records.

    Includes the uploader's username and a human-readable file size.
    The file field accepts file uploads via multipart form data.
    """

    uploaded_by_username = serializers.CharField(
        source='uploaded_by.username',
        read_only=True,
    )
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = CourseMaterial
        fields = [
            'id',
            'course',
            'title',
            'description',
            'file',
            'material_type',
            'file_size',
            'file_size_display',
            'uploaded_by',
            'uploaded_by_username',
            'uploaded_at',
        ]
        read_only_fields = [
            'id', 'course', 'file_size', 'uploaded_by', 'uploaded_at',
        ]

    def get_file_size_display(self, obj):
        """Return a human-readable file size string."""
        if obj.file_size < 1024:
            return f'{obj.file_size} B'
        elif obj.file_size < 1024 * 1024:
            return f'{obj.file_size / 1024:.1f} KB'
        else:
            return f'{obj.file_size / (1024 * 1024):.1f} MB'


class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for course feedback records.

    Includes the student's username for display. The student and course
    fields are set automatically by the viewset.
    """

    student_username = serializers.CharField(
        source='student.username',
        read_only=True,
    )
    course_code = serializers.CharField(
        source='course.code',
        read_only=True,
    )

    class Meta:
        model = Feedback
        fields = [
            'id',
            'course',
            'course_code',
            'student',
            'student_username',
            'rating',
            'comment',
            'created_at',
        ]
        read_only_fields = [
            'id', 'course', 'student', 'created_at',
        ]
