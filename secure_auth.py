import hashlib
import secrets
import time
import sqlite3
from typing import Optional, Tuple
from functools import wraps
import jwt
from datetime import datetime, timedelta

class SecureAuth:
    """Secure authentication system with password hashing and session management"""

    def __init__(self, db_path: str = "users.db", secret_key: str = None):
        self.db_path = db_path
        self.secret_key = secret_key or secrets.token_hex(32)
        self.max_login_attempts = 3
        self.lockout_duration = 300  # 5 minutes
        self.session_timeout = 3600  # 1 hour
        self.init_database()

    def init_database(self):
        """Initialize secure user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS secure_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP NULL,
                last_login TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES secure_users (id)
            )
        ''')

        conn.commit()
        conn.close()

    def hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return password_hash.hex(), salt

    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
        return computed_hash.hex() == password_hash

    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> bool:
        """Create a new user with secure password hashing"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        password_hash, salt = self.hash_password(password)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO secure_users (username, email, password_hash, salt, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, role))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            return False  # User already exists

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user with rate limiting and lockout protection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, username, email, password_hash, salt, role, failed_attempts,
                   locked_until, is_active
            FROM secure_users
            WHERE username = ? OR email = ?
        ''', (username, username))

        user = cursor.fetchone()

        if not user or not user[8]:  # User doesn't exist or is inactive
            return None

        user_id, username, email, password_hash, salt, role, failed_attempts, locked_until, is_active = user

        # Check if account is locked
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
            return None

        # Verify password
        if self.verify_password(password, password_hash, salt):
            # Reset failed attempts on successful login
            cursor.execute('''
                UPDATE secure_users
                SET failed_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()

            return {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role
            }
        else:
            # Increment failed attempts
            new_failed_attempts = failed_attempts + 1
            locked_until = None

            if new_failed_attempts >= self.max_login_attempts:
                locked_until = (datetime.now() + timedelta(seconds=self.lockout_duration)).isoformat()

            cursor.execute('''
                UPDATE secure_users
                SET failed_attempts = ?, locked_until = ?
                WHERE id = ?
            ''', (new_failed_attempts, locked_until, user_id))

            conn.commit()
            conn.close()
            return None

    def create_session(self, user_id: int) -> str:
        """Create a secure session token"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=self.session_timeout)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at.isoformat()))

        conn.commit()
        conn.close()

        return session_token

    def validate_session(self, session_token: str) -> Optional[dict]:
        """Validate session token and return user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT u.id, u.username, u.email, u.role, s.expires_at
            FROM user_sessions s
            JOIN secure_users u ON s.user_id = u.id
            WHERE s.session_token = ? AND u.is_active = 1
        ''', (session_token,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        user_id, username, email, role, expires_at = result

        # Check if session is expired
        if datetime.fromisoformat(expires_at) < datetime.now():
            self.invalidate_session(session_token)
            return None

        return {
            'id': user_id,
            'username': username,
            'email': email,
            'role': role
        }

    def invalidate_session(self, session_token: str):
        """Invalidate a session token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))

        conn.commit()
        conn.close()

    def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM user_sessions WHERE expires_at < ?',
                      (datetime.now().isoformat(),))

        conn.commit()
        conn.close()

# Initialize authentication system
auth_system = SecureAuth()

def require_auth(role: str = None):
    """Decorator to require authentication for routes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is a placeholder - implement based on your web framework
            # For Gradio, you'll need to implement session checking differently
            pass
        return wrapper
    return decorator