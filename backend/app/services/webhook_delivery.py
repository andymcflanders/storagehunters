"""Synchronous webhook delivery, used by the Celery worker.

CRUD handlers enqueue a delivery task and return immediately; the actual
outbound HTTP (with retries and backoff) happens here, off the request path,
so a slow or dead subscriber never blocks a user request. The URL is
re-validated against the SSRF policy at delivery time — the only check that
resists DNS-rebinding between webhook creation and delivery.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_sync_db
from app.models.webhook import Webhook, WebhookDelivery
from app.services.webhook_security import WebhookURLError, validate_webhook_url

logger = logging.getLogger(__name__)

_MAX_RESPONSE_BODY = 1000


def build_headers(webhook: Webhook, event: str, payload_json: str) -> dict[str, str]:
    """Build request headers, including the HMAC signature when a secret is set."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "StorageHub-Webhook/1.0",
        "X-StorageHub-Event": event,
    }
    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(), payload_json.encode(), hashlib.sha256
        ).hexdigest()
        headers["X-StorageHub-Signature"] = f"sha256={signature}"
    return headers


def _record_status(webhook: Webhook, success: bool) -> None:
    now = datetime.now(timezone.utc)
    webhook.last_triggered_at = now
    if success:
        webhook.last_success_at = now
        webhook.failure_count = 0
    else:
        webhook.last_failure_at = now
        webhook.failure_count = (webhook.failure_count or 0) + 1


def deliver_to_webhook(
    db: Session, webhook: Webhook, event: str, payload: dict[str, Any]
) -> WebhookDelivery:
    """Deliver one event to one webhook, recording the attempt. Never raises."""
    full_payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }
    payload_json = json.dumps(full_payload, default=str)

    delivery = WebhookDelivery(webhook_id=webhook.id, event=event, payload=payload_json)
    delivery.attempt_count = 0
    delivery.success = False

    # SSRF re-check at delivery time (resists DNS-rebinding).
    try:
        validate_webhook_url(webhook.url, resolve=True)
    except WebhookURLError as exc:
        delivery.response_body = f"Blocked by SSRF policy: {exc}"[:_MAX_RESPONSE_BODY]
        _record_status(webhook, success=False)
        db.add(delivery)
        db.flush()
        logger.warning("Webhook %s blocked: %s", webhook.id, exc)
        return delivery

    headers = build_headers(webhook, event, payload_json)
    max_attempts = (webhook.retry_count or 0) + 1
    success = False
    response_status: int | None = None
    response_body: str | None = None
    attempts = 0

    with httpx.Client(timeout=webhook.timeout_seconds) as client:
        for attempt in range(max_attempts):
            attempts = attempt + 1
            try:
                response = client.post(webhook.url, content=payload_json, headers=headers)
                response_status = response.status_code
                response_body = response.text[:_MAX_RESPONSE_BODY]
                if 200 <= response.status_code < 300:
                    success = True
                    break
                if response.status_code >= 500 and attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                break
            except httpx.TimeoutException:
                response_body = "Request timed out"
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                break
            except httpx.RequestError as exc:
                response_body = f"Request error: {exc}"
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                break

    delivery.response_status = response_status
    delivery.response_body = response_body
    delivery.success = success
    delivery.attempt_count = attempts  # the real number of attempts made
    _record_status(webhook, success)
    db.add(delivery)
    db.flush()
    return delivery


def deliver_event(event: str, payload: dict[str, Any], user_id: str | None = None) -> int:
    """Deliver an event to every active webhook subscribed to it.

    Returns the number of webhooks the event was delivered to. `user_id`
    optionally restricts delivery to one owner's webhooks; entity events pass
    None so any subscriber in the household receives them.
    """
    delivered = 0
    with get_sync_db() as db:
        query = select(Webhook).where(Webhook.is_active == True)  # noqa: E712
        if user_id:
            query = query.where(Webhook.user_id == UUID(user_id))
        webhooks = db.execute(query).scalars().all()
        for webhook in webhooks:
            if webhook.subscribes_to(event):
                deliver_to_webhook(db, webhook, event, payload)
                delivered += 1
    return delivered
