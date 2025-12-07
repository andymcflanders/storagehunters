"""Add Norwegian AI fields to items table.

Revision ID: 009
Revises: 008
Create Date: 2025-12-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Norwegian AI fields to items table
    op.add_column("items", sa.Column("ai_name_no", sa.String(255), nullable=True))
    op.add_column("items", sa.Column("ai_description_no", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("items", "ai_description_no")
    op.drop_column("items", "ai_name_no")
