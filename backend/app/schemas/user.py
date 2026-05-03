"""User and authentication schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


class Language(str, Enum):
    """Supported languages."""

    EN = "en"
    NO = "no"


class UserBase(BaseModel):
    """Base user schema."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    requires_password: bool = False


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str | None = Field(None, min_length=4)
    role: UserRole = UserRole.USER
    language: Language = Language.EN


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    requires_password: bool | None = None
    password: str | None = Field(None, min_length=4)
    role: UserRole | None = None
    language: Language | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    name: str
    email: str | None
    avatar_url: str | None
    requires_password: bool
    role: UserRole
    language: Language
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Schema for login request.

    Provide exactly one of `user_id` or `email`. The household login
    screen uses `user_id` (the user picked their card). The admin login
    flow uses `email` since admins aren't in the card grid.
    """

    user_id: UUID | None = None
    email: str | None = None
    password: str | None = None


class SessionResponse(BaseModel):
    """Schema for session response."""

    token: str
    expires_at: datetime
    user: UserResponse
