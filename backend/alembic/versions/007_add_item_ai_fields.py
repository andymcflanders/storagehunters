"""Add AI fields to items table.

Revision ID: 007
Revises: 006
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI fields to items table
    op.add_column("items", sa.Column("ai_name", sa.String(255), nullable=True))
    op.add_column("items", sa.Column("ai_description", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("ai_processed", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("items", "ai_processed")
    op.drop_column("items", "ai_description")
    op.drop_column("items", "ai_name")
