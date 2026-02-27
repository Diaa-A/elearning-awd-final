"""
REST API URL configuration for the courses application.

Uses DRF DefaultRouter to generate URL patterns for courses,
enrollments, materials, and feedback endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import (
    CourseMaterialViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    FeedbackViewSet,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='api-course')
router.register(r'enrollments', EnrollmentViewSet, basename='api-enrollment')
router.register(r'materials', CourseMaterialViewSet, basename='api-material')
router.register(r'feedback', FeedbackViewSet, basename='api-feedback')

urlpatterns = [
    path('', include(router.urls)),
]
