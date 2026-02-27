"""
Development settings.

Extends base settings with local development configuration:
- DEBUG mode enabled
- SQLite database for zero-setup local development
- Celery tasks run synchronously (no Celery worker needed)
- In-memory channel layer for real-time WebSocket chat (no Redis needed)
- Console email backend for testing
"""

from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Debug mode
# ---------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ---------------------------------------------------------------------------
# Database - SQLite for local development (zero external dependencies)
#
# For production, PostgreSQL is configured in prod.py. If you want to use
# PostgreSQL locally, uncomment the block below and comment out SQLite.
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Uncomment below for local PostgreSQL (requires PostgreSQL to be installed):
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'elearning_db'),
#         'USER': os.environ.get('DB_USER', 'postgres'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#     }
# }

# ---------------------------------------------------------------------------
# Celery - Run tasks synchronously in development
# This means notifications will be created immediately without needing
# a running Celery worker or Redis instance for task processing.
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# Channels - In-memory channel layer for development
# No Redis server required. Production uses Redis (see prod.py).
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# ---------------------------------------------------------------------------
# Email - Print to console during development
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
