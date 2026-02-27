"""
Forms for the accounts application.

Provides user registration, profile editing, and status update forms
with appropriate validation for the eLearning platform.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, StatusUpdate, User


class UserRegistrationForm(UserCreationForm):
    """
    Registration form for new users.

    Extends Django's UserCreationForm to include role selection (student/teacher),
    email, and name fields. The role determines which features are available
    to the user after registration.
    """

    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your role on the platform.',
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'password1', 'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """Add Bootstrap CSS classes to password fields."""
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class ProfileEditForm(forms.ModelForm):
    """
    Form for editing user profile information.

    Allows users to update their bio, avatar, contact details,
    and role-specific fields like department or student ID.
    """

    class Meta:
        model = Profile
        fields = [
            'bio', 'avatar', 'date_of_birth', 'phone',
            'department', 'student_id', 'enrollment_year',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell others about yourself...',
            }),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'enrollment_year': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class UserEditForm(forms.ModelForm):
    """
    Form for editing basic user account information (name, email).

    Separate from ProfileEditForm because these fields live on the
    User model rather than the Profile model.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class StatusUpdateForm(forms.ModelForm):
    """
    Form for creating a new status update on the user home page.

    Requirement R1(i): Users should be able to add status updates
    to their home page.
    """

    class Meta:
        model = StatusUpdate
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'What is on your mind?',
                'maxlength': 1000,
            }),
        }
