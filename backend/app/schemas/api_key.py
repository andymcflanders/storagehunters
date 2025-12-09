"""API Key schemas for external integrations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class APIKeyScope(str, Enum):
    """API key permission scopes."""

    READ = "read"
    WRITE = "write"
    SEARCH = "search"
    WEBHOOKS = "webhooks"
    ADMIN = "admin"


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    scopes: list[APIKeyScope] = Field(default=[APIKeyScope.READ])
    expires_at: datetime | None = None


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    scopes: list[APIKeyScope] | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None


class APIKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)."""

    id: UUID
    name: str
    description: str | None
    key_prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyResponse):
    """Schema for newly created API key (includes the actual key)."""

    key: str  # Only returned once on creation


class WebhookEvent(str, Enum):
    """Events that can trigger webhooks."""

    # Item events
    ITEM_CREATED = "item.created"
    ITEM_UPDATED = "item.updated"
    ITEM_DELETED = "item.deleted"
    ITEM_MOVED = "item.moved"

    # Container events
    CONTAINER_CREATED = "container.created"
    CONTAINER_UPDATED = "container.updated"
    CONTAINER_DELETED = "container.deleted"

    # Location events
    LOCATION_CREATED = "location.created"
    LOCATION_UPDATED = "location.updated"
    LOCATION_DELETED = "location.deleted"

    # Reminder events
    REMINDER_DUE = "reminder.due"
    REMINDER_OVERDUE = "reminder.overdue"
    REMINDER_COMPLETED = "reminder.completed"

    # Stats events
    STATS_UPDATED = "stats.updated"


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""

    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1)
    secret: str | None = None
    events: list[WebhookEvent] = Field(..., min_length=1)
    retry_count: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=120)


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""

    name: str | None = Field(None, min_length=1, max_length=255)
    url: str | None = None
    secret: str | None = None
    events: list[WebhookEvent] | None = None
    is_active: bool | None = None
    retry_count: int | None = Field(None, ge=0, le=10)
    timeout_seconds: int | None = Field(None, ge=5, le=120)


class WebhookResponse(BaseModel):
    """Schema for webhook response."""

    id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    retry_count: int
    timeout_seconds: int
    last_triggered_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    failure_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""

    id: UUID
    webhook_id: UUID
    event: str
    response_status: int | None
    success: bool
    attempt_count: int
    delivered_at: datetime

    model_config = {"from_attributes": True}


class WebhookTestRequest(BaseModel):
    """Schema for testing a webhook."""

    event: WebhookEvent = WebhookEvent.STATS_UPDATED
