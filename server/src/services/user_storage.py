"""User authentication and storage - SQLite based."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

logger = logging.getLogger(__name__)


class UserStorage:
    """Store users and manage authentication in SQLite."""

    def __init__(self, db_path: str = "users.db"):
        """Initialize user storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self.hasher = PasswordHasher()
        self._init_db()
        logger.info(f"[USER_STORAGE] Initialized at {self.db_path}")

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Migrate older databases that predate TOTP support
            existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
            if "totp_secret" not in existing_cols:
                conn.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT")
            if "totp_enabled" not in existing_cols:
                conn.execute("ALTER TABLE users ADD COLUMN totp_enabled INTEGER DEFAULT 0")

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_username
                ON users(username)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_email
                ON users(email)
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_token
                ON sessions(session_token)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions
                ON sessions(user_id, expires_at)
            """)

            conn.commit()

    def create_user(self, username: str, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create a new user.

        Args:
            username: Username
            email: Email address
            password: Plain text password

        Returns:
            User dict or None if failed
        """
        if not username or not email or not password:
            logger.warning("[USER] Invalid user data provided")
            return None

        if len(username) < 3 or len(password) < 6:
            logger.warning("[USER] Username must be 3+ chars, password 6+ chars")
            return None

        try:
            password_hash = self.hasher.hash(password)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                """, (username, email, password_hash))

                user_id = cursor.lastrowid
                conn.commit()

            logger.info(f"[USER] Created new user: {username}")
            return {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                logger.warning(f"[USER] Username already exists: {username}")
            elif "email" in str(e):
                logger.warning(f"[USER] Email already exists: {email}")
            return None
        except Exception as e:
            logger.error(f"[USER] Failed to create user: {e}")
            return None

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User dict if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                user = conn.execute("""
                    SELECT id, username, email, password_hash, is_active, created_at
                    FROM users
                    WHERE username = ?
                """, (username,)).fetchone()

                if not user:
                    logger.debug(f"[USER] User not found: {username}")
                    return None

                if not user["is_active"]:
                    logger.warning(f"[USER] Account disabled: {username}")
                    return None

                try:
                    self.hasher.verify(user["password_hash"], password)
                    # Update last_login
                    conn.execute("""
                        UPDATE users SET last_login = ? WHERE id = ?
                    """, (datetime.now().isoformat(), user["id"]))
                    conn.commit()

                    logger.info(f"[USER] Authenticated: {username}")
                    return {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user["email"],
                        "created_at": user["created_at"]
                    }
                except (VerifyMismatchError, VerificationError):
                    logger.warning(f"[USER] Invalid password: {username}")
                    return None
        except Exception as e:
            logger.error(f"[USER] Authentication failed: {e}")
            return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User dict or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                user = conn.execute("""
                    SELECT id, username, email, created_at, is_active
                    FROM users
                    WHERE id = ?
                """, (user_id,)).fetchone()

                if user:
                    return dict(user)
                return None
        except Exception as e:
            logger.error(f"[USER] Failed to get user: {e}")
            return None

    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT 1 FROM users WHERE username = ?
                """, (username,)).fetchone()
                return result is not None
        except Exception:
            return False

    def count_users(self) -> int:
        """Return number of users in the database."""
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def list_users(self) -> list:
        """Return all users without secrets or password hashes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT id, username, email, created_at, last_login, is_active, totp_enabled
                FROM users ORDER BY id
            """).fetchall()
            return [dict(row) for row in rows]

    def get_mfa_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return TOTP secret and enabled flag for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT id, username, email, totp_secret, totp_enabled
                FROM users WHERE id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def set_totp_secret(self, user_id: int, secret: str) -> None:
        """Store a (not yet confirmed) TOTP secret for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE users SET totp_secret = ?, totp_enabled = 0 WHERE id = ?
            """, (secret, user_id))
            conn.commit()

    def enable_totp(self, user_id: int) -> None:
        """Mark TOTP as confirmed for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET totp_enabled = 1 WHERE id = ?", (user_id,))
            conn.commit()

    def create_session(self, user_id: int, token_hash: str, ip: str, user_agent: str, expires_at: datetime) -> None:
        """Persist a session. Only the hash of the cookie token is stored."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (user_id, session_token, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, token_hash, ip, user_agent, expires_at.isoformat()))
            conn.commit()

    def get_session_user(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Return the user owning a valid (unexpired, active) session, else None."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT u.id, u.username, u.email, u.is_active, s.expires_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.session_token = ?
            """, (token_hash,)).fetchone()
            if not row or not row["is_active"]:
                return None
            if row["expires_at"] <= datetime.now().isoformat():
                return None
            return {"id": row["id"], "username": row["username"], "email": row["email"]}

    def delete_session(self, token_hash: str) -> None:
        """Remove a session by token hash."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE session_token = ?", (token_hash,))
            conn.commit()

    def purge_expired_sessions(self) -> None:
        """Delete sessions past their expiry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (datetime.now().isoformat(),))
            conn.commit()


# Global instance
_user_storage = None


def get_user_storage(db_path: str = "users.db") -> UserStorage:
    """Get or create global user storage instance."""
    global _user_storage
    if _user_storage is None:
        _user_storage = UserStorage(db_path)
    return _user_storage
