"""
eLearning project package initializer.

Imports the Celery app so that it is loaded when Django starts,
ensuring that shared_task decorators in app tasks.py files use
this Celery instance.
"""

from .celery import app as celery_app

__all__ = ('celery_app',)
