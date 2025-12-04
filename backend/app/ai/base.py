"""Base classes for AI image classification."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ClassificationResult:
    """Result of image classification."""

    tags: list[str] = field(default_factory=list)
    description: str = ""
    confidence: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ImageClassifier(Protocol):
    """Protocol for image classifiers."""

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        """
        Classify an image and return tags and description.

        Args:
            image_bytes: The image file contents as bytes

        Returns:
            ClassificationResult with tags, description, and confidence
        """
        ...


class BaseClassifier(ABC):
    """Abstract base class for image classifiers."""

    @abstractmethod
    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        """Classify an image."""
        pass

    def _normalize_tags(self, tags: list[str]) -> list[str]:
        """Normalize and deduplicate tags."""
        seen = set()
        normalized = []
        for tag in tags:
            tag_lower = tag.lower().strip()
            if tag_lower and tag_lower not in seen:
                seen.add(tag_lower)
                normalized.append(tag_lower)
        return normalized
