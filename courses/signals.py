"""
Signals for the courses application.

Triggers notification creation when:
- A student enrols on a course (notify the teacher) -- R1(k)
- A teacher uploads new course material (notify enrolled students) -- R1(l)

Uses Celery tasks for async dispatch in production. In development,
CELERY_TASK_ALWAYS_EAGER=True ensures these run synchronously.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CourseMaterial, Enrollment


@receiver(post_save, sender=Enrollment)
def notify_teacher_on_enrollment(sender, instance, created, **kwargs):
    """
    R1(k): When a student enrols on a course, the teacher should be notified.

    Only fires when a new enrollment is created with active status.
    Uses a Celery task to create the notification asynchronously.
    """
    if created and instance.status == Enrollment.Status.ACTIVE:
        from notifications.tasks import create_notification
        create_notification.delay(
            recipient_id=instance.course.teacher_id,
            notification_type='enrollment',
            title=f'New enrollment in {instance.course.code}',
            message=(
                f'{instance.student.get_full_name() or instance.student.username} '
                f'has enrolled in {instance.course.title}.'
            ),
            link=f'/courses/{instance.course.id}/students/',
        )


@receiver(post_save, sender=CourseMaterial)
def notify_students_on_new_material(sender, instance, created, **kwargs):
    """
    R1(l): When new material is added to a course, students should be notified.

    Only fires when a new material is created (not updated).
    Uses a Celery task to create bulk notifications for all enrolled students.
    """
    if created:
        from notifications.tasks import notify_course_students
        notify_course_students.delay(
            course_id=instance.course_id,
            notification_type='new_material',
            title=f'New material in {instance.course.code}',
            message=(
                f'"{instance.title}" has been uploaded to '
                f'{instance.course.title}.'
            ),
            link=f'/courses/{instance.course_id}/',
        )
