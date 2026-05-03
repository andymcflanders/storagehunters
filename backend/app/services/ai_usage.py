"""Helpers for recording OpenAI API usage.

Inserts one row per call into ai_usage_log. The function is sync and
swallows all errors so logging failures never break the AI flow that
just succeeded — a missing usage row is much better than a missing
classified item.

Cost is computed at log time from the active pricing table and
frozen on the row, so future pricing edits don't retroactively
revalue old calls.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import get_sync_db
from app.models.ai_settings import OPENAI_MODEL_PRICING
from app.models.ai_usage import AIUsageLog

logger = logging.getLogger(__name__)

UsageKind = Literal["vision", "summary", "size_age"]


def _compute_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    has_images: bool,
) -> Decimal:
    """Cost of a single call in USD given OpenAI's actual token counts.

    Falls back to gpt-4o pricing for unknown models — the row is
    still better than no row, even if the dollar figure is mildly
    off for an exotic model.
    """
    pricing = OPENAI_MODEL_PRICING.get(model, OPENAI_MODEL_PRICING["gpt-4o"])
    if has_images and "vision_input" in pricing:
        input_price = Decimal(str(pricing["vision_input"]))
    else:
        input_price = Decimal(str(pricing["input"]))
    output_price = Decimal(str(pricing["output"]))
    million = Decimal("1000000")
    return (
        Decimal(input_tokens) * input_price / million
        + Decimal(output_tokens) * output_price / million
    )


def log_ai_call(
    *,
    kind: UsageKind,
    model: str,
    input_tokens: int,
    output_tokens: int,
    has_images: bool = False,
    user_id: UUID | None = None,
    item_id: UUID | None = None,
    latency_ms: int | None = None,
    db: Session | None = None,
) -> None:
    """Persist one usage row. Never raises.

    Pass an existing `db` session if the caller already has one open
    (e.g. inside a Celery task); otherwise a one-shot session is
    opened and committed.
    """
    try:
        cost = _compute_cost(model, input_tokens, output_tokens, has_images)
        row = AIUsageLog(
            kind=kind,
            model=model,
            input_tokens=int(input_tokens or 0),
            output_tokens=int(output_tokens or 0),
            cost_usd=cost,
            user_id=user_id,
            item_id=item_id,
            latency_ms=latency_ms,
        )
        if db is not None:
            db.add(row)
            # Caller owns the commit; we just queue the insert.
            db.flush()
        else:
            with get_sync_db() as own_db:
                own_db.add(row)
                own_db.commit()
    except Exception as exc:
        # Logging failure must never propagate. The AI call already
        # succeeded — losing one usage row is acceptable.
        logger.warning("ai_usage_log insert failed: %s", exc)
