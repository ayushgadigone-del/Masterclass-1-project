"""
auth_service.py — password hashing and JWT token operations for reviewer auth.

Uses:
  - hashlib.pbkdf2_hmac for password hashing (no bcrypt dependency)
  - python-jose for JWT signing (already a dependency)
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone, timedelta

from jose import JWTError, jwt

from app.config import settings

# ── Constants ─────────────────────────────────────────────────────────────────

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


# ── Password hashing (PBKDF2-HMAC-SHA256, no external lib needed) ─────────────

_ITERATIONS = 260_000
_HASH_NAME = "sha256"


def hash_password(plain: str) -> str:
    """Return a salted PBKDF2 hash in the format 'salt$hash' (hex-encoded)."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        _HASH_NAME, plain.encode(), salt.encode(), _ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def verify_password(plain: str, stored: str) -> bool:
    """Constant-time comparison against a stored 'salt$hash' string."""
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        _HASH_NAME, plain.encode(), salt.encode(), _ITERATIONS
    ).hex()
    return hmac.compare_digest(candidate, digest)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(reviewer_id: str, username: str, role: str) -> tuple[str, int]:
    """
    Return (jwt_token_string, expires_in_seconds).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": reviewer_id,
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "reviewer_access",
    }
    token = jwt.encode(payload, settings.settlement_secret_key, algorithm=ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a reviewer JWT.

    Returns the payload dict on success.
    Raises jose.JWTError on invalid / expired token.
    """
    payload = jwt.decode(
        token,
        settings.settlement_secret_key,
        algorithms=[ALGORITHM],
    )
    if payload.get("type") != "reviewer_access":
        raise JWTError("Token type mismatch")
    return payload
