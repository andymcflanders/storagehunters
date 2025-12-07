"""Add SSL configuration table.

Revision ID: 006
Revises: 005
Create Date: 2025-12-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create SSL config table with string column for mode
    op.create_table(
        "ssl_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mode", sa.String(50), nullable=False, server_default="disabled"),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("certificate_valid", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("certificate_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_renewal_attempt", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("auto_renew", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Insert default config row
    op.execute(
        """
        INSERT INTO ssl_config (id, mode, certificate_valid, auto_renew)
        VALUES (gen_random_uuid(), 'disabled', false, true)
        """
    )


def downgrade() -> None:
    op.drop_table("ssl_config")
