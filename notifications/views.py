"""
Views for the notifications application.

Handles notification listing, marking as read, and bulk mark-all-read.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import Notification


class NotificationListView(LoginRequiredMixin, View):
    """Display all notifications for the authenticated user."""

    def get(self, request):
        """List notifications, newest first."""
        notifications = request.user.notifications.all()[:50]
        context = {'notifications': notifications}
        return render(request, 'notifications/notification_list.html', context)


@login_required
def mark_read(request, pk):
    """Mark a single notification as read and redirect to its link if available."""
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user,
    )
    notification.is_read = True
    notification.save()

    # Redirect to the notification's link if it has one
    if notification.link:
        return redirect(notification.link)
    return redirect('notification-list')


@login_required
def mark_all_read(request):
    """Mark all unread notifications as read for the authenticated user."""
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
    return redirect('notification-list')
