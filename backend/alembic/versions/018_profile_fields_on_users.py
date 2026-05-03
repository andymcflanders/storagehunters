"""Add profile fields to users.

Introduces a "profile" notion: a household member who exists as an item
owner but never logs in (e.g. small kids whose clothes you track but
who don't use the UI). The login screen filters these rows out of the
card grid; owner pickers continue to show them.

Adds two demographic fields used by Phase 2's AI owner suggestion
(size 98 dinosaur t-shirt → 2-year-old boy, etc.):
  - birthdate: stable across years; the AI prompt computes age at
    request time so we don't need to maintain it.
  - gender: enum (male / female / other), nullable.

Revision ID: 018
Revises: 017
Create Date: 2026-05-03

"""
from alembic import op
import sqlalchemy as sa


revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_profile",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("birthdate", sa.Date(), nullable=True),
    )

    # Postgres enum mirrors the existing user_role_enum / language_enum
    # patterns. Using an enum (vs free-form String) keeps the database
    # honest if someone tries to insert a typo'd gender via raw SQL.
    gender_enum = sa.Enum("male", "female", "other", name="gender_enum")
    gender_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("gender", gender_enum, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "gender")
    sa.Enum(name="gender_enum").drop(op.get_bind(), checkfirst=True)
    op.drop_column("users", "birthdate")
    op.drop_column("users", "is_profile")
