"""Item schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.item import ConditionEnum, SeasonalEnum


class ItemBase(BaseModel):
    """Base item schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    container_id: UUID
    owner_id: UUID | None = None
    size: str | None = Field(None, max_length=50)
    condition: ConditionEnum = ConditionEnum.GOOD
    seasonal: SeasonalEnum = SeasonalEnum.NONE
    value_estimate: Decimal | None = None


class ItemCreate(ItemBase):
    """Schema for creating an item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    container_id: UUID | None = None
    owner_id: UUID | None = None
    size: str | None = Field(None, max_length=50)
    condition: ConditionEnum | None = None
    seasonal: SeasonalEnum | None = None
    value_estimate: Decimal | None = None
    # Set true to clear the AI owner suggestion (banner dismissed or
    # applied). Apply path: send {owner_id: ..., clear_suggestion: true}.
    clear_suggestion: bool = False


class ItemImageResponse(BaseModel):
    """Schema for item image response."""

    id: UUID
    filename: str
    filepath: str
    ai_tags: list[str]
    ai_description: str | None
    ai_processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TagInfo(BaseModel):
    """Brief tag info."""

    id: UUID
    name: str

    model_config = {"from_attributes": True}


class ItemResponse(BaseModel):
    """Schema for item response."""

    id: UUID
    name: str
    description: str | None
    container_id: UUID
    owner_id: UUID | None
    size: str | None
    condition: ConditionEnum
    seasonal: SeasonalEnum
    value_estimate: Decimal | None
    ai_names: dict[str, str] = {}
    ai_descriptions: dict[str, str] = {}
    ai_processed: bool = False
    needs_review: bool = False
    primary_image_id: UUID | None = None
    suggested_owner_id: UUID | None = None
    owner_suggestion_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OwnerInfo(BaseModel):
    """Brief owner info."""

    id: UUID
    name: str
    avatar_url: str | None

    model_config = {"from_attributes": True}


class ContainerPath(BaseModel):
    """Container path element."""

    id: UUID
    name: str
    type: str  # "location" or "container"


class ItemWithDetails(ItemResponse):
    """Item response with full details."""

    images: list[ItemImageResponse] = []
    tags: list[TagInfo] = []
    owner: OwnerInfo | None = None
    suggested_owner: OwnerInfo | None = None
    path: list[ContainerPath] = []
    related_items: list["ItemResponse"] = []
