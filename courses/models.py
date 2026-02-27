"""
Models for the courses application.

Defines the Course, Enrollment, CourseMaterial, and Feedback models.
These represent the core business logic of the eLearning platform:
teachers create courses, students enrol, teachers upload materials,
and students leave feedback.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_file_extension, validate_file_size


class Course(models.Model):
    """
    Represents a course created by a teacher.

    Requirement R1(d): Teachers should be able to create courses and
    upload course material. Each course has a unique code, a description,
    and tracks enrollment capacity.
    """

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_courses',
        limit_choices_to={'role': 'teacher'},
        help_text='The teacher who owns and manages this course.',
    )
    title = models.CharField(max_length=200)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique course code, e.g. "CS101".',
    )
    description = models.TextField(
        help_text='Detailed description of the course content and objectives.',
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text='Subject category, e.g. "Computer Science", "Mathematics".',
    )
    max_students = models.PositiveIntegerField(
        default=50,
        help_text='Maximum number of students that can enrol.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the course is currently accepting enrollments.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return f'{self.code} - {self.title}'

    @property
    def enrolled_count(self):
        """Return the number of actively enrolled students."""
        return self.enrollments.filter(status=Enrollment.Status.ACTIVE).count()

    @property
    def is_full(self):
        """Return True if the course has reached its enrollment capacity."""
        return self.enrolled_count >= self.max_students


class Enrollment(models.Model):
    """
    Junction table linking students to courses.

    Uses an explicit through-model rather than a simple ManyToMany field
    so that we can store enrollment status (active, dropped, blocked)
    and timestamps. This supports requirements R1(e) for enrollment
    and R1(h) for teacher blocking/removing students.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DROPPED = 'dropped', 'Dropped'
        BLOCKED = 'blocked', 'Blocked'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    dropped_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # Enforce one enrollment record per student per course
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'

    def __str__(self):
        return f'{self.student.username} -> {self.course.code} [{self.status}]'


class CourseMaterial(models.Model):
    """
    Files uploaded by teachers as course content.

    Requirement R1(j): Teachers should add files such as teaching materials
    to their account, accessible via the course home page. Supports PDFs,
    images, documents, and other common file types with size validation.
    """

    MATERIAL_TYPES = [
        ('pdf', 'PDF Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='materials',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_materials',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(
        blank=True,
        help_text='Optional description of this material.',
    )
    file = models.FileField(
        upload_to='course_materials/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
    )
    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPES,
        default='other',
    )
    file_size = models.PositiveIntegerField(
        editable=False,
        default=0,
        help_text='File size in bytes, set automatically on save.',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Course Material'
        verbose_name_plural = 'Course Materials'

    def save(self, *args, **kwargs):
        """Override save to automatically record the file size."""
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} ({self.course.code})'


class Feedback(models.Model):
    """
    Student feedback and rating for a course.

    Requirement R1(f): Students should be able to leave feedback for
    a particular course. Each student can only leave one review per course,
    enforced by the unique_together constraint.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='feedbacks',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks_given',
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 (poor) to 5 (excellent).',
    )
    comment = models.TextField(
        max_length=2000,
        help_text='Written feedback about the course (max 2000 characters).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One feedback per student per course
        unique_together = ['course', 'student']
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'

    def __str__(self):
        return f'{self.student.username} -> {self.course.code}: {self.rating}/5'
