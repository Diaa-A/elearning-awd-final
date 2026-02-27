"""
Production settings for AWS EC2 deployment.

Extends base settings with production-grade configuration:
- DEBUG disabled
- PostgreSQL database
- Redis for Django Channels (WebSocket) and Celery (background tasks)
- Nginx serves static and media files
- Security headers enabled

All sensitive values are read from environment variables (.env file).
"""

from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Debug mode - must be off in production
# ---------------------------------------------------------------------------
DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

# ---------------------------------------------------------------------------
# Database - PostgreSQL
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ---------------------------------------------------------------------------
# Redis - Channel layer for WebSocket chat + Celery task broker
# ---------------------------------------------------------------------------
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, 6379)],
        },
    },
}

CELERY_BROKER_URL = f'redis://{REDIS_HOST}:6379/1'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:6379/2'

# ---------------------------------------------------------------------------
# Static files - collected to staticfiles/ and served by Nginx
# ---------------------------------------------------------------------------
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ---------------------------------------------------------------------------
# Media files - stored locally and served by Nginx
# ---------------------------------------------------------------------------
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# AWS S3 - Optional media file storage
# Uncomment and configure if you want media files on S3 instead of local disk.
# Requires: pip install django-storages boto3
# ---------------------------------------------------------------------------
# INSTALLED_APPS += ['storages']
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-west-1')
# AWS_DEFAULT_ACL = 'private'
# AWS_S3_FILE_OVERWRITE = False
# AWS_QUERYSTRING_AUTH = True
# AWS_S3_SIGNATURE_VERSION = 's3v4'
# AWS_QUERYSTRING_EXPIRE = 3600

# ---------------------------------------------------------------------------
# CSRF - Trusted origins for form submissions (required in Django 4+)
# Without this, all POST requests (login, register, etc.) will fail with 403.
# ---------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    f'http://{host.strip()}'
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]

# ---------------------------------------------------------------------------
# Security settings for production
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = False   # Set to True when using HTTPS
SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
SECURE_SSL_REDIRECT = False    # Set to True when using HTTPS
