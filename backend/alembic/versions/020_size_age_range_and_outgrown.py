"""Add size age range + outgrown dismissal to items.

Phase 3 of profile users: surfaces items the household has aged out of.
The classifier (or admin backfill) annotates each age-mapped item with
[size_age_min_months, size_age_max_months]; the /outgrown view queries
items where the owner's age in months has crossed size_age_max_months.

Stored in MONTHS, not years, because the 0-4 age window covers ~20
distinct kid sizes in 6-month increments — years would be too coarse
to surface "Sverre outgrew size 92 today" until 6+ months too late.

outgrown_dismissed_at lets the user hide an item from /outgrown
without changing its size or owner — for the "yes, this is outgrown,
but I'm keeping it" case (sentimental, future grandchildren, etc.).

Revision ID: 020
Revises: 019
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa


revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column("size_age_min_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "items",
        sa.Column("size_age_max_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "items",
        sa.Column("outgrown_dismissed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("items", "outgrown_dismissed_at")
    op.drop_column("items", "size_age_max_months")
    op.drop_column("items", "size_age_min_months")
