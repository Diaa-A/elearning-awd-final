"""
Forms for the courses application.

Provides forms for course creation/editing, material upload,
and student feedback with appropriate validation.
"""

from django import forms

from .models import Course, CourseMaterial, Feedback


class CourseForm(forms.ModelForm):
    """
    Form for creating and editing courses.

    Used by teachers to define course details including title, code,
    description, category, and enrollment capacity.
    """

    class Meta:
        model = Course
        fields = ['title', 'code', 'description', 'category', 'max_students', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS101',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Computer Science',
            }),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseMaterialForm(forms.ModelForm):
    """
    Form for uploading course materials.

    Teachers use this form to upload files (PDFs, images, documents)
    to their courses. File type and size are validated by the model field validators.
    """

    class Meta:
        model = CourseMaterial
        fields = ['title', 'description', 'file', 'material_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'material_type': forms.Select(attrs={'class': 'form-select'}),
        }


class FeedbackForm(forms.ModelForm):
    """
    Form for students to leave course feedback.

    Includes a rating (1-5 stars) and a written comment.
    Each student can only submit one feedback per course.
    """

    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'},
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this course...',
            }),
        }
