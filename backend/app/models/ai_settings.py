"""AI settings model for OpenAI configuration."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


# OpenAI pricing per 1M tokens (as of early 2025)
# https://openai.com/api/pricing/
OPENAI_MODEL_PRICING = {
    # GPT-4o models
    "gpt-4o": {"input": 2.50, "output": 10.00, "vision_input": 2.50},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.00, "vision_input": 2.50},
    "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00, "vision_input": 2.50},
    "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00, "vision_input": 5.00},
    # GPT-4o-mini models
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "vision_input": 0.15},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60, "vision_input": 0.15},
    # GPT-4 Turbo
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "vision_input": 10.00},
    "gpt-4-turbo-2024-04-09": {"input": 10.00, "output": 30.00, "vision_input": 10.00},
    # GPT-4
    "gpt-4": {"input": 30.00, "output": 60.00},
    # GPT-3.5 Turbo
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-3.5-turbo-0125": {"input": 0.50, "output": 1.50},
}

# Available models for vision classification
VISION_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "description": "Best quality, fast, recommended"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Good quality, very fast, cheapest"},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "High quality, slower, expensive"},
]

# Available models for text generation (summaries)
TEXT_MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast and cheap, recommended"},
    {"id": "gpt-4o", "name": "GPT-4o", "description": "Higher quality, more expensive"},
    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Legacy, cheap"},
]


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    has_images: bool = False,
) -> float:
    """
    Estimate the cost for an API call.

    Args:
        model: The model ID
        input_tokens: Estimated input tokens
        output_tokens: Estimated output tokens
        has_images: Whether the request includes images

    Returns:
        Estimated cost in USD
    """
    pricing = OPENAI_MODEL_PRICING.get(model, OPENAI_MODEL_PRICING["gpt-4o"])

    if has_images and "vision_input" in pricing:
        input_price = pricing["vision_input"]
    else:
        input_price = pricing["input"]

    output_price = pricing["output"]

    # Convert from per 1M tokens to actual cost
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return input_cost + output_cost


def estimate_vision_cost(model: str, num_images: int = 1) -> dict:
    """
    Estimate the cost for a vision classification call.

    Typical usage:
    - Input: ~500 tokens for prompt + ~765 tokens per image (low detail) or ~1700 (high detail)
    - Output: ~200-400 tokens for JSON response

    Args:
        model: The model ID
        num_images: Number of images

    Returns:
        Dict with estimated cost details
    """
    # Estimate tokens (using auto detail mode which averages)
    prompt_tokens = 600  # Base prompt
    image_tokens = 1000 * num_images  # Approximate for auto detail
    input_tokens = prompt_tokens + image_tokens
    output_tokens = 350  # JSON response

    cost = estimate_cost(model, input_tokens, output_tokens, has_images=True)

    return {
        "model": model,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
        "cost_per_image_usd": round(cost / num_images, 6) if num_images > 0 else 0,
    }


def estimate_summary_cost(model: str) -> dict:
    """
    Estimate the cost for a summary generation call.

    Typical usage:
    - Input: ~300-500 tokens for prompt with item list
    - Output: ~50-100 tokens for summary

    Args:
        model: The model ID

    Returns:
        Dict with estimated cost details
    """
    input_tokens = 400
    output_tokens = 75

    cost = estimate_cost(model, input_tokens, output_tokens, has_images=False)

    return {
        "model": model,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
    }


class AISettings(Base):
    """AI settings model - singleton table for OpenAI configuration."""

    __tablename__ = "ai_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Vision classification settings (for item photos)
    vision_model: Mapped[str] = mapped_column(
        String(100),
        default="gpt-4o",
        nullable=False,
    )
    vision_max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=500,
        nullable=False,
    )
    vision_temperature: Mapped[float] = mapped_column(
        Float,
        default=0.3,
        nullable=False,
    )

    # Summary generation settings (for container labels)
    summary_model: Mapped[str] = mapped_column(
        String(100),
        default="gpt-4o-mini",
        nullable=False,
    )
    summary_max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=150,
        nullable=False,
    )
    summary_temperature: Mapped[float] = mapped_column(
        Float,
        default=0.3,
        nullable=False,
    )

    # Enable/disable AI features
    vision_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    summary_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    # When true, the vision classifier also picks the most likely owner
    # (matching item size + motif against each non-admin user's age and
    # gender) and stores it on the item as a non-binding suggestion.
    owner_suggestion_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Languages the AI should generate content in (ISO codes, e.g. ["en", "no"]).
    # The OpenAI prompt asks for one name + description per language.
    supported_languages: Mapped[list[str]] = mapped_column(
        ARRAY(String(length=10)),
        default=lambda: ["en", "no"],
        nullable=False,
    )
    # Fallback language used when a translation is missing for a user's locale.
    default_language: Mapped[str] = mapped_column(
        String(length=10),
        default="en",
        nullable=False,
    )

    # Persistent OpenAI API key. Takes precedence over the OPENAI_API_KEY
    # env var, which stays as a fallback for installs that haven't been
    # onboarded yet.
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stable identifier for *this* StorageHub instance, surfaced by
    # /api/ha/status. The HA integration uses it as its config-entry
    # unique_id so reconfiguring the host URL doesn't fork a new
    # entry and orphan the old entities.
    instance_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
