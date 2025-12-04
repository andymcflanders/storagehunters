"""Container schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ContainerBase(BaseModel):
    """Base container schema."""

    name: str = Field(..., min_length=1, max_length=255)
    location_id: UUID
    parent_container_id: UUID | None = None
    notes: str | None = None


class ContainerCreate(ContainerBase):
    """Schema for creating a container."""

    pass


class ContainerUpdate(BaseModel):
    """Schema for updating a container."""

    name: str | None = Field(None, min_length=1, max_length=255)
    location_id: UUID | None = None
    parent_container_id: UUID | None = None
    notes: str | None = None


class ContainerResponse(BaseModel):
    """Schema for container response."""

    id: UUID
    name: str
    location_id: UUID
    parent_container_id: UUID | None
    qr_code: str
    notes: str | None
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
