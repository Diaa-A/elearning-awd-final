"""
Celery configuration for the eLearning project.

Sets up Celery to use Redis as the message broker and auto-discovers
task modules from all registered Django apps. Used primarily for
asynchronous notification dispatch when students enrol or teachers
upload new course materials.
"""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings.dev')

# Create the Celery application instance
app = Celery('elearning')

# Load Celery config from Django settings, using the CELERY_ namespace
# so that all Celery-related settings must be prefixed with CELERY_.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all installed Django apps
app.autodiscover_tasks()
