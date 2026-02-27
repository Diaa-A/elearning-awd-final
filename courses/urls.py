"""
URL configuration for the courses application.

Maps URL patterns to views for course management, enrollment,
materials, student management, and feedback.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Course listing and CRUD
    path(
        '',
        views.CourseListView.as_view(),
        name='course-list',
    ),
    path(
        'create/',
        views.CourseCreateView.as_view(),
        name='course-create',
    ),
    path(
        '<int:pk>/',
        views.CourseDetailView.as_view(),
        name='course-detail',
    ),
    path(
        '<int:pk>/edit/',
        views.CourseEditView.as_view(),
        name='course-edit',
    ),

    # Enrollment
    path(
        '<int:pk>/enroll/',
        views.enroll,
        name='course-enroll',
    ),
    path(
        '<int:pk>/unenroll/',
        views.unenroll,
        name='course-unenroll',
    ),

    # Student management (teacher only)
    path(
        '<int:pk>/students/',
        views.CourseStudentListView.as_view(),
        name='course-students',
    ),
    path(
        '<int:pk>/students/<int:student_id>/block/',
        views.block_student,
        name='block-student',
    ),
    path(
        '<int:pk>/students/<int:student_id>/remove/',
        views.remove_student,
        name='remove-student',
    ),

    # Materials
    path(
        '<int:pk>/materials/upload/',
        views.MaterialUploadView.as_view(),
        name='material-upload',
    ),

    # Feedback
    path(
        '<int:pk>/feedback/',
        views.FeedbackCreateView.as_view(),
        name='feedback-create',
    ),
]
