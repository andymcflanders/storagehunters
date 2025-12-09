"""API Key model for external integrations like Home Assistant."""

import enum
import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class APIKeyScope(str, enum.Enum):
    """API key permission scopes."""

    READ = "read"  # Read-only access to data
    WRITE = "write"  # Create/update items, containers, etc.
    SEARCH = "search"  # Search functionality
    WEBHOOKS = "webhooks"  # Manage webhooks
    ADMIN = "admin"  # Full administrative access


class APIKey(Base):
    """API Key for external service authentication."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # First 8 chars for identification
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")  # type: ignore[name-defined]

    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key."""
        return f"shub_{secrets.token_urlsafe(32)}"

    @staticmethod
    def get_prefix(key: str) -> str:
        """Get the prefix from a key for identification."""
        return key[:12]

    def has_scope(self, scope: APIKeyScope | str) -> bool:
        """Check if this API key has the specified scope."""
        scope_value = scope.value if isinstance(scope, APIKeyScope) else scope
        return scope_value in self.scopes or APIKeyScope.ADMIN.value in self.scopes
