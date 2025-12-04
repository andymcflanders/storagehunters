"""Share link model for public sharing of containers."""

import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def generate_share_token() -> str:
    """Generate a unique share token."""
    return secrets.token_urlsafe(16)


class ShareLink(Base):
    """Share link for public access to containers."""

    __tablename__ = "share_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("containers.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, default=generate_share_token
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_item_view: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    view_count: Mapped[int] = mapped_column(default=0)

    # Relationships
    container: Mapped["Container"] = relationship(  # type: ignore[name-defined]
        "Container", backref="share_links"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", backref="share_links"
    )
