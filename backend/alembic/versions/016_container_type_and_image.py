"""Add container_type and image_filepath columns to containers.

Wires up two long-documented but unimplemented features: typed
containers (box / drawer / shelf / ...) and a single hero image per
container. Both are nullable so existing rows are unaffected and the
fields can be left blank.

Revision ID: 016
Revises: 015
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa


revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Free-form string rather than a Postgres enum: the set of valid
    # values lives in the Pydantic schema and the frontend translation
    # keys, so adding "shed" or "rack" later is a code change, not a
    # migration. Length matches the longest current value with headroom.
    op.add_column(
        "containers",
        sa.Column("container_type", sa.String(length=32), nullable=True),
    )
    # Relative path under the upload_dir, same convention as
    # item_images.filepath.
    op.add_column(
        "containers",
        sa.Column("image_filepath", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("containers", "image_filepath")
    op.drop_column("containers", "container_type")
