"""Add backup system tables.

Revision ID: 012
Revises: 011
Create Date: 2025-12-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create backup_configs table
    op.create_table(
        "backup_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "provider_type",
            sa.Enum("local", "google_drive", "dropbox", name="backup_provider_type_enum"),
            nullable=False,
        ),
        sa.Column("provider_config", JSON, nullable=False, server_default="{}"),
        sa.Column("include_images", sa.Boolean, default=False, nullable=False),
        sa.Column("encryption_enabled", sa.Boolean, default=False, nullable=False),
        sa.Column("compression_level", sa.Integer, default=6, nullable=False),
        sa.Column("retention_count", sa.Integer, default=10, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_default", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create backup_schedules table
    op.create_table(
        "backup_schedules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "config_id",
            UUID(as_uuid=True),
            sa.ForeignKey("backup_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "frequency",
            sa.Enum("daily", "weekly", "monthly", name="schedule_frequency_enum"),
            nullable=False,
        ),
        sa.Column("time_of_day", sa.Time, nullable=False),
        sa.Column("day_of_week", sa.Integer, nullable=True),
        sa.Column("day_of_month", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_backup_schedules_config_id", "backup_schedules", ["config_id"])

    # Create backup_history table
    op.create_table(
        "backup_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "config_id",
            UUID(as_uuid=True),
            sa.ForeignKey("backup_configs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "schedule_id",
            UUID(as_uuid=True),
            sa.ForeignKey("backup_schedules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text, nullable=True),
        sa.Column("remote_id", sa.String(255), nullable=True),
        sa.Column("remote_path", sa.Text, nullable=True),
        sa.Column("size_bytes", sa.BigInteger, default=0, nullable=False),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("include_images", sa.Boolean, default=False, nullable=False),
        sa.Column("is_encrypted", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "in_progress", "completed", "failed",
                name="backup_status_enum"
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("progress_phase", sa.String(50), nullable=True),
        sa.Column("progress_percentage", sa.Integer, default=0, nullable=False),
        sa.Column("statistics", JSON, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "triggered_by_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_scheduled", sa.Boolean, default=False, nullable=False),
    )
    op.create_index("ix_backup_history_config_id", "backup_history", ["config_id"])
    op.create_index("ix_backup_history_status", "backup_history", ["status"])
    op.create_index("ix_backup_history_created_at", "backup_history", ["created_at"])


def downgrade() -> None:
    op.drop_table("backup_history")
    op.drop_table("backup_schedules")
    op.drop_table("backup_configs")
    op.execute("DROP TYPE IF EXISTS backup_status_enum")
    op.execute("DROP TYPE IF EXISTS schedule_frequency_enum")
    op.execute("DROP TYPE IF EXISTS backup_provider_type_enum")
