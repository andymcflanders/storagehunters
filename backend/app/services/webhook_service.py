"""Webhook service for sending event notifications."""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook, WebhookDelivery, WebhookEvent


class WebhookService:
    """Service for webhook operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_webhooks_for_event(self, event: str) -> list[Webhook]:
        """Get all active webhooks that subscribe to an event."""
        result = await self.db.execute(
            select(Webhook)
            .where(Webhook.is_active == True)
            .where(
                Webhook.events.any(event) | Webhook.events.any("*")
            )
        )
        return list(result.scalars().all())

    async def trigger_event(
        self,
        event: str,
        payload: dict[str, Any],
        user_id: UUID | None = None,
    ) -> list[WebhookDelivery]:
        """Trigger an event and send to all subscribed webhooks."""
        # Get webhooks for this event
        query = select(Webhook).where(Webhook.is_active == True)
        if user_id:
            query = query.where(Webhook.user_id == user_id)

        result = await self.db.execute(query)
        webhooks = result.scalars().all()

        deliveries = []
        for webhook in webhooks:
            if webhook.subscribes_to(event):
                delivery = await self._send_webhook(webhook, event, payload)
                deliveries.append(delivery)

        return deliveries

    async def send_test_event(self, webhook: Webhook, event: str) -> WebhookDelivery:
        """Send a test event to a webhook."""
        test_payload = {
            "test": True,
            "message": "This is a test event from StorageHub",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return await self._send_webhook(webhook, event, test_payload)

    async def _send_webhook(
        self,
        webhook: Webhook,
        event: str,
        payload: dict[str, Any],
    ) -> WebhookDelivery:
        """Send a single webhook request."""
        # Build the full payload
        full_payload = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }
        payload_json = json.dumps(full_payload, default=str)

        # Calculate signature if secret is set
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "StorageHub-Webhook/1.0",
            "X-StorageHub-Event": event,
        }

        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                payload_json.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-StorageHub-Signature"] = f"sha256={signature}"

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload_json,
        )

        # Send the request
        success = False
        response_status = None
        response_body = None

        try:
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                for attempt in range(webhook.retry_count + 1):
                    try:
                        response = await client.post(
                            webhook.url,
                            content=payload_json,
                            headers=headers,
                        )
                        response_status = response.status_code
                        response_body = response.text[:1000]  # Limit response body

                        if 200 <= response.status_code < 300:
                            success = True
                            break

                        # Retry on server errors
                        if response.status_code >= 500 and attempt < webhook.retry_count:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue

                        break

                    except httpx.TimeoutException:
                        response_body = "Request timed out"
                        if attempt < webhook.retry_count:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        break

                    except httpx.RequestError as e:
                        response_body = f"Request error: {str(e)}"
                        if attempt < webhook.retry_count:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        break

        except Exception as e:
            response_body = f"Unexpected error: {str(e)}"

        # Update delivery record
        delivery.response_status = response_status
        delivery.response_body = response_body
        delivery.success = success
        delivery.attempt_count = webhook.retry_count + 1 if not success else 1

        # Update webhook status
        webhook.last_triggered_at = datetime.now(timezone.utc)
        if success:
            webhook.last_success_at = datetime.now(timezone.utc)
            webhook.failure_count = 0
        else:
            webhook.last_failure_at = datetime.now(timezone.utc)
            webhook.failure_count += 1

        self.db.add(delivery)
        await self.db.flush()
        await self.db.refresh(delivery)

        return delivery


# Convenience function for triggering webhooks from anywhere in the app
async def trigger_webhook_event(
    db: AsyncSession,
    event: WebhookEvent | str,
    payload: dict[str, Any],
    user_id: UUID | None = None,
) -> None:
    """Convenience function to trigger a webhook event.

    Usage:
        await trigger_webhook_event(
            db,
            WebhookEvent.ITEM_CREATED,
            {"item_id": str(item.id), "name": item.name},
        )
    """
    event_str = event.value if isinstance(event, WebhookEvent) else event
    service = WebhookService(db)
    await service.trigger_event(event_str, payload, user_id)
