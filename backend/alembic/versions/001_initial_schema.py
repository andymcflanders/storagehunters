"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("requires_password", sa.Boolean, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(255), unique=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Create locations table
    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create containers table
    op.create_table(
        "containers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_container_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("containers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("qr_code", sa.String(32), unique=True, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("user_created", sa.Boolean, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create condition enum
    condition_enum = postgresql.ENUM(
        "good", "fair", "damaged", "needs_repair", name="condition_enum"
    )
    condition_enum.create(op.get_bind())

    # Create seasonal enum
    seasonal_enum = postgresql.ENUM(
        "none", "spring", "summer", "fall", "winter", "holiday", name="seasonal_enum"
    )
    seasonal_enum.create(op.get_bind())

    # Create items table
    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "container_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("containers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column(
            "condition",
            condition_enum,
            default="good",
        ),
        sa.Column(
            "seasonal",
            seasonal_enum,
            default="none",
        ),
        sa.Column("value_estimate", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create item_images table
    op.create_table(
        "item_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("filepath", sa.Text, nullable=False),
        sa.Column("ai_tags", postgresql.ARRAY(sa.String), default=[]),
        sa.Column("ai_description", sa.Text, nullable=True),
        sa.Column("ai_processed", sa.Boolean, default=False),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create item_tags junction table
    op.create_table(
        "item_tags",
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # Create related_items junction table
    op.create_table(
        "related_items",
        sa.Column(
            "item_a_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "item_b_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("relationship_type", sa.String(50), nullable=True),
    )

    # Create printer type enum
    printer_type_enum = postgresql.ENUM(
        "zebra_zpl", "brother_ql", "generic_pdf", name="printer_type_enum"
    )
    printer_type_enum.create(op.get_bind())

    # Create connection type enum
    connection_type_enum = postgresql.ENUM("network", "usb", name="connection_type_enum")
    connection_type_enum.create(op.get_bind())

    # Create printers table
    op.create_table(
        "printers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("printer_type", printer_type_enum, nullable=False),
        sa.Column("connection_type", connection_type_enum, nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("label_width_mm", sa.Float, nullable=False),
        sa.Column("label_height_mm", sa.Float, nullable=False),
        sa.Column("is_default", sa.Boolean, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create action enum
    action_enum = postgresql.ENUM(
        "created", "updated", "moved", "deleted", name="action_enum"
    )
    action_enum.create(op.get_bind())

    # Create activity_logs table
    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", action_enum, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_name", sa.String(255), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Create indexes
    op.create_index("ix_items_name", "items", ["name"])
    op.create_index("ix_items_container_id", "items", ["container_id"])
    op.create_index("ix_items_owner_id", "items", ["owner_id"])
    op.create_index("ix_containers_location_id", "containers", ["location_id"])
    op.create_index("ix_containers_qr_code", "containers", ["qr_code"])
    op.create_index("ix_activity_logs_entity_id", "activity_logs", ["entity_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_activity_logs_created_at")
    op.drop_index("ix_activity_logs_entity_id")
    op.drop_index("ix_containers_qr_code")
    op.drop_index("ix_containers_location_id")
    op.drop_index("ix_items_owner_id")
    op.drop_index("ix_items_container_id")
    op.drop_index("ix_items_name")

    # Drop tables
    op.drop_table("activity_logs")
    op.drop_table("printers")
    op.drop_table("related_items")
    op.drop_table("item_tags")
    op.drop_table("item_images")
    op.drop_table("items")
    op.drop_table("tags")
    op.drop_table("containers")
    op.drop_table("locations")
    op.drop_table("sessions")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS action_enum")
    op.execute("DROP TYPE IF EXISTS connection_type_enum")
    op.execute("DROP TYPE IF EXISTS printer_type_enum")
    op.execute("DROP TYPE IF EXISTS seasonal_enum")
    op.execute("DROP TYPE IF EXISTS condition_enum")
