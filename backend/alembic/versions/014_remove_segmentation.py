"""Remove segmentation feature (FastSAM/Replicate).

Drops the columns and table that were only used by the multi-item
segmentation pipeline:
  - item_images.is_segmented
  - items.source_upload_id (FK to pending_uploads)
  - pending_uploads table and its indexes

The items.needs_review column and its index are kept — the field is
still surfaced in the godview filter, Home Assistant stats, and item
schemas as a general "needs review" flag, even though no code path
currently sets it.

Revision ID: 014
Revises: 013
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop is_segmented from item_images
    op.drop_column("item_images", "is_segmented")

    # Drop source_upload_id FK column from items (must come before dropping pending_uploads)
    op.drop_column("items", "source_upload_id")

    # Drop pending_uploads table and its indexes
    op.drop_index("ix_pending_uploads_uploaded_by", table_name="pending_uploads")
    op.drop_index("ix_pending_uploads_status", table_name="pending_uploads")
    op.drop_table("pending_uploads")


def downgrade() -> None:
    # Recreate pending_uploads table
    op.create_table(
        "pending_uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "container_id",
            UUID(as_uuid=True),
            sa.ForeignKey("containers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("temp_filepath", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("multi_item_mode", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("items_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pending_uploads_status", "pending_uploads", ["status"])
    op.create_index("ix_pending_uploads_uploaded_by", "pending_uploads", ["uploaded_by"])

    # Restore source_upload_id FK column on items
    op.add_column(
        "items",
        sa.Column(
            "source_upload_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pending_uploads.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Restore is_segmented on item_images
    op.add_column(
        "item_images",
        sa.Column("is_segmented", sa.Boolean(), nullable=False, server_default="false"),
    )
