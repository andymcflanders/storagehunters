"""PendingUpload model for tracking image uploads awaiting segmentation."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class UploadStatus(str, enum.Enum):
    """Status of a pending upload."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PendingUpload(Base):
    """Pending upload awaiting FastSAM segmentation processing."""

    __tablename__ = "pending_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("containers.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    temp_filepath: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UploadStatus.PENDING.value
    )
    multi_item_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    items_created: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    container: Mapped["Container"] = relationship(  # type: ignore[name-defined]
        "Container", back_populates="pending_uploads"
    )
    uploader: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="pending_uploads"
    )
    created_items: Mapped[list["Item"]] = relationship(  # type: ignore[name-defined]
        "Item",
        back_populates="source_upload",
        foreign_keys="Item.source_upload_id",
    )
