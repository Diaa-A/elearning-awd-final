"""
DRF serializers for the accounts application.

Provides serialization for User, Profile, and StatusUpdate models,
including nested profile data within user representations and
registration with password hashing.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Profile, StatusUpdate

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model.

    Exposes all editable profile fields. The user field is read-only
    because profiles are always accessed in the context of their owning user.
    """

    class Meta:
        model = Profile
        fields = [
            'id',
            'bio',
            'avatar',
            'date_of_birth',
            'phone',
            'department',
            'student_id',
            'enrollment_year',
        ]
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for reading user data.

    Includes a nested read-only profile and computed full_name field.
    Does not expose password or other sensitive authentication fields.
    """

    profile = ProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'date_joined',
            'profile',
        ]
        read_only_fields = ['id', 'username', 'date_joined']

    def get_full_name(self, obj):
        """Return the user's full name or username as fallback."""
        return obj.get_full_name() or obj.username


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration via the API.

    Accepts username, email, password, role, and optional name fields.
    Passwords are write-only and properly hashed using Django's
    create_user method.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Minimum 8 characters.',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Must match the password field.',
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'password',
            'password_confirm',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """Ensure both password fields match."""
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        """Create a new user with a properly hashed password."""
        return User.objects.create_user(**validated_data)


class StatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for user status updates.

    The user field is set automatically from the request context and
    is displayed as a username string for readability.
    """

    user = serializers.StringRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StatusUpdate
        fields = [
            'id',
            'user',
            'username',
            'content',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'username', 'created_at', 'updated_at']
