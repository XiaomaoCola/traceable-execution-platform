"""Security utilities for password hashing and JWT tokens."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from backend.app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# CryptContext 可以看作为「密码策略管理器」。
# schemes=["bcrypt"]的意思是：系统里所有密码，都按 bcrypt 这种方式来算。
# bcrypt放在 list 里的原因是：
# 它支持多算法共存，比如将来改成schemes=["argon2", "bcrypt"]的话，新用户用 argon2加密，但是登录时候自动识别。
# deprecated="auto"的意思是：  “过期的算法”未来仍然可以用。


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    return payload
