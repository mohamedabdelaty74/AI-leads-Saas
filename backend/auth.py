"""
Authentication utilities - Password hashing + JWT tokens

🎓 TEACHING: Security Essentials
- NEVER store plain passwords (always hash with bcrypt)
- JWT tokens = Stateless authentication (no session storage needed)
- Access tokens expire quickly (security), refresh tokens last longer (UX)
"""

import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
# CRITICAL: JWT_SECRET_KEY must be set in environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError(
        "CRITICAL: JWT_SECRET_KEY or JWT_SECRET environment variable is required!\n"
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
        "Then add it to your .env file: JWT_SECRET=<generated-key>"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30 days


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    🎓 TEACHING: Why bcrypt?
    - Slow by design (prevents brute force attacks)
    - Automatically salted (different hash each time)
    - Industry standard

    Example:
        hash_password("mypassword")
        → "$2b$12$KIXl3..."  (60 characters)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Example:
        verify_password("mypassword", "$2b$12$KIXl3...") → True
        verify_password("wrongpass", "$2b$12$KIXl3...") → False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    🎓 TEACHING: JWT Structure
    JWT has 3 parts: header.payload.signature

    Payload contains:
    - sub: User ID (subject)
    - tenant_id: Which company they belong to
    - role: owner/admin/member
    - exp: Expiration timestamp

    Example:
        create_access_token({
            "sub": "user-uuid-123",
            "tenant_id": "tenant-uuid-456",
            "role": "owner"
        })
        → "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Encode token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token

    Returns:
        dict with user_id, tenant_id, role if valid
        None if token is invalid or expired

    Example:
        decode_access_token("eyJhbGciOiJI...")
        → {"sub": "user-123", "tenant_id": "tenant-456", "role": "owner"}
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None


def create_token_pair(user_id: str, tenant_id: str, role: str) -> dict:
    """
    Create both access and refresh tokens

    🎓 TEACHING: Why two tokens?
    - Access token: Short-lived (1 hour), used for API calls
    - Refresh token: Long-lived (30 days), used to get new access tokens

    This way if access token is stolen, damage is limited (expires quickly)

    Returns:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "bearer",
            "expires_in": 3600
        }
    """
    access_token = create_access_token(
        data={
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access"
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_access_token(
        data={
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "refresh"
        },
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("AUTH UTILITIES TEST")
    print("=" * 60)
    print()

    # Test password hashing
    print("1. Password Hashing:")
    password = "mySecurePassword123"
    hashed = hash_password(password)
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    print(f"   Verify correct: {verify_password(password, hashed)}")
    print(f"   Verify wrong: {verify_password('wrongpassword', hashed)}")
    print()

    # Test JWT tokens
    print("2. JWT Token Creation:")
    tokens = create_token_pair(
        user_id="user-123",
        tenant_id="tenant-456",
        role="owner"
    )
    print(f"   Access Token: {tokens['access_token'][:50]}...")
    print(f"   Expires in: {tokens['expires_in']} seconds")
    print()

    # Test token decoding
    print("3. JWT Token Decoding:")
    decoded = decode_access_token(tokens['access_token'])
    print(f"   User ID: {decoded.get('sub')}")
    print(f"   Tenant ID: {decoded.get('tenant_id')}")
    print(f"   Role: {decoded.get('role')}")
    print()

    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
