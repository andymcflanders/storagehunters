"""Webhook management API routes."""

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.webhook import Webhook, WebhookDelivery, WebhookEvent
from app.schemas.api_key import (
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookTestRequest,
    WebhookUpdate,
)
from app.services.webhook_service import WebhookService

router = APIRouter()


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    db: DbSession,
    current_user: CurrentUser,
) -> list[WebhookResponse]:
    """List all webhooks for the current user."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.user_id == current_user.id)
        .order_by(Webhook.created_at.desc())
    )
    webhooks = result.scalars().all()
    return [WebhookResponse.model_validate(w) for w in webhooks]


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> WebhookResponse:
    """Create a new webhook.

    Subscribe to events like item.created, item.updated, reminder.due, etc.
    """
    webhook = Webhook(
        user_id=current_user.id,
        name=data.name,
        url=data.url,
        secret=data.secret,
        events=[e.value for e in data.events],
        retry_count=data.retry_count,
        timeout_seconds=data.timeout_seconds,
    )
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    return WebhookResponse.model_validate(webhook)


@router.get("/events", response_model=list[dict])
async def list_webhook_events() -> list[dict]:
    """List all available webhook events.

    Use this to discover which events can be subscribed to.
    """
    return [
        {"event": e.value, "description": _get_event_description(e)}
        for e in WebhookEvent
    ]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> WebhookResponse:
    """Get a webhook by ID."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    return WebhookResponse.model_validate(webhook)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> WebhookResponse:
    """Update a webhook."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    if "events" in update_data and update_data["events"]:
        update_data["events"] = [e.value for e in update_data["events"]]

    for field, value in update_data.items():
        setattr(webhook, field, value)

    await db.flush()
    await db.refresh(webhook)
    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a webhook."""
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    await db.delete(webhook)


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryResponse)
async def test_webhook(
    webhook_id: UUID,
    data: WebhookTestRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> WebhookDeliveryResponse:
    """Test a webhook by sending a test event.

    Use this to verify your webhook endpoint is configured correctly.
    """
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    service = WebhookService(db)
    delivery = await service.send_test_event(webhook, data.event.value)

    return WebhookDeliveryResponse.model_validate(delivery)


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    webhook_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = 20,
) -> list[WebhookDeliveryResponse]:
    """List recent webhook deliveries.

    Use this to debug webhook delivery issues.
    """
    result = await db.execute(
        select(Webhook)
        .where(Webhook.id == webhook_id)
        .where(Webhook.user_id == current_user.id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )

    deliveries_result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(limit)
    )
    deliveries = deliveries_result.scalars().all()

    return [WebhookDeliveryResponse.model_validate(d) for d in deliveries]


def _get_event_description(event: WebhookEvent) -> str:
    """Get a description for a webhook event."""
    descriptions = {
        WebhookEvent.ITEM_CREATED: "Triggered when a new item is created",
        WebhookEvent.ITEM_UPDATED: "Triggered when an item is updated",
        WebhookEvent.ITEM_DELETED: "Triggered when an item is deleted",
        WebhookEvent.ITEM_MOVED: "Triggered when an item is moved to a different container",
        WebhookEvent.CONTAINER_CREATED: "Triggered when a new container is created",
        WebhookEvent.CONTAINER_UPDATED: "Triggered when a container is updated",
        WebhookEvent.CONTAINER_DELETED: "Triggered when a container is deleted",
        WebhookEvent.LOCATION_CREATED: "Triggered when a new location is created",
        WebhookEvent.LOCATION_UPDATED: "Triggered when a location is updated",
        WebhookEvent.LOCATION_DELETED: "Triggered when a location is deleted",
        WebhookEvent.REMINDER_DUE: "Triggered when a reminder becomes due",
        WebhookEvent.REMINDER_OVERDUE: "Triggered when a reminder becomes overdue",
        WebhookEvent.REMINDER_COMPLETED: "Triggered when a reminder is marked as completed",
        WebhookEvent.SEARCH_PERFORMED: "Triggered when a search is performed",
        WebhookEvent.STATS_UPDATED: "Triggered when inventory statistics change significantly",
    }
    return descriptions.get(event, "No description available")
