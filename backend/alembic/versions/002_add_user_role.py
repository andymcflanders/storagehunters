"""Add user role and is_active fields

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_role_enum type
    user_role_enum = postgresql.ENUM("admin", "user", name="user_role_enum", create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Add role column with default 'user'
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="user",
        ),
    )

    # Add is_active column with default True
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # Make the first user an admin (if any users exist)
    op.execute(
        """
        UPDATE users
        SET role = 'admin'
        WHERE id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)
        """
    )


def downgrade() -> None:
    # Remove columns
    op.drop_column("users", "is_active")
    op.drop_column("users", "role")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS user_role_enum")
