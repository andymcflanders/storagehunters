"""SSL configuration model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class SSLMode(str, enum.Enum):
    """SSL mode enumeration."""

    DISABLED = "disabled"
    SELF_SIGNED = "self_signed"
    LETSENCRYPT = "letsencrypt"


class SSLConfig(Base):
    """SSL configuration model - singleton table."""

    __tablename__ = "ssl_config"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mode: Mapped[str] = mapped_column(
        String(50),
        default="disabled",
        nullable=False,
    )
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)  # For Let's Encrypt notifications

    # Certificate status
    certificate_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    certificate_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_renewal_attempt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auto-renewal settings
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
