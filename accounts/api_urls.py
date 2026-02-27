"""
REST API URL configuration for the accounts application.

Uses DRF DefaultRouter to automatically generate URL patterns for
user, profile, registration, and status update endpoints.
"""

from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .viewsets import (
    ProfileViewSet,
    RegistrationViewSet,
    StatusUpdateViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='api-user')
router.register(r'register', RegistrationViewSet, basename='api-register')
router.register(r'profiles', ProfileViewSet, basename='api-profile')
router.register(r'status-updates', StatusUpdateViewSet, basename='api-status')

urlpatterns = [
    # Token authentication endpoint
    path('token/', obtain_auth_token, name='api-token-auth'),
    # Router-generated endpoints
    path('', include(router.urls)),
]
