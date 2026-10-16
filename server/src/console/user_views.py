"""User management views: any logged-in user can list and add accounts.

A new account gets no MFA secret here. Its owner sets up TOTP on the first login
(see auth_views.login, which generates the secret when totp_enabled is 0).
"""

import json
import logging
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from console.auth_views import _error, _get_user_storage, get_current_user

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def users(request):
    """GET: list accounts. POST: create an account (MFA is set up at its first login)."""
    if request.method == "GET":
        return JsonResponse({
            "users": _get_user_storage().list_users(),
            "timestamp": datetime.now().isoformat()
        }, status=200)

    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        password_confirm = data.get("password_confirm", "").strip()

        if not username or not email or not password:
            return _error("Missing required fields", 400)

        if len(username) < 3:
            return _error("Username must be at least 3 characters", 400)

        if len(password) < 6:
            return _error("Password must be at least 6 characters", 400)

        if password != password_confirm:
            return _error("Passwords do not match", 400)

        if "@" not in email:
            return _error("Invalid email address", 400)

        user = _get_user_storage().create_user(username, email, password)
        if not user:
            # create_user returns None for duplicate username or email (and for storage errors)
            return _error("Username or email already exists", 409)

        logger.info(f"[USERS] Account {username} created by {get_current_user(request)['username']}")
        return JsonResponse({
            "message": "User created. They will set up MFA at first login.",
            "user": user,
            "timestamp": datetime.now().isoformat()
        }, status=201)

    except json.JSONDecodeError:
        return _error("Invalid JSON", 400)
    except Exception as e:
        logger.error(f"[USERS] Failed to create user: {e}")
        return _error("Failed to create user", 500)
