"""Location schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    """Base location schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    address: str | None = None
    sort_order: int = 0


class LocationCreate(LocationBase):
    """Schema for creating a location."""

    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    address: str | None = None
    sort_order: int | None = None


class LocationResponse(BaseModel):
    """Schema for location response."""

    id: UUID
    name: str
    description: str | None
    address: str | None
    sort_order: int
    container_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContainerSummary(BaseModel):
    """Brief container info for location responses."""

    id: UUID
    name: str
    qr_code: str
    item_count: int = 0
    container_type: str | None = None
    image_url: str | None = None

    model_config = {"from_attributes": True}


class LocationWithContainers(LocationResponse):
    """Location response with containers included."""

    containers: list[ContainerSummary] = []
