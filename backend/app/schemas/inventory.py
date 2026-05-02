"""Inventory schemas for God View."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserInfo(BaseModel):
    """Brief user info for owner selection."""

    id: UUID
    name: str

    model_config = {"from_attributes": True}


class GodViewItem(BaseModel):
    """Item data for God View with core editable fields."""

    id: UUID
    name: str
    description: str | None
    size: str | None
    condition: str
    seasonal: str
    owner_id: UUID | None
    owner_name: str | None
    thumbnail_url: str | None
    value_estimate: float | None
    ai_names: dict[str, str] = {}
    ai_descriptions: dict[str, str] = {}
    ai_processed: bool
    needs_review: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GodViewContainer(BaseModel):
    """Container data for God View with nested children."""

    id: UUID
    name: str
    notes: str | None
    qr_code: str
    location_id: UUID
    parent_container_id: UUID | None
    items: list[GodViewItem] = []
    children: list["GodViewContainer"] = []
    item_count: int = 0

    model_config = {"from_attributes": True}


# Allow recursive type reference
GodViewContainer.model_rebuild()


class GodViewLocation(BaseModel):
    """Location data for God View with nested containers."""

    id: UUID
    name: str
    description: str | None
    address: str | None
    sort_order: int
    containers: list[GodViewContainer] = []
    container_count: int = 0
    item_count: int = 0

    model_config = {"from_attributes": True}


class GodViewResponse(BaseModel):
    """Complete inventory tree response for God View."""

    locations: list[GodViewLocation]
    users: list[UserInfo]
    total_locations: int
    total_containers: int
    total_items: int


class ContainerMoveRequest(BaseModel):
    """Request to move a container to a different location or parent."""

    location_id: UUID | None = None
    parent_container_id: UUID | None = None
