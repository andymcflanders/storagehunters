"""AI classification module."""

from app.ai.base import BaseClassifier, ClassificationResult, ImageClassifier
from app.ai.mock_classifier import MockClassifier
from app.ai.openai_vision import OpenAIVisionClassifier
from app.ai.summary_generator import (
    ContainerItem,
    SummaryGenerator,
    SummaryResult,
    get_summary_generator,
)
from app.config import get_settings

__all__ = [
    "BaseClassifier",
    "ClassificationResult",
    "ImageClassifier",
    "OpenAIVisionClassifier",
    "MockClassifier",
    "get_classifier",
    "ContainerItem",
    "SummaryGenerator",
    "SummaryResult",
    "get_summary_generator",
]


def get_classifier() -> BaseClassifier:
    """
    Get the configured image classifier based on settings.

    Returns:
        An image classifier instance
    """
    settings = get_settings()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            # Fall back to mock if no API key
            return MockClassifier()
        return OpenAIVisionClassifier(api_key=settings.openai_api_key)

    elif settings.ai_provider == "mock":
        return MockClassifier()

    else:
        # Default to mock for unknown providers
        return MockClassifier()
