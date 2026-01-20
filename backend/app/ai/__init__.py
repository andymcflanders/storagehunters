"""AI classification module."""

from dataclasses import dataclass

from app.ai.base import BaseClassifier, ClassificationResult, ImageClassifier
from app.ai.mock_classifier import MockClassifier
from app.ai.openai_vision import OpenAIVisionClassifier
from app.ai.summary_generator import (
    ContainerItem,
    SummaryGenerator,
    SummaryResult,
)
from app.config import get_settings

__all__ = [
    "BaseClassifier",
    "ClassificationResult",
    "ImageClassifier",
    "OpenAIVisionClassifier",
    "MockClassifier",
    "get_classifier",
    "get_summary_generator",
    "ContainerItem",
    "SummaryGenerator",
    "SummaryResult",
    "_reset_classifier_cache",
]


@dataclass
class CachedAISettings:
    """Cached AI settings from database."""

    vision_enabled: bool = True
    vision_model: str = "gpt-4o"
    vision_max_tokens: int = 500
    vision_temperature: float = 0.3
    summary_enabled: bool = True
    summary_model: str = "gpt-4o-mini"
    summary_max_tokens: int = 150
    summary_temperature: float = 0.3


# Module-level cache
_ai_settings_cache: CachedAISettings | None = None
_summary_generator_cache: SummaryGenerator | None = None


def _load_ai_settings_sync() -> CachedAISettings:
    """
    Load AI settings from database synchronously.
    Uses a new connection to avoid async issues.
    """
    global _ai_settings_cache

    if _ai_settings_cache is not None:
        return _ai_settings_cache

    try:
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import Session
        from app.models.ai_settings import AISettings
        from app.config import get_settings

        config = get_settings()

        # Create a sync engine for this one-off query
        # Convert async URL to sync if needed
        db_url = str(config.database_url)
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(select(AISettings).limit(1))
            settings = result.scalar_one_or_none()

            if settings:
                _ai_settings_cache = CachedAISettings(
                    vision_enabled=settings.vision_enabled,
                    vision_model=settings.vision_model,
                    vision_max_tokens=settings.vision_max_tokens,
                    vision_temperature=settings.vision_temperature,
                    summary_enabled=settings.summary_enabled,
                    summary_model=settings.summary_model,
                    summary_max_tokens=settings.summary_max_tokens,
                    summary_temperature=settings.summary_temperature,
                )
            else:
                # Use defaults if no settings exist yet
                _ai_settings_cache = CachedAISettings()

        engine.dispose()

    except Exception:
        # Fall back to defaults if database is unavailable
        _ai_settings_cache = CachedAISettings()

    return _ai_settings_cache


def _reset_classifier_cache() -> None:
    """Reset the classifier cache. Call this when AI settings are updated."""
    global _ai_settings_cache, _summary_generator_cache
    _ai_settings_cache = None
    _summary_generator_cache = None


def get_classifier() -> BaseClassifier:
    """
    Get the configured image classifier based on settings.

    Returns:
        An image classifier instance
    """
    settings = get_settings()
    ai_settings = _load_ai_settings_sync()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            # Fall back to mock if no API key
            return MockClassifier()

        if not ai_settings.vision_enabled:
            return MockClassifier()

        return OpenAIVisionClassifier(
            api_key=settings.openai_api_key,
            model=ai_settings.vision_model,
            max_tokens=ai_settings.vision_max_tokens,
            temperature=ai_settings.vision_temperature,
        )

    elif settings.ai_provider == "mock":
        return MockClassifier()

    else:
        # Default to mock for unknown providers
        return MockClassifier()


def get_summary_generator() -> SummaryGenerator:
    """Get or create the summary generator instance with current settings."""
    global _summary_generator_cache

    if _summary_generator_cache is not None:
        return _summary_generator_cache

    settings = get_settings()
    ai_settings = _load_ai_settings_sync()

    _summary_generator_cache = SummaryGenerator(
        api_key=settings.openai_api_key if settings.openai_api_key else None,
        model=ai_settings.summary_model,
        max_tokens=ai_settings.summary_max_tokens,
        temperature=ai_settings.summary_temperature,
        enabled=ai_settings.summary_enabled,
    )

    return _summary_generator_cache
