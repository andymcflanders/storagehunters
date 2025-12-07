"""Add file connection type to printer enum.

Revision ID: 005
Revises: 004
Create Date: 2025-12-05

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add 'file' value to connection_type_enum
    op.execute("ALTER TYPE connection_type_enum ADD VALUE IF NOT EXISTS 'file'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type, which is complex and risky
    pass
