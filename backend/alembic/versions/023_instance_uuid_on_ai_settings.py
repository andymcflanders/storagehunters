"""Add instance_uuid to ai_settings.

The Home Assistant integration uses the StorageHub host URL as its
config-entry unique_id today, so reconfiguring (e.g. from
`http://storagehub.local` to `https://storagehub.example.com`) forks
a new HA entry and orphans the old entities. A stable instance UUID
exposed at /api/ha/status lets HA detect "same instance, new URL"
and migrate cleanly.

Reuses the existing `ai_settings` singleton row rather than
introducing a one-row `instance` table — no new model surface, same
persistence guarantees. The UUID is only rotated when the database
itself is wiped.

Revision ID: 023
Revises: 022
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # gen_random_uuid() needs pgcrypto in older Postgres builds; on
    # Postgres 13+ it's available out of the box. We lean on it for
    # the per-row default so existing rows get a stable UUID without
    # an explicit UPDATE.
    op.add_column(
        "ai_settings",
        sa.Column(
            "instance_uuid",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    # Drop the server default — we want the value frozen at insert,
    # not regenerated if someone resets the column. The Python side
    # supplies its own default for new rows.
    op.alter_column("ai_settings", "instance_uuid", server_default=None)


def downgrade() -> None:
    op.drop_column("ai_settings", "instance_uuid")
