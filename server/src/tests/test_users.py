#!/usr/bin/env python3
"""Tests for user management: admin-created accounts must set up MFA at their first login."""

import json
import os
import shutil
import sys
import tempfile
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

ADMIN = ("admin", "admin@example.com", "secret123")
NEW = ("bob", "bob@example.com", "bobpass1")


def _post(client, path, body):
    return client.post(path, data=json.dumps(body), content_type="application/json")


@override_settings(ALLOWED_HOSTS=["testserver"])
class TestUserManagement(SimpleTestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.storage = UserStorage(str(Path(self.tmp_dir) / "users.db"))
        for target in ("console.auth_views._get_user_storage", "console.user_views._get_user_storage"):
            patcher = patch(target, return_value=self.storage)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

        # Log in the admin with MFA fully configured
        username, email, password = ADMIN
        self.admin_secret = pyotp.random_base32()
        admin = self.storage.create_user(username, email, password)
        self.storage.set_totp_secret(admin["id"], self.admin_secret)
        self.storage.enable_totp(admin["id"])
        _post(self.client, "/api/auth/login", {"username": username, "password": password})
        _post(self.client, "/api/auth/mfa/verify", {"code": pyotp.TOTP(self.admin_secret).now()})

    def _create(self, username, email, password, confirm=None):
        return _post(self.client, "/api/users", {
            "username": username,
            "email": email,
            "password": password,
            "password_confirm": password if confirm is None else confirm,
        })

    def test_list_requires_session(self):
        self.client.cookies.clear()
        self.assertEqual(self.client.get("/api/users").status_code, 401)

    def test_list_returns_users_without_secrets(self):
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        users = response.json()["users"]
        self.assertEqual([u["username"] for u in users], [ADMIN[0]])
        self.assertNotIn("password_hash", users[0])
        self.assertNotIn("totp_secret", users[0])
        self.assertTrue(users[0]["totp_enabled"])

    def test_create_user_without_mfa(self):
        response = self._create(*NEW)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("qr_svg", response.json())
        state = self.storage.get_mfa_state(response.json()["user"]["id"])
        self.assertIsNone(state["totp_secret"])
        self.assertFalse(state["totp_enabled"])
        self.assertNotIn("mfa_pending", response.cookies)

    def test_create_validation(self):
        self.assertEqual(self._create("ab", NEW[1], NEW[2]).status_code, 400)
        self.assertEqual(self._create(NEW[0], "not-an-email", NEW[2]).status_code, 400)
        self.assertEqual(self._create(NEW[0], NEW[1], "123", "123").status_code, 400)
        self.assertEqual(self._create(NEW[0], NEW[1], NEW[2], "different").status_code, 400)
        self.assertEqual(self._create("", NEW[1], NEW[2]).status_code, 400)

    def test_duplicate_username_or_email_rejected(self):
        self.assertEqual(self._create(NEW[0], NEW[1], NEW[2]).status_code, 201)
        self.assertEqual(self._create(NEW[0], "other@example.com", NEW[2]).status_code, 409)
        self.assertEqual(self._create("carol", NEW[1], NEW[2]).status_code, 409)

    def test_new_user_sets_up_mfa_at_first_login(self):
        self._create(*NEW)
        self.client.post("/api/auth/logout")
        self.client.cookies.clear()

        response = _post(self.client, "/api/auth/login", {"username": NEW[0], "password": NEW[2]})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["setup_required"])
        self.assertIn("<svg", data["qr_svg"])
        self.assertNotIn("auth_token", response.cookies)

        response = _post(self.client, "/api/auth/mfa/verify", {"code": pyotp.TOTP(data["secret"]).now()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)

        # From now on the same user is asked for a code, not for setup
        self.client.post("/api/auth/logout")
        self.client.cookies.clear()
        response = _post(self.client, "/api/auth/login", {"username": NEW[0], "password": NEW[2]})
        self.assertFalse(response.json()["setup_required"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
