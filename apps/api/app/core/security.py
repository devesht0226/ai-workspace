"""Security helpers: passwords and JWTs."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(*, subject: str, role: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
        "jti": str(uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(*, subject: str) -> tuple[str, str, datetime]:
    """Return raw token, jti, and expiry."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=settings.refresh_token_ttl_seconds)
    jti = str(uuid4())
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": expires,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, jti, expires


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def hash_token(token: str) -> str:
    """Hash refresh tokens at rest (sha256 via passlib identify-safe digest)."""
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
