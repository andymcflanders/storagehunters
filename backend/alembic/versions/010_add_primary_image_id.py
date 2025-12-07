"""Add primary_image_id to items.

Revision ID: 010
Revises: 009
Create Date: 2025-12-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column("primary_image_id", UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("items", "primary_image_id")
