"""
DRF ViewSets for the notifications application.

Provides API endpoints for listing notifications, retrieving single
notifications, and marking notifications as read. Scoped to the
authenticated user's notifications only.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationMarkReadSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing notifications.

    All endpoints are scoped to the authenticated user's own
    notifications. Supports filtering by type and read status.

    list:     GET /api/v1/notifications/
    retrieve: GET /api/v1/notifications/{id}/
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return the authenticated user's notifications.

        Supports optional query parameter filtering:
        - ?is_read=true/false
        - ?type=enrollment
        """
        queryset = Notification.objects.filter(
            recipient=self.request.user,
        )
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(
                is_read=is_read.lower() in ('true', '1', 'yes'),
            )
        # Filter by notification type
        notif_type = self.request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type)
        return queryset

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """
        Mark a single notification as read.

        POST /api/v1/notifications/{id}/read/
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all unread notifications as read.

        POST /api/v1/notifications/mark-all-read/
        """
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response(
            {'marked_read': updated},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_selected_read(self, request):
        """
        Mark specific notifications as read by ID.

        POST /api/v1/notifications/mark-read/
        Body: {"notification_ids": [1, 2, 3]}
        """
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data.get('notification_ids', [])
        if ids:
            updated = Notification.objects.filter(
                recipient=request.user,
                pk__in=ids,
                is_read=False,
            ).update(is_read=True)
        else:
            # No IDs provided, mark all as read
            updated = Notification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).update(is_read=True)

        return Response(
            {'marked_read': updated},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Return the count of unread notifications.

        GET /api/v1/notifications/unread-count/
        Useful for updating notification badges in the frontend.
        """
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response({'unread_count': count})
