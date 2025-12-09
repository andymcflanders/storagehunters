"""User and Session models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


class Language(str, enum.Enum):
    """Supported languages."""

    EN = "en"
    NO = "no"


class User(Base):
    """User model for household members."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_password: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER,
        nullable=False,
    )
    language: Mapped[Language] = mapped_column(
        Enum(Language, name="language_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        default=Language.EN,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    items: Mapped[list["Item"]] = relationship(  # type: ignore[name-defined]
        "Item", back_populates="owner", foreign_keys="Item.owner_id"
    )
    pending_uploads: Mapped[list["PendingUpload"]] = relationship(  # type: ignore[name-defined]
        "PendingUpload", back_populates="uploader"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(  # type: ignore[name-defined]
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    webhooks: Mapped[list["Webhook"]] = relationship(  # type: ignore[name-defined]
        "Webhook", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    """Session model for user authentication."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
