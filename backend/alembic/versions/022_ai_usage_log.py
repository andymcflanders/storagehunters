"""Add ai_usage_log table.

One row per OpenAI API call so the admin Usage panel can aggregate
real spend (using the `usage` block returned by OpenAI) instead of
the hardcoded estimates the cost panel previously showed. Kind +
model are denormalised so we can break down by feature and model
without joining to settings.

cost_usd is computed at log time from the active pricing table and
frozen on the row — historical pricing changes don't retroactively
revalue past calls.

Revision ID: 022
Revises: 021
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_usage_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
    )

    # Aggregations are always time-bounded ("today", "last 30d") and
    # often grouped by kind, so a btree on created_at and a separate
    # index on kind cover the dashboard queries cheaply.
    op.create_index("ix_ai_usage_log_created_at", "ai_usage_log", ["created_at"])
    op.create_index("ix_ai_usage_log_kind", "ai_usage_log", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_log_kind", table_name="ai_usage_log")
    op.drop_index("ix_ai_usage_log_created_at", table_name="ai_usage_log")
    op.drop_table("ai_usage_log")
