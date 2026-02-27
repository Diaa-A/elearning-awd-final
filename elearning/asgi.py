"""
ASGI config for the eLearning project.

Configures the ASGI application to handle both HTTP and WebSocket protocols.
HTTP requests are routed to Django's standard ASGI handler, while WebSocket
connections are routed through Django Channels with authentication middleware.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings.dev')

# Initialize Django ASGI application early to ensure the AppRegistry is
# populated before importing consumers that depend on Django models.
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    # Standard HTTP requests handled by Django
    'http': django_asgi_app,
    # WebSocket connections routed through authentication middleware
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
