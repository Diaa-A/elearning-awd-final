"""
URL configuration for the accounts application.

Maps URL patterns to views for registration, authentication,
profile management, user search, and status updates.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Registration
    path(
        'register/',
        views.RegisterView.as_view(),
        name='register',
    ),

    # Authentication (using Django's built-in auth views)
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='accounts/login.html'),
        name='login',
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout',
    ),

    # Profile
    path(
        'profile/<int:pk>/',
        views.ProfileDetailView.as_view(),
        name='profile-detail',
    ),
    path(
        'profile/edit/',
        views.ProfileEditView.as_view(),
        name='profile-edit',
    ),

    # User search
    path(
        'search/',
        views.UserSearchView.as_view(),
        name='user-search',
    ),

    # Status updates
    path(
        'status/create/',
        views.status_create,
        name='status-create',
    ),
    path(
        'status/<int:pk>/delete/',
        views.status_delete,
        name='status-delete',
    ),
]
