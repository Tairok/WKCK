#!/usr/bin/env python3
"""Tests for dashboard authentication: middleware redirects, password + TOTP login flow."""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bmc_server.settings")

import django

django.setup()

import pyotp
from django.test import SimpleTestCase, override_settings

from services.user_storage import UserStorage

USERNAME = "alice"
EMAIL = "alice@example.com"
PASSWORD = "secret123"


def _post(client, path, body):
    return client.post(path, data=json.dumps(body), content_type="application/json")


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestDashboardAuth(SimpleTestCase):
    """End-to-end checks of the auth flow through the Django test client."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.storage = UserStorage(str(Path(self.tmp_dir) / "users.db"))
        patcher = patch("console.auth_views._get_user_storage", return_value=self.storage)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

    def _register(self):
        """Register the first user and return the TOTP secret from the setup payload."""
        response = _post(self.client, "/api/auth/register", {
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        })
        self.assertEqual(response.status_code, 201)
        return response.json()["secret"]

    def _confirm_mfa(self, secret):
        """Complete the setup step with a valid code; leaves the client logged in."""
        response = _post(self.client, "/api/auth/mfa/verify", {"code": pyotp.TOTP(secret).now()})
        self.assertEqual(response.status_code, 200)
        return response

    def _login_password(self):
        return _post(self.client, "/api/auth/login", {"username": USERNAME, "password": PASSWORD})

    def test_redirect_to_login_when_not_authenticated(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/auth/login")

    def test_api_returns_401_when_not_authenticated(self):
        response = self.client.get("/api/inventory")
        self.assertEqual(response.status_code, 401)

    def test_redirect_when_database_has_no_users(self):
        self.assertEqual(self.client.get("/api/auth/status").json()["has_users"], False)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/auth/login")

    def test_register_returns_mfa_setup_and_no_session(self):
        response = _post(self.client, "/api/auth/register", {
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["setup_required"])
        self.assertIn("<svg", data["qr_svg"])
        self.assertIn("mfa_pending", response.cookies)
        self.assertNotIn("auth_token", response.cookies)

    def test_register_closed_once_a_user_exists(self):
        self.storage.create_user("existing", "existing@example.com", "password1")
        response = _post(self.client, "/api/auth/register", {
            "username": "second",
            "email": "second@example.com",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        })
        self.assertEqual(response.status_code, 403)

    def test_full_setup_then_dashboard_access(self):
        secret = self._register()
        self._confirm_mfa(secret)

        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.get("/api/inventory").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_login_requires_totp_code(self):
        secret = self._register()
        self._confirm_mfa(secret)
        self.client.post("/api/auth/logout")
        self.client.cookies.clear()

        response = self._login_password()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["mfa_required"])
        self.assertFalse(response.json()["setup_required"])
        self.assertNotIn("auth_token", response.cookies)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

        response = _post(self.client, "/api/auth/mfa/verify", {"code": pyotp.TOTP(secret).now()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

    def test_wrong_password_rejected(self):
        secret = self._register()
        self._confirm_mfa(secret)
        self.client.post("/api/auth/logout")

        response = _post(self.client, "/api/auth/login", {"username": USERNAME, "password": "wrong-pass"})
        self.assertEqual(response.status_code, 401)

    def test_mfa_locked_after_five_wrong_codes(self):
        secret = self._register()
        self._confirm_mfa(secret)
        self.client.post("/api/auth/logout")
        self.client.cookies.clear()
        self._login_password()

        totp = pyotp.TOTP(secret)
        # A code that is not valid in the neighbouring time windows either
        now = int(time.time())
        valid_now = {totp.at(now + offset) for offset in (-30, 0, 30)}
        wrong = next(c for c in ("000000", "111111") if c not in valid_now)
        for _ in range(5):
            response = _post(self.client, "/api/auth/mfa/verify", {"code": wrong})
            self.assertEqual(response.json()["error"], "Invalid code")

        response = _post(self.client, "/api/auth/mfa/verify", {"code": totp.now()})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Too many attempts, log in again")

    def test_logout_revokes_server_side_session(self):
        secret = self._register()
        self._confirm_mfa(secret)
        token = self.client.cookies["auth_token"].value

        self.client.post("/api/auth/logout")

        # Replaying the old cookie must fail: the session row was deleted
        self.client.cookies["auth_token"] = token
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_verify_without_pending_challenge_fails(self):
        response = _post(self.client, "/api/auth/mfa/verify", {"code": "123456"})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
