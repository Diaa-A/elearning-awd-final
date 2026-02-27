"""
Custom validators for the courses application.

Provides file extension and file size validation for course material uploads.
These validators are applied to the CourseMaterial.file field to ensure
only approved file types within the size limit are accepted.
"""

from django.core.exceptions import ValidationError


# Allowed file extensions for course material uploads
ALLOWED_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    'jpg', 'jpeg', 'png', 'gif', 'svg',
    'mp4', 'webm',
    'zip', 'rar',
    'txt', 'csv',
]

# Maximum file size in bytes (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def validate_file_extension(value):
    """
    Validate that the uploaded file has an allowed extension.

    Extracts the file extension from the filename and checks it
    against the ALLOWED_EXTENSIONS list. Raises a ValidationError
    if the extension is not permitted.
    """
    ext = value.name.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '.{ext}' is not allowed. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def validate_file_size(value):
    """
    Validate that the uploaded file does not exceed the maximum size limit.

    Raises a ValidationError if the file size exceeds MAX_FILE_SIZE (50 MB).
    """
    if value.size > MAX_FILE_SIZE:
        size_mb = value.size / (1024 * 1024)
        raise ValidationError(
            f'File size {size_mb:.1f} MB exceeds the maximum of '
            f'{MAX_FILE_SIZE / (1024 * 1024):.0f} MB.'
        )
