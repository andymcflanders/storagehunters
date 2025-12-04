"""Search schemas."""

from uuid import UUID

from pydantic import BaseModel

from app.models.item import ConditionEnum, SeasonalEnum
from app.schemas.item import ItemResponse


class SearchFilters(BaseModel):
    """Search filter parameters."""

    q: str | None = None
    owner: UUID | None = None
    location: UUID | None = None
    container: UUID | None = None
    size: str | None = None
    condition: ConditionEnum | None = None
    seasonal: SeasonalEnum | None = None
    tags: list[str] | None = None


class PathElement(BaseModel):
    """Path element for search results."""

    id: UUID
    name: str
    type: str  # "location" or "container"


class SearchResultItem(ItemResponse):
    """Search result with path information."""

    path: list[PathElement] = []
    thumbnail_url: str | None = None
    matching_tags: list[str] = []


class SearchResult(BaseModel):
    """Search results response."""

    query: str | None
    total: int
    items: list[SearchResultItem]
