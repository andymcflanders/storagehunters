"""Backup configuration and history models."""

import enum
import uuid
from datetime import datetime, time
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class BackupProviderType(str, enum.Enum):
    """Storage provider types for backups."""

    LOCAL = "local"
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"


class BackupStatus(str, enum.Enum):
    """Status of a backup operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleFrequency(str, enum.Enum):
    """Frequency for scheduled backups."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class BackupConfig(Base):
    """Configuration for backup storage and settings."""

    __tablename__ = "backup_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Storage provider configuration
    provider_type: Mapped[BackupProviderType] = mapped_column(
        Enum(
            BackupProviderType,
            name="backup_provider_type_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    provider_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Backup options
    include_images: Mapped[bool] = mapped_column(Boolean, default=False)
    encryption_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    compression_level: Mapped[int] = mapped_column(Integer, default=6)

    # Retention policy
    retention_count: Mapped[int] = mapped_column(Integer, default=10)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    schedules: Mapped[list["BackupSchedule"]] = relationship(
        "BackupSchedule", back_populates="config", cascade="all, delete-orphan"
    )
    history: Mapped[list["BackupHistory"]] = relationship(
        "BackupHistory", back_populates="config", cascade="all, delete-orphan"
    )


class BackupSchedule(Base):
    """Schedule configuration for automated backups."""

    __tablename__ = "backup_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backup_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Schedule settings
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[ScheduleFrequency] = mapped_column(
        Enum(
            ScheduleFrequency,
            name="schedule_frequency_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    time_of_day: Mapped[time] = mapped_column(Time, nullable=False)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-6
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-28

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    config: Mapped["BackupConfig"] = relationship(
        "BackupConfig", back_populates="schedules"
    )


class BackupHistory(Base):
    """History of backup operations."""

    __tablename__ = "backup_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backup_configs.id", ondelete="SET NULL"),
        nullable=True,
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backup_schedules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Backup details
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Backup options used
    include_images: Mapped[bool] = mapped_column(Boolean, default=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    status: Mapped[BackupStatus] = mapped_column(
        Enum(
            BackupStatus,
            name="backup_status_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=BackupStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progress tracking
    progress_phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)

    # Statistics
    statistics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Who triggered it
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    config: Mapped["BackupConfig | None"] = relationship(
        "BackupConfig", back_populates="history"
    )
    schedule: Mapped["BackupSchedule | None"] = relationship("BackupSchedule")
    triggered_by: Mapped["User | None"] = relationship("User")  # type: ignore[name-defined]
