#!/usr/bin/env python3
"""Tests for authentication system."""

import sys
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.user_storage import UserStorage


class TestUserStorage(unittest.TestCase):
    """Test user storage and authentication."""

    def setUp(self):
        """Create temporary database for testing."""
        self.db_file = NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.db_file.name
        self.db_file.close()
        self.storage = UserStorage(self.db_path)

    def tearDown(self):
        """Clean up."""
        import os
        import gc
        # Force garbage collection to close DB connection
        gc.collect()
        import time
        time.sleep(0.1)
        if Path(self.db_path).exists():
            try:
                os.unlink(self.db_path)
            except Exception:
                pass

    def test_create_user_success(self):
        """Test successful user creation."""
        user = self.storage.create_user("testuser", "test@example.com", "password123")

        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertIn("id", user)
        self.assertIn("created_at", user)

    def test_create_user_short_username(self):
        """Test user creation fails with short username."""
        user = self.storage.create_user("ab", "test@example.com", "password123")
        self.assertIsNone(user)

    def test_create_user_short_password(self):
        """Test user creation fails with short password."""
        user = self.storage.create_user("testuser", "test@example.com", "pass")
        self.assertIsNone(user)

    def test_create_user_duplicate_username(self):
        """Test duplicate username is rejected."""
        user1 = self.storage.create_user("testuser", "test1@example.com", "password123")
        self.assertIsNotNone(user1)

        user2 = self.storage.create_user("testuser", "test2@example.com", "password123")
        self.assertIsNone(user2)

    def test_create_user_duplicate_email(self):
        """Test duplicate email is rejected."""
        user1 = self.storage.create_user("user1", "test@example.com", "password123")
        self.assertIsNotNone(user1)

        user2 = self.storage.create_user("user2", "test@example.com", "password123")
        self.assertIsNone(user2)

    def test_authenticate_success(self):
        """Test successful authentication."""
        self.storage.create_user("testuser", "test@example.com", "password123")

        user = self.storage.authenticate("testuser", "password123")

        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")

    def test_authenticate_wrong_password(self):
        """Test authentication fails with wrong password."""
        self.storage.create_user("testuser", "test@example.com", "password123")

        user = self.storage.authenticate("testuser", "wrongpassword")

        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        """Test authentication fails for nonexistent user."""
        user = self.storage.authenticate("nonexistent", "password123")
        self.assertIsNone(user)

    def test_get_user(self):
        """Test getting user by ID."""
        created = self.storage.create_user("testuser", "test@example.com", "password123")

        user = self.storage.get_user(created["id"])

        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")

    def test_get_nonexistent_user(self):
        """Test getting nonexistent user returns None."""
        user = self.storage.get_user(99999)
        self.assertIsNone(user)

    def test_user_exists(self):
        """Test user existence check."""
        self.storage.create_user("testuser", "test@example.com", "password123")

        self.assertTrue(self.storage.user_exists("testuser"))
        self.assertFalse(self.storage.user_exists("nonexistent"))

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "mySecurePassword123!"
        self.storage.create_user("testuser", "test@example.com", password)

        # Get the hash from database
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                ("testuser",)
            ).fetchone()
            password_hash = row[0]

        # Hash should not be equal to plain password
        self.assertNotEqual(password_hash, password)

        # But authentication should still work
        user = self.storage.authenticate("testuser", password)
        self.assertIsNotNone(user)

    def test_multiple_users(self):
        """Test creating and authenticating multiple users."""
        users_data = [
            ("alice", "alice@example.com", "alice123"),
            ("bob", "bob@example.com", "bob456"),
            ("charlie", "charlie@example.com", "charlie789"),
        ]

        # Create users
        created_users = []
        for username, email, password in users_data:
            user = self.storage.create_user(username, email, password)
            self.assertIsNotNone(user)
            created_users.append(user)

        # Authenticate each user
        for username, email, password in users_data:
            user = self.storage.authenticate(username, password)
            self.assertIsNotNone(user)
            self.assertEqual(user["username"], username)
            self.assertEqual(user["email"], email)


if __name__ == "__main__":
    unittest.main(verbosity=2)
