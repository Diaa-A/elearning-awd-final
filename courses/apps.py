"""
Application configuration for the courses app.
"""

from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    verbose_name = 'Courses'

    def ready(self):
        """Import signals when the app is ready."""
        import courses.signals  # noqa: F401
