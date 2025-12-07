"""Base classes for AI image classification."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ClassificationResult:
    """Result of image classification."""

    name: str = ""  # Short, descriptive name for the item (English)
    name_no: str = ""  # Norwegian name for the item
    tags: list[str] = field(default_factory=list)
    description: str = ""
    description_no: str = ""  # Norwegian description
    size: str = ""  # Size in EU format (e.g., "46", "M", "104")
    seasonal: str = ""  # Season: none, spring, summer, fall, winter, holiday
    confidence: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ImageClassifier(Protocol):
    """Protocol for image classifiers."""

    async def classify(self, images: list[bytes]) -> ClassificationResult:
        """
        Classify one or more images of the same item and return name, tags, and description.

        Args:
            images: List of image file contents as bytes (all images of the same item)

        Returns:
            ClassificationResult with name, tags, description, and confidence
        """
        ...


class BaseClassifier(ABC):
    """Abstract base class for image classifiers."""

    @abstractmethod
    async def classify(self, images: list[bytes]) -> ClassificationResult:
        """Classify one or more images of the same item."""
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
