"""Switch AI translations to JSONB + add AISettings.supported_languages.

Replaces the explicit per-language columns on items
(ai_name, ai_name_no, ai_description, ai_description_no) with two
JSONB columns (ai_names, ai_descriptions) keyed by ISO language code.
Existing values are backfilled into the JSONB columns before the old
columns are dropped.

Adds AISettings.supported_languages and AISettings.default_language so
the OpenAI prompt and admin UI can be driven by data instead of
hardcoded "en + no" assumptions.

Revision ID: 015
Revises: 014
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- items: add JSONB columns + backfill + drop old columns ----
    op.add_column(
        "items",
        sa.Column("ai_names", JSONB, nullable=False, server_default="{}"),
    )
    op.add_column(
        "items",
        sa.Column("ai_descriptions", JSONB, nullable=False, server_default="{}"),
    )

    # Backfill from the four old columns into the new JSONB columns.
    # jsonb_strip_nulls drops keys whose value is JSON null, so items that
    # only had English get {"en": "..."} rather than {"en": "...", "no": null}.
    op.execute(
        """
        UPDATE items SET ai_names = jsonb_strip_nulls(jsonb_build_object(
            'en', ai_name,
            'no', ai_name_no
        ))
        WHERE ai_name IS NOT NULL OR ai_name_no IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE items SET ai_descriptions = jsonb_strip_nulls(jsonb_build_object(
            'en', ai_description,
            'no', ai_description_no
        ))
        WHERE ai_description IS NOT NULL OR ai_description_no IS NOT NULL
        """
    )

    op.drop_column("items", "ai_name")
    op.drop_column("items", "ai_name_no")
    op.drop_column("items", "ai_description")
    op.drop_column("items", "ai_description_no")

    # ---- ai_settings: add supported_languages + default_language ----
    op.add_column(
        "ai_settings",
        sa.Column(
            "supported_languages",
            ARRAY(sa.String(length=10)),
            nullable=False,
            server_default="{en,no}",
        ),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "default_language",
            sa.String(length=10),
            nullable=False,
            server_default="en",
        ),
    )


def downgrade() -> None:
    # ---- ai_settings ----
    op.drop_column("ai_settings", "default_language")
    op.drop_column("ai_settings", "supported_languages")

    # ---- items: re-add old columns + backfill from JSONB + drop new ----
    op.add_column("items", sa.Column("ai_name", sa.String(length=255), nullable=True))
    op.add_column("items", sa.Column("ai_name_no", sa.String(length=255), nullable=True))
    op.add_column("items", sa.Column("ai_description", sa.Text(), nullable=True))
    op.add_column("items", sa.Column("ai_description_no", sa.Text(), nullable=True))

    op.execute("UPDATE items SET ai_name = ai_names ->> 'en'")
    op.execute("UPDATE items SET ai_name_no = ai_names ->> 'no'")
    op.execute("UPDATE items SET ai_description = ai_descriptions ->> 'en'")
    op.execute("UPDATE items SET ai_description_no = ai_descriptions ->> 'no'")

    op.drop_column("items", "ai_descriptions")
    op.drop_column("items", "ai_names")
