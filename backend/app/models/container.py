"""Container model."""

import secrets
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def generate_qr_code() -> str:
    """Generate a unique QR code identifier."""
    return secrets.token_urlsafe(8)


class Container(Base):
    """Container model for storage boxes/bins."""

    __tablename__ = "containers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    parent_container_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("containers.id", ondelete="SET NULL"), nullable=True
    )
    qr_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, default=generate_qr_code
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional category — values come from the frontend's translation
    # keys (containers.types.box / drawer / shelf / etc.). Free-form so
    # adding a new type is a code change, not a migration.
    container_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Relative path under the upload_dir for the container's hero image.
    image_filepath: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    location: Mapped["Location"] = relationship(  # type: ignore[name-defined]
        "Location", back_populates="containers"
    )
    parent_container: Mapped["Container | None"] = relationship(
        "Container", remote_side=[id], back_populates="child_containers"
    )
    child_containers: Mapped[list["Container"]] = relationship(
        "Container", back_populates="parent_container"
    )
    items: Mapped[list["Item"]] = relationship(  # type: ignore[name-defined]
        "Item", back_populates="container", cascade="all, delete-orphan"
    )
