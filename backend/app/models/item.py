"""Item, ItemImage, ItemTag, and RelatedItems models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ConditionEnum(str, enum.Enum):
    """Item condition enumeration."""

    GOOD = "good"
    FAIR = "fair"
    DAMAGED = "damaged"
    NEEDS_REPAIR = "needs_repair"


class SeasonalEnum(str, enum.Enum):
    """Seasonal classification enumeration."""

    NONE = "none"
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    HOLIDAY = "holiday"


class Item(Base):
    """Item model for stored belongings."""

    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("containers.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # AI's guess at the most likely owner, based on item size/motif and
    # the user's age + gender. Surfaced as a suggestion banner on the
    # item detail page; never auto-applied to owner_id. Cleared when
    # the user dismisses or applies the suggestion.
    suggested_owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    owner_suggestion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Age range (in months) implied by the size, populated by the AI
    # classifier or the admin backfill action. Both null when the size
    # is for an adult / not age-mapped — those items don't show up in
    # /outgrown.
    size_age_min_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_age_max_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Set when the user dismisses an item from /outgrown (yes, it's
    # outgrown — but I'm keeping it). NULL means it's eligible to
    # surface again if the data changes.
    outgrown_dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Phase 4 declutter ("Tinder for items"). One shared household
    # decision per item: 'love' | 'undecided' | 'hate' | None.
    # NULL means "never been triaged"; eligible for the next-card pool.
    triage_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    triage_decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # The cooldown stamp set when the user picks love or undecided.
    # While now() < triage_show_after, the item is excluded from the
    # next-card pool. NULL means immediately eligible.
    triage_show_after: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    condition: Mapped[ConditionEnum] = mapped_column(
        Enum(ConditionEnum, name="condition_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        default=ConditionEnum.GOOD
    )
    seasonal: Mapped[SeasonalEnum] = mapped_column(
        Enum(SeasonalEnum, name="seasonal_enum", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        default=SeasonalEnum.NONE
    )
    value_estimate: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # AI-generated names and descriptions, keyed by ISO language code.
    # Example: {"en": "Red sweater", "no": "Rød genser"}.
    # Populated by the OpenAI classifier for each language listed in
    # AISettings.supported_languages. Read via the get_localized helpers.
    ai_names: Mapped[dict[str, str]] = mapped_column(
        JSONB, default=dict, nullable=False, server_default="{}"
    )
    ai_descriptions: Mapped[dict[str, str]] = mapped_column(
        JSONB, default=dict, nullable=False, server_default="{}"
    )
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    primary_image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    container: Mapped["Container"] = relationship(  # type: ignore[name-defined]
        "Container", back_populates="items"
    )
    owner: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="items", foreign_keys=[owner_id]
    )
    suggested_owner: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[suggested_owner_id]
    )
    images: Mapped[list["ItemImage"]] = relationship(
        "ItemImage", back_populates="item", cascade="all, delete-orphan",
        order_by="ItemImage.created_at"  # Order by oldest first
    )
    item_tags: Mapped[list["ItemTag"]] = relationship(
        "ItemTag", back_populates="item", cascade="all, delete-orphan"
    )
    related_items_a: Mapped[list["RelatedItems"]] = relationship(
        "RelatedItems",
        foreign_keys="RelatedItems.item_a_id",
        back_populates="item_a",
        cascade="all, delete-orphan",
    )
    related_items_b: Mapped[list["RelatedItems"]] = relationship(
        "RelatedItems",
        foreign_keys="RelatedItems.item_b_id",
        back_populates="item_b",
        cascade="all, delete-orphan",
    )


class ItemImage(Base):
    """Image attached to an item."""

    __tablename__ = "item_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    ai_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    item: Mapped["Item"] = relationship("Item", back_populates="images")


class ItemTag(Base):
    """Many-to-many relationship between items and tags."""

    __tablename__ = "item_tags"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    item: Mapped["Item"] = relationship("Item", back_populates="item_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="item_tags")  # type: ignore[name-defined]


class RelatedItems(Base):
    """Many-to-many relationship for related items."""

    __tablename__ = "related_items"

    item_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    item_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    relationship_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    item_a: Mapped["Item"] = relationship(
        "Item", foreign_keys=[item_a_id], back_populates="related_items_a"
    )
    item_b: Mapped["Item"] = relationship(
        "Item", foreign_keys=[item_b_id], back_populates="related_items_b"
    )
