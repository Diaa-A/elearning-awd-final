"""
Template context processors for the notifications app.

Injects the unread notification count into every template context,
allowing the navbar badge to display without explicit view logic.
"""


def unread_notification_count(request):
    """
    Add the count of unread notifications for the authenticated user
    to the template context. Returns 0 for anonymous users.
    """
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notification_count': count}
    return {'unread_notification_count': 0}
