"""Pydantic schemas for StorageHub API."""

from app.schemas.container import (
    ContainerCreate,
    ContainerResponse,
    ContainerUpdate,
    ContainerWithItems,
)
from app.schemas.item import (
    ItemCreate,
    ItemImageResponse,
    ItemResponse,
    ItemUpdate,
    ItemWithDetails,
)
from app.schemas.location import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    LocationWithContainers,
)
from app.schemas.printer import PrinterCreate, PrinterResponse, PrinterUpdate
from app.schemas.search import SearchFilters, SearchResult
from app.schemas.tag import TagCreate, TagResponse
from app.schemas.user import (
    LoginRequest,
    SessionResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "SessionResponse",
    # Location
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    "LocationWithContainers",
    # Container
    "ContainerCreate",
    "ContainerUpdate",
    "ContainerResponse",
    "ContainerWithItems",
    # Item
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    "ItemWithDetails",
    "ItemImageResponse",
    # Tag
    "TagCreate",
    "TagResponse",
    # Printer
    "PrinterCreate",
    "PrinterUpdate",
    "PrinterResponse",
    # Search
    "SearchFilters",
    "SearchResult",
]
