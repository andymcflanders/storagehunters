"""Container schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# Allowed values mirror the frontend translation keys
# (containers.types.{box,drawer,...}). Add new values here AND in the
# locale files when introducing a new container type.
ContainerType = Literal[
    "box",
    "drawer",
    "shelf",
    "cabinet",
    "closet",
    "bin",
    "basket",
    "other",
]


class ContainerBase(BaseModel):
    """Base container schema."""

    name: str = Field(..., min_length=1, max_length=255)
    location_id: UUID
    parent_container_id: UUID | None = None
    notes: str | None = None
    container_type: ContainerType | None = None


class ContainerCreate(ContainerBase):
    """Schema for creating a container."""

    pass


class ContainerUpdate(BaseModel):
    """Schema for updating a container."""

    name: str | None = Field(None, min_length=1, max_length=255)
    location_id: UUID | None = None
    parent_container_id: UUID | None = None
    notes: str | None = None
    container_type: ContainerType | None = None


class ContainerResponse(BaseModel):
    """Schema for container response."""

    id: UUID
    name: str
    location_id: UUID
    parent_container_id: UUID | None
    qr_code: str
    notes: str | None
    container_type: ContainerType | None = None
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemSummary(BaseModel):
    """Brief item info for container responses."""

    id: UUID
    name: str
    thumbnail_url: str | None = None

    model_config = {"from_attributes": True}


class ContainerWithItems(ContainerResponse):
    """Container response with items and path included."""

    items: list[ItemSummary] = []
    child_containers: list["ContainerResponse"] = []
    path: list[dict[str, str]] = []  # [{"id": "...", "name": "...", "type": "location|container"}]
