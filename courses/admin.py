"""
Django admin configuration for the courses application.

Registers Course, Enrollment, CourseMaterial, and Feedback models
with custom display, filtering, and search capabilities.
"""

from django.contrib import admin

from .models import Course, CourseMaterial, Enrollment, Feedback


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin for the Course model."""
    list_display = [
        'code', 'title', 'teacher', 'category', 'enrolled_count',
        'max_students', 'is_active', 'created_at',
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['title', 'code', 'description', 'teacher__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin for the Enrollment model."""
    list_display = ['student', 'course', 'status', 'enrolled_at']
    list_filter = ['status', 'enrolled_at']
    search_fields = [
        'student__username', 'student__email',
        'course__title', 'course__code',
    ]
    ordering = ['-enrolled_at']


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    """Admin for the CourseMaterial model."""
    list_display = [
        'title', 'course', 'uploaded_by', 'material_type',
        'file_size_display', 'uploaded_at',
    ]
    list_filter = ['material_type', 'uploaded_at']
    search_fields = ['title', 'description', 'course__title', 'course__code']
    ordering = ['-uploaded_at']

    def file_size_display(self, obj):
        """Return human-readable file size."""
        if obj.file_size < 1024:
            return f'{obj.file_size} B'
        elif obj.file_size < 1024 * 1024:
            return f'{obj.file_size / 1024:.1f} KB'
        return f'{obj.file_size / (1024 * 1024):.1f} MB'
    file_size_display.short_description = 'File Size'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin for the Feedback model."""
    list_display = ['student', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['student__username', 'course__title', 'comment']
    ordering = ['-created_at']
