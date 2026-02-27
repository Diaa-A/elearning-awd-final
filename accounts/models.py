"""
Models for the accounts application.

Defines the custom User model with role-based access (student/teacher),
an extended Profile model for additional biographical data, and a
StatusUpdate model for user home page posts.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds a role field to distinguish between students and teachers,
    and enforces unique email addresses for all accounts.
    """

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='Determines the user permissions level within the platform.',
    )
    email = models.EmailField(
        unique=True,
        help_text='Required. Used for account identification and notifications.',
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    @property
    def is_teacher(self):
        """Return True if this user has the teacher role."""
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        """Return True if this user has the student role."""
        return self.role == self.Role.STUDENT


class Profile(models.Model):
    """
    Extended user profile storing additional biographical information.

    Automatically created via a post_save signal when a new User is created.
    Contains fields relevant to both students and teachers, with some fields
    being role-specific (e.g. department for teachers, student_id for students).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text='A short biography displayed on the user home page.',
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text='Profile photo. Recommended size: 300x300 pixels.',
    )
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    # Teacher-specific fields
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text='Academic department (teachers only).',
    )

    # Student-specific fields
    student_id = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        null=True,
        help_text='Institutional student ID number.',
    )
    enrollment_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='The year the student enrolled in the institution.',
    )

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f'Profile of {self.user.username}'


class StatusUpdate(models.Model):
    """
    A status update posted by a user to their home page.

    Requirement R1(i): Users should be able to add status updates
    to their home page. These are visible to other users when
    viewing the profile.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='status_updates',
    )
    content = models.TextField(
        max_length=1000,
        help_text='Status update text (max 1000 characters).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Status Update'
        verbose_name_plural = 'Status Updates'

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
