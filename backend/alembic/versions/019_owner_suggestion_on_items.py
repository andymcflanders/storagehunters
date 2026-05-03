"""Add AI owner suggestion fields to items.

Phase 2 of profile users: when the vision classifier processes an item,
it picks the most likely owner from the household's non-admin users
(matching size + motif against age + gender) and stores both the
candidate and a one-sentence reason. The item detail page surfaces
this as a banner the user can apply or dismiss — owner_id is never
auto-set.

Kept separate from owner_id so the suggestion remains visible even
after a manual override, and so the banner only fires while
owner_id IS NULL.

Revision ID: 019
Revises: 018
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column(
            "suggested_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "items",
        sa.Column("owner_suggestion_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "owner_suggestion_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_settings", "owner_suggestion_enabled")
    op.drop_column("items", "owner_suggestion_reason")
    op.drop_column("items", "suggested_owner_id")
