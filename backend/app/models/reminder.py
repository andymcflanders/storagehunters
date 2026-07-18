"""Reminder model for item and container alerts."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ReminderType(str, Enum):
    """Types of reminders."""

    CHECK_ITEM = "check_item"  # Reminder to check on an item
    EXPIRATION = "expiration"  # Item expiration date
    MAINTENANCE = "maintenance"  # Maintenance reminder
    RESTOCK = "restock"  # Restock reminder
    CUSTOM = "custom"  # Custom reminder


class Reminder(Base):
    """Reminder/alert for items and containers."""

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=True
    )
    container_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("containers.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_type: Mapped[ReminderType] = mapped_column(
        String(32), default=ReminderType.CUSTOM
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_days: Mapped[int | None] = mapped_column(nullable=True)  # Days between recurrences
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Set once the reminder.due / reminder.overdue webhook events have fired,
    # so the periodic scan emits each at most once per reminder occurrence.
    due_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    overdue_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", backref="reminders"
    )
    item: Mapped["Item | None"] = relationship(  # type: ignore[name-defined]
        "Item", backref="reminders"
    )
    container: Mapped["Container | None"] = relationship(  # type: ignore[name-defined]
        "Container", backref="reminders"
    )
