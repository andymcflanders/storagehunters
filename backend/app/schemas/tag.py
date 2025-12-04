"""Tag schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """Schema for creating a tag."""

    name: str = Field(..., min_length=1, max_length=100)


class TagResponse(BaseModel):
    """Schema for tag response."""

    id: UUID
    name: str
    user_created: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TagMerge(BaseModel):
    """Schema for merging tags."""

    source_tag_ids: list[UUID]
    target_tag_id: UUID
