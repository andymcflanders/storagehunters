"""Persist the OpenAI API key on ai_settings.

The key was env-only before, which made the onboarding wizard
impossible to implement durably — anything the wizard wrote to
os.environ would be lost on container restart. Storing the key on
the singleton ai_settings row lets the wizard and the admin panel
both manage it, and lets it survive deploys without touching .env
on the host.

The env var stays as a fallback so existing deployments keep working
until they explicitly set a value through the UI.

Revision ID: 017
Revises: 016
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa


revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_settings",
        sa.Column("openai_api_key", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ai_settings", "openai_api_key")
