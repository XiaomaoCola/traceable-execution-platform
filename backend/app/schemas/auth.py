"""Authentication schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """JWT access token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: int  # User ID


class LoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str
