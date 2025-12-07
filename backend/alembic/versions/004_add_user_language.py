"""Add language field to users table

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the language enum type
    language_enum = sa.Enum("en", "no", name="language_enum", create_type=False)
    language_enum.create(op.get_bind(), checkfirst=True)

    # Add the language column with default 'en'
    op.add_column(
        "users",
        sa.Column(
            "language",
            language_enum,
            nullable=False,
            server_default="en",
        ),
    )


def downgrade() -> None:
    # Remove the language column
    op.drop_column("users", "language")

    # Drop the enum type
    sa.Enum(name="language_enum").drop(op.get_bind(), checkfirst=True)
