"""Add triage fields to items.

Phase 4 ("Declutter" / Tinder for items): users review items one at
a time and pick Love / Undecided / Hate. Decisions are shared across
the household. Cooldowns:
  - Love     → triage_show_after = now + 12 months
  - Undecided→ triage_show_after = now + 3 months
  - Hate     → no cooldown; item moves to the discard list and is
              excluded from /declutter until the user undoes or
              acts on it (delete / mark donated).

Stored as text (not a Postgres enum) so adding e.g. "later" or
"gift" later is a one-line change with no migration.

Revision ID: 021
Revises: 020
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa


revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column("triage_decision", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "items",
        sa.Column("triage_decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "items",
        sa.Column("triage_show_after", sa.DateTime(timezone=True), nullable=True),
    )

    # Partial index over the discard pile (tiny subset of items, but
    # hit every time the user opens /declutter/discard).
    op.create_index(
        "ix_items_triage_discard",
        "items",
        ["triage_decision"],
        postgresql_where=sa.text("triage_decision = 'hate'"),
    )


def downgrade() -> None:
    op.drop_index("ix_items_triage_discard", table_name="items")
    op.drop_column("items", "triage_show_after")
    op.drop_column("items", "triage_decided_at")
    op.drop_column("items", "triage_decision")
