"""
DRF ViewSets for the accounts application.

Provides API endpoints for user registration, user listing/detail,
profile management, and status updates. Uses custom permissions to
enforce role-based access where needed.
"""

from django.contrib.auth import get_user_model
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from elearning.permissions import IsOwnerOrReadOnly

from .models import Profile, StatusUpdate
from .serializers import (
    ProfileSerializer,
    StatusUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving users.

    Supports search by username, first name, last name, and email.
    Supports filtering by role via query parameter (?role=teacher).
    Only authenticated users can access this endpoint.

    list:   GET /api/v1/accounts/users/
    detail: GET /api/v1/accounts/users/{id}/
    """

    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined']
    ordering = ['username']

    def get_queryset(self):
        """
        Optionally filter the user list by role.

        Query parameter: ?role=student or ?role=teacher
        """
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        if role in ('student', 'teacher'):
            queryset = queryset.filter(role=role)
        return queryset

    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """
        Return the profile data for the currently authenticated user.

        GET /api/v1/accounts/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for user registration.

    Creates a new user account and returns an authentication token.
    This endpoint is publicly accessible (no authentication required).

    create: POST /api/v1/accounts/register/
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Register a new user and return their data with an auth token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create an API authentication token for the new user
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                'user': UserSerializer(user).data,
                'token': token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API endpoint for viewing and updating user profiles.

    Users can only update their own profile. Profiles are accessed
    by user ID (not profile ID) for convenience.

    retrieve: GET /api/v1/accounts/profiles/{user_id}/
    update:   PUT/PATCH /api/v1/accounts/profiles/{user_id}/
    """

    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'user_id'


class StatusUpdateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CRUD operations on status updates.

    Users can create status updates (assigned to themselves) and
    can only edit or delete their own updates. All authenticated
    users can list and view status updates.

    list:     GET    /api/v1/accounts/status-updates/
    create:   POST   /api/v1/accounts/status-updates/
    retrieve: GET    /api/v1/accounts/status-updates/{id}/
    update:   PUT    /api/v1/accounts/status-updates/{id}/
    delete:   DELETE /api/v1/accounts/status-updates/{id}/
    """

    serializer_class = StatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Return all status updates, optionally filtered by user ID.

        Query parameter: ?user_id=123
        """
        queryset = StatusUpdate.objects.select_related('user').all()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        """Assign the status update to the requesting user."""
        serializer.save(user=self.request.user)
