"""
Root URL configuration for the eLearning project.

Routes requests to the appropriate app URL configurations, the Django admin,
the REST API endpoints, and the Swagger/ReDoc API documentation.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

from rest_framework import permissions

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

# ---------------------------------------------------------------------------
# Swagger / OpenAPI schema configuration
# ---------------------------------------------------------------------------
schema_view = get_schema_view(
    openapi.Info(
        title='eLearning Platform API',
        default_version='v1',
        description='REST API for the eLearning web application.',
        contact=openapi.Contact(email='admin@elearning.local'),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


def home(request):
    """
    Render the home/dashboard page.

    Shows different content depending on whether the user is authenticated
    and their role (student or teacher).
    """
    if request.user.is_authenticated:
        context = {}
        if request.user.is_teacher:
            context['taught_courses'] = request.user.taught_courses.all()[:5]
        else:
            active_enrollments = request.user.enrollments.filter(
                status='active',
            ).select_related('course')[:5]
            context['enrollments'] = active_enrollments
        return render(request, 'home.html', context)
    return render(request, 'home.html')


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Home page
    path('', home, name='home'),

    # App template-based views
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),

    # REST API endpoints (versioned under /api/v1/)
    path('api/v1/accounts/', include('accounts.api_urls')),
    path('api/v1/courses/', include('courses.api_urls')),
    path('api/v1/chat/', include('chat.api_urls')),
    path('api/v1/notifications/', include('notifications.api_urls')),

    # API documentation
    path(
        'api/docs/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='redoc',
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
