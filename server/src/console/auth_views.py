"""Authentication views: password login followed by TOTP (MFA)."""

import hashlib
import io
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path

import pyotp
import qrcode
import qrcode.image.svg
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from config import Config
from services.user_storage import get_user_storage

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "auth_token"
SESSION_EXPIRY_DAYS = 7
MFA_COOKIE_NAME = "mfa_pending"
MFA_PENDING_SECONDS = 300
MFA_MAX_ATTEMPTS = 5
TOTP_ISSUER = "BMC Console"

# In-memory MFA challenges: token -> {user_id, setup, expires, attempts}.
# Lost on restart, which just means the user logs in again.
_pending_mfa = {}


def _get_user_storage():
    """Get user storage instance."""
    db_path = Path(Config.BASE_PATH) / "data" / "users.db"
    return get_user_storage(str(db_path))


def _error(message, status):
    return JsonResponse({
        "error": message,
        "timestamp": datetime.now().isoformat()
    }, status=status)


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def get_current_user(request):
    """Return the user for a valid session cookie, or None."""
    token = request.COOKIES.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    return _get_user_storage().get_session_user(_hash_token(token))


def _totp_setup_payload(username, secret):
    """Provisioning data for an authenticator app: URI, secret and QR code as SVG."""
    uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=TOTP_ISSUER)
    buf = io.BytesIO()
    qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage).save(buf)
    return {
        "otpauth_uri": uri,
        "secret": secret,
        "qr_svg": buf.getvalue().decode(),
    }


def _start_mfa_challenge(response, user_id, setup):
    """Create a pending MFA challenge and set its cookie on the response."""
    token = secrets.token_urlsafe(32)
    _pending_mfa[token] = {
        "user_id": user_id,
        "setup": setup,
        "expires": time.time() + MFA_PENDING_SECONDS,
        "attempts": 0,
    }
    response.set_cookie(
        MFA_COOKIE_NAME,
        token,
        max_age=MFA_PENDING_SECONDS,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="Lax"
    )
    return response


def _get_mfa_challenge(request):
    """Return the pending MFA challenge for this request, dropping it if expired."""
    token = request.COOKIES.get(MFA_COOKIE_NAME)
    if not token:
        return None, None
    challenge = _pending_mfa.get(token)
    if not challenge or challenge["expires"] < time.time():
        _pending_mfa.pop(token, None)
        return None, None
    return token, challenge


@require_http_methods(["GET"])
def status(request):
    """Tell the login page whether any user exists yet."""
    return JsonResponse({
        "has_users": _get_user_storage().count_users() > 0,
        "timestamp": datetime.now().isoformat()
    }, status=200)


@require_http_methods(["POST"])
def register(request):
    """Register the first user. Only allowed while the user table is empty."""
    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        password_confirm = data.get("password_confirm", "").strip()

        storage = _get_user_storage()
        if storage.count_users() > 0:
            return _error("Registration is closed", 403)

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

        # Create user
        user = storage.create_user(username, email, password)

        if not user:
            return _error("Failed to create user", 500)

        # MFA must be confirmed before the account is usable
        secret = pyotp.random_base32()
        storage.set_totp_secret(user["id"], secret)

        logger.info(f"[AUTH] New user registered: {username}")

        response = JsonResponse({
            "message": "User created. Configure MFA to finish.",
            "user": user,
            "mfa_required": True,
            "setup_required": True,
            **_totp_setup_payload(username, secret),
            "timestamp": datetime.now().isoformat()
        }, status=201)
        return _start_mfa_challenge(response, user["id"], setup=True)

    except json.JSONDecodeError:
        return _error("Invalid JSON", 400)
    except Exception as e:
        logger.error(f"[AUTH] Registration failed: {e}")
        return _error("Registration failed", 500)


@require_http_methods(["POST"])
def login(request):
    """Step 1: check password. Session is only created after the MFA step."""
    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return _error("Missing username or password", 400)

        storage = _get_user_storage()
        user = storage.authenticate(username, password)

        if not user:
            logger.warning(f"[AUTH] Failed login attempt: {username}")
            return _error("Invalid username or password", 401)

        mfa = storage.get_mfa_state(user["id"])

        if mfa["totp_enabled"]:
            response = JsonResponse({
                "mfa_required": True,
                "setup_required": False,
                "timestamp": datetime.now().isoformat()
            }, status=200)
            return _start_mfa_challenge(response, user["id"], setup=False)

        # Account has no confirmed MFA yet: show the setup again (reuse the stored secret)
        secret = mfa["totp_secret"] or pyotp.random_base32()
        if not mfa["totp_secret"]:
            storage.set_totp_secret(user["id"], secret)

        response = JsonResponse({
            "mfa_required": True,
            "setup_required": True,
            **_totp_setup_payload(username, secret),
            "timestamp": datetime.now().isoformat()
        }, status=200)
        return _start_mfa_challenge(response, user["id"], setup=True)

    except json.JSONDecodeError:
        return _error("Invalid JSON", 400)
    except Exception as e:
        logger.error(f"[AUTH] Login failed: {e}")
        return _error("Login failed", 500)


@require_http_methods(["POST"])
def mfa_verify(request):
    """Step 2: check the TOTP code and create the session."""
    try:
        data = json.loads(request.body)
        code = str(data.get("code", "")).replace(" ", "").strip()

        token, challenge = _get_mfa_challenge(request)
        if not challenge:
            return _error("MFA session expired, log in again", 401)

        if challenge["attempts"] >= MFA_MAX_ATTEMPTS:
            _pending_mfa.pop(token, None)
            logger.warning(f"[AUTH] Too many MFA attempts for user id {challenge['user_id']}")
            return _error("Too many attempts, log in again", 401)

        storage = _get_user_storage()
        mfa = storage.get_mfa_state(challenge["user_id"])
        if not mfa or not mfa["totp_secret"]:
            _pending_mfa.pop(token, None)
            return _error("MFA session expired, log in again", 401)

        if not pyotp.TOTP(mfa["totp_secret"]).verify(code, valid_window=1):
            challenge["attempts"] += 1
            logger.warning(f"[AUTH] Invalid MFA code for user: {mfa['username']}")
            return _error("Invalid code", 401)

        _pending_mfa.pop(token, None)

        if challenge["setup"]:
            storage.enable_totp(mfa["id"])
            logger.info(f"[AUTH] MFA enabled for user: {mfa['username']}")

        session_token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
        storage.purge_expired_sessions()
        storage.create_session(
            mfa["id"],
            _hash_token(session_token),
            request.META.get("REMOTE_ADDR", ""),
            request.META.get("HTTP_USER_AGENT", "")[:255],
            expires,
        )

        logger.info(f"[AUTH] User logged in: {mfa['username']}")

        response = JsonResponse({
            "message": "Logged in successfully",
            "user": {"id": mfa["id"], "username": mfa["username"], "email": mfa["email"]},
            "timestamp": datetime.now().isoformat()
        }, status=200)
        response.set_cookie(
            SESSION_COOKIE_NAME,
            session_token,
            max_age=SESSION_EXPIRY_DAYS * 86400,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax"
        )
        response.delete_cookie(MFA_COOKIE_NAME)
        return response

    except json.JSONDecodeError:
        return _error("Invalid JSON", 400)
    except Exception as e:
        logger.error(f"[AUTH] MFA verification failed: {e}")
        return _error("MFA verification failed", 500)


@require_http_methods(["POST"])
def logout(request):
    """Logout user: drop the server-side session and the cookie."""
    token = request.COOKIES.get(SESSION_COOKIE_NAME)
    if token:
        _get_user_storage().delete_session(_hash_token(token))

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
    user = get_current_user(request)
    if not user:
        return _error("Not authenticated", 401)

    return JsonResponse({
        "authenticated": True,
        "user": user,
        "timestamp": datetime.now().isoformat()
    }, status=200)


def auth_page(request):
    """Serve the login page, or send already-authenticated users to the dashboard."""
    if get_current_user(request):
        return redirect("/")
    return render(request, "auth.html")
