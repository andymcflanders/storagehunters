"""Add network_ipp to printer_type_enum.

The PrinterTypeEnum model enum gained NETWORK_IPP but the Postgres enum
was never altered, so creating an IPP printer failed at the database.

Revision ID: 024
Revises: 023
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safe inside a transaction on PostgreSQL 12+; the new value just
    # can't be used within this same transaction (we don't).
    op.execute("ALTER TYPE printer_type_enum ADD VALUE IF NOT EXISTS 'network_ipp'")


def downgrade() -> None:
    # PostgreSQL cannot remove enum values; leaving the value in place is
    # harmless for older code paths.
    pass
