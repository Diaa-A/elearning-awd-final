"""
Views for the accounts application.

Handles user registration, login, logout, profile viewing/editing,
user search (teacher-only), and status update management.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import ProfileEditForm, StatusUpdateForm, UserEditForm, UserRegistrationForm
from .models import StatusUpdate, User


class RegisterView(View):
    """
    Handle user registration with role selection.

    GET: Display the registration form.
    POST: Validate and create a new user account, then log them in.
    """

    def get(self, request):
        """Display the empty registration form."""
        form = UserRegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        """Process the registration form submission."""
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to eLearning, {user.username}!')
            return redirect('home')
        return render(request, 'accounts/register.html', {'form': form})


class ProfileDetailView(LoginRequiredMixin, View):
    """
    Display a user's profile (home page).

    Shows user information, status updates, enrolled/taught courses,
    and allows the profile owner to post new status updates.
    Profiles are discoverable and visible to other authenticated users.
    """

    def get(self, request, pk):
        """Display the user profile with status updates and courses."""
        user = get_object_or_404(User, pk=pk)
        status_updates = user.status_updates.all()[:10]
        status_form = StatusUpdateForm() if request.user == user else None

        # Get course data based on role
        if user.is_teacher:
            courses = user.taught_courses.all()
        else:
            courses = [
                enrollment.course
                for enrollment in user.enrollments.filter(status='active')
                .select_related('course')
            ]

        context = {
            'profile_user': user,
            'status_updates': status_updates,
            'status_form': status_form,
            'courses': courses,
        }
        return render(request, 'accounts/profile.html', context)


class ProfileEditView(LoginRequiredMixin, View):
    """
    Edit the authenticated user's profile information.

    Uses two forms: UserEditForm for basic account fields and
    ProfileEditForm for extended profile data.
    """

    def get(self, request):
        """Display the profile edit forms pre-filled with current data."""
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, 'accounts/profile_edit.html', context)

    def post(self, request):
        """Process the profile edit form submission."""
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(
            request.POST, request.FILES, instance=request.user.profile,
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile-detail', pk=request.user.pk)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, 'accounts/profile_edit.html', context)


class UserSearchView(LoginRequiredMixin, View):
    """
    Search for students and other teachers.

    Requirement R1(c): Teachers should be able to search for students
    and other teachers. The search checks username, first name, last name,
    and email fields.
    """

    def get(self, request):
        """Display search form and results."""
        query = request.GET.get('q', '').strip()
        role_filter = request.GET.get('role', '')
        results = User.objects.none()

        if query:
            results = User.objects.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
            ).exclude(pk=request.user.pk)

            # Apply optional role filter
            if role_filter in ('student', 'teacher'):
                results = results.filter(role=role_filter)

        context = {
            'query': query,
            'role_filter': role_filter,
            'results': results,
        }
        return render(request, 'accounts/search_results.html', context)


@login_required
def status_create(request):
    """
    Create a new status update for the authenticated user.

    Only accepts POST requests. Redirects back to the user's profile
    after creating the status update.
    """
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST)
        if form.is_valid():
            status = form.save(commit=False)
            status.user = request.user
            status.save()
            messages.success(request, 'Status update posted.')
    return redirect('profile-detail', pk=request.user.pk)


@login_required
def status_delete(request, pk):
    """
    Delete a status update.

    Only the status update owner can delete their own updates.
    """
    status = get_object_or_404(StatusUpdate, pk=pk, user=request.user)
    if request.method == 'POST':
        status.delete()
        messages.success(request, 'Status update deleted.')
    return redirect('profile-detail', pk=request.user.pk)
