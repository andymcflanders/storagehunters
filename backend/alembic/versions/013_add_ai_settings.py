"""Add AI settings table for OpenAI configuration.

Revision ID: 013
Revises: 012
Create Date: 2025-12-20

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create AI settings table
    op.create_table(
        "ai_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Vision classification settings
        sa.Column("vision_model", sa.String(100), nullable=False, server_default="gpt-4o"),
        sa.Column("vision_max_tokens", sa.Integer, nullable=False, server_default="500"),
        sa.Column("vision_temperature", sa.Float, nullable=False, server_default="0.3"),
        sa.Column("vision_enabled", sa.Boolean, nullable=False, server_default="true"),
        # Summary generation settings
        sa.Column("summary_model", sa.String(100), nullable=False, server_default="gpt-4o-mini"),
        sa.Column("summary_max_tokens", sa.Integer, nullable=False, server_default="150"),
        sa.Column("summary_temperature", sa.Float, nullable=False, server_default="0.3"),
        sa.Column("summary_enabled", sa.Boolean, nullable=False, server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Insert default config row
    op.execute(
        """
        INSERT INTO ai_settings (
            id,
            vision_model, vision_max_tokens, vision_temperature, vision_enabled,
            summary_model, summary_max_tokens, summary_temperature, summary_enabled
        )
        VALUES (
            gen_random_uuid(),
            'gpt-4o', 500, 0.3, true,
            'gpt-4o-mini', 150, 0.3, true
        )
        """
    )


def downgrade() -> None:
    op.drop_table("ai_settings")
