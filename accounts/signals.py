"""
Signals for the accounts application.

Automatically creates a Profile instance when a new User is created,
ensuring every user always has an associated profile for their home page.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile for every newly created User."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile whenever the User is saved."""
    instance.profile.save()
