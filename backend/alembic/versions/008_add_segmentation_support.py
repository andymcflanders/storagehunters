"""Add segmentation support tables and columns.

Revision ID: 008
Revises: 007
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pending_uploads table
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

    # Create index on status for filtering pending uploads
    op.create_index(
        "ix_pending_uploads_status",
        "pending_uploads",
        ["status"],
    )

    # Create index on uploaded_by for user's pending uploads
    op.create_index(
        "ix_pending_uploads_uploaded_by",
        "pending_uploads",
        ["uploaded_by"],
    )

    # Add needs_review column to items table
    op.add_column(
        "items",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Add source_upload_id column to items table (FK to pending_uploads)
    op.add_column(
        "items",
        sa.Column(
            "source_upload_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pending_uploads.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Create index on needs_review for filtering items needing review
    op.create_index(
        "ix_items_needs_review",
        "items",
        ["needs_review"],
    )

    # Add is_segmented column to item_images table
    op.add_column(
        "item_images",
        sa.Column("is_segmented", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # Remove is_segmented from item_images
    op.drop_column("item_images", "is_segmented")

    # Remove index and source_upload_id from items
    op.drop_index("ix_items_needs_review", table_name="items")
    op.drop_column("items", "source_upload_id")
    op.drop_column("items", "needs_review")

    # Drop pending_uploads table and its indexes
    op.drop_index("ix_pending_uploads_uploaded_by", table_name="pending_uploads")
    op.drop_index("ix_pending_uploads_status", table_name="pending_uploads")
    op.drop_table("pending_uploads")
