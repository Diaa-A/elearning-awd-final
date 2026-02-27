"""
Celery tasks for the notifications application.

Provides asynchronous notification creation to avoid blocking HTTP
responses when enrollment or material upload events trigger bulk
notification generation.
"""

from celery import shared_task


@shared_task
def create_notification(recipient_id, notification_type, title, message, link=''):
    """
    Create a single notification for one user.

    Called when a student enrols on a course to notify the teacher.
    Uses shared_task so it works with CELERY_TASK_ALWAYS_EAGER in dev.
    """
    from .models import Notification

    Notification.objects.create(
        recipient_id=recipient_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )


@shared_task
def notify_course_students(course_id, notification_type, title, message, link=''):
    """
    Create notifications for all actively enrolled students in a course.

    Called when a teacher uploads new course material. Uses bulk_create
    for efficiency when notifying many students at once.
    """
    from courses.models import Enrollment
    from .models import Notification

    # Get all active student IDs for this course
    student_ids = Enrollment.objects.filter(
        course_id=course_id,
        status=Enrollment.Status.ACTIVE,
    ).values_list('student_id', flat=True)

    # Bulk create notifications for all enrolled students
    notifications = [
        Notification(
            recipient_id=student_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
        )
        for student_id in student_ids
    ]
    Notification.objects.bulk_create(notifications)
