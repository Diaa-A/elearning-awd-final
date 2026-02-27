"""
Django admin configuration for the accounts application.

Registers User, Profile, and StatusUpdate models with custom
display options, search fields, and filters for administrative use.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, StatusUpdate, User


class ProfileInline(admin.StackedInline):
    """Inline display of Profile on the User admin page."""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model with role-based display."""
    inlines = [ProfileInline]
    list_display = [
        'username', 'email', 'first_name', 'last_name', 'role', 'is_active',
    ]
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    # Add role field to the add/change forms
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin for the Profile model."""
    list_display = ['user', 'department', 'student_id', 'phone']
    search_fields = ['user__username', 'user__email', 'department']
    list_filter = ['department']


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    """Admin for the StatusUpdate model."""
    list_display = ['user', 'content_preview', 'created_at']
    search_fields = ['user__username', 'content']
    list_filter = ['created_at']
    ordering = ['-created_at']

    def content_preview(self, obj):
        """Return truncated content for the list display."""
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Content'
