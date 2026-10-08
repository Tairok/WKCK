"""Authentication views."""

import json
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from config import Config
from services.user_storage import get_user_storage

logger = logging.getLogger(__name__)
SESSION_COOKIE_NAME = "auth_token"
SESSION_EXPIRY_DAYS = 7


def _get_user_storage():
    """Get user storage instance."""
    db_path = Path(Config.BASE_PATH) / "data" / "users.db"
    return get_user_storage(str(db_path))


@require_http_methods(["POST"])
def register(request):
    """Register new user."""
    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        password_confirm = data.get("password_confirm", "").strip()

        # Validation
        if not username or not email or not password:
            return JsonResponse({
                "error": "Missing required fields",
                "timestamp": datetime.now().isoformat()
            }, status=400)

        if len(username) < 3:
            return JsonResponse({
                "error": "Username must be at least 3 characters",
                "timestamp": datetime.now().isoformat()
            }, status=400)

        if len(password) < 6:
            return JsonResponse({
                "error": "Password must be at least 6 characters",
                "timestamp": datetime.now().isoformat()
            }, status=400)

        if password != password_confirm:
            return JsonResponse({
                "error": "Passwords do not match",
                "timestamp": datetime.now().isoformat()
            }, status=400)

        if "@" not in email:
            return JsonResponse({
                "error": "Invalid email address",
                "timestamp": datetime.now().isoformat()
            }, status=400)

        storage = _get_user_storage()

        # Check if username exists
        if storage.user_exists(username):
            return JsonResponse({
                "error": "Username already taken",
                "timestamp": datetime.now().isoformat()
            }, status=409)

        # Create user
        user = storage.create_user(username, email, password)

        if not user:
            return JsonResponse({
                "error": "Failed to create user",
                "timestamp": datetime.now().isoformat()
            }, status=500)

        logger.info(f"[AUTH] New user registered: {username}")

        return JsonResponse({
            "message": "User created successfully",
            "user": user,
            "timestamp": datetime.now().isoformat()
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON",
            "timestamp": datetime.now().isoformat()
        }, status=400)
    except Exception as e:
        logger.error(f"[AUTH] Registration failed: {e}")
        return JsonResponse({
            "error": "Registration failed",
            "timestamp": datetime.now().isoformat()
        }, status=500)


@require_http_methods(["POST"])
def login(request):
    """Login user."""
    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return JsonResponse({
                "error": "Missing username or password",
                "timestamp": datetime.now().isoformat()
            }, status=400)

        storage = _get_user_storage()
        user = storage.authenticate(username, password)

        if not user:
            logger.warning(f"[AUTH] Failed login attempt: {username}")
            return JsonResponse({
                "error": "Invalid username or password",
                "timestamp": datetime.now().isoformat()
            }, status=401)

        logger.info(f"[AUTH] User logged in: {username}")

        response = JsonResponse({
            "message": "Logged in successfully",
            "user": user,
            "timestamp": datetime.now().isoformat()
        }, status=200)

        # Set session cookie
        session_token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)

        response.set_cookie(
            SESSION_COOKIE_NAME,
            session_token,
            max_age=SESSION_EXPIRY_DAYS * 86400,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax"
        )

        return response

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON",
            "timestamp": datetime.now().isoformat()
        }, status=400)
    except Exception as e:
        logger.error(f"[AUTH] Login failed: {e}")
        return JsonResponse({
            "error": "Login failed",
            "timestamp": datetime.now().isoformat()
        }, status=500)


@require_http_methods(["POST"])
def logout(request):
    """Logout user."""
    response = JsonResponse({
        "message": "Logged out successfully",
        "timestamp": datetime.now().isoformat()
    }, status=200)

    response.delete_cookie(SESSION_COOKIE_NAME)
    logger.debug("[AUTH] User logged out")

    return response


@require_http_methods(["GET"])
def me(request):
    """Get current user info."""
    session_token = request.COOKIES.get(SESSION_COOKIE_NAME)

    if not session_token:
        return JsonResponse({
            "error": "Not authenticated",
            "timestamp": datetime.now().isoformat()
        }, status=401)

    return JsonResponse({
        "authenticated": True,
        "timestamp": datetime.now().isoformat()
    }, status=200)


def auth_page(request):
    """Serve authentication page."""
    return render(request, "auth.html")
