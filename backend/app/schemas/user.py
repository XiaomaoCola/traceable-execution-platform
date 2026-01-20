"""User schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None


class UserResponse(UserBase):
    """Schema for user response (public info)."""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserMe(UserResponse):
    """Schema for current user info."""
    pass
