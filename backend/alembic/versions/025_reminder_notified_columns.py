"""Add due/overdue notification tracking to reminders.

Lets the periodic reminder scan emit reminder.due / reminder.overdue
webhook events at most once per reminder occurrence.

Revision ID: 025
Revises: 024
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reminders",
        sa.Column("due_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reminders",
        sa.Column("overdue_notified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reminders", "overdue_notified_at")
    op.drop_column("reminders", "due_notified_at")
