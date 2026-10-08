"""Authentication middleware: every page and API needs a valid session, except the public list."""

import logging
from django.http import JsonResponse
from django.shortcuts import redirect
from datetime import datetime

from console.auth_views import get_current_user

logger = logging.getLogger(__name__)

LOGIN_PATH = "/auth/login"

# Exact paths that never require a session
PUBLIC_PATHS = {
    "/api/health",
    "/api/status",
}

# Path prefixes that never require a session (login flow and static files)
PUBLIC_PREFIXES = (
    "/static/",
    "/auth/",
    "/api/auth/",
)


class AuthMiddleware:
    """Redirect unauthenticated page requests to the login page; 401 for API calls."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return self.get_response(request)

        if get_current_user(request):
            return self.get_response(request)

        if path.startswith("/api/"):
            return JsonResponse({
                "error": "Not authenticated",
                "timestamp": datetime.now().isoformat()
            }, status=401)

        return redirect(LOGIN_PATH)
