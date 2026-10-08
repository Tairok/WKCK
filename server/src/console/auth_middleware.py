"""Authentication middleware."""

import logging
from django.http import JsonResponse
from datetime import datetime

logger = logging.getLogger(__name__)

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    "/api/health",
    "/api/status",
    "/auth/register",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/logout",
]


class AuthMiddleware:
    """Check if user is authenticated for protected endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Allow public endpoints and static files
        if any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS) or path.startswith("/static"):
            return self.get_response(request)

        # Check authentication for protected endpoints
        session_token = request.COOKIES.get("auth_token")

        if not session_token:
            # Allow static files and template renders
            if request.path.startswith("/static") or request.path == "/":
                return self.get_response(request)

            # API endpoints require auth
            if request.path.startswith("/api"):
                return JsonResponse({
                    "error": "Not authenticated",
                    "timestamp": datetime.now().isoformat()
                }, status=401)

        return self.get_response(request)
