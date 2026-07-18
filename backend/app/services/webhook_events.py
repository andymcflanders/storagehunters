"""Emitting webhook events from request handlers.

Handlers call `emit_webhook_event(...)`, which enqueues a Celery delivery task
and returns immediately. Emission is best-effort: if the broker is unreachable
the event is dropped with a log line rather than failing the user's request
(creating an item must not 500 because a webhook queue is down).

Payloads must be JSON-serializable (Celery's json serializer), so callers pass
already-stringified UUIDs.
"""

import logging
from typing import Any
from uuid import UUID

from app.models.webhook import WebhookEvent

logger = logging.getLogger(__name__)


def emit_webhook_event(
    event: WebhookEvent | str,
    payload: dict[str, Any],
    user_id: UUID | str | None = None,
) -> None:
    """Enqueue a webhook event for out-of-band delivery. Never raises."""
    event_value = event.value if isinstance(event, WebhookEvent) else event
    uid = str(user_id) if user_id is not None else None
    try:
        from app.worker.tasks import deliver_webhook_event

        deliver_webhook_event.delay(event_value, payload, uid)
    except Exception:  # broker down, serialization issue, etc.
        logger.exception("Failed to enqueue webhook event %s", event_value)
