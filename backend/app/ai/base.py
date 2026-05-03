"""Base classes for AI image classification."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class CandidateOwner:
    """A user the classifier may pick as the suggested owner.

    Age is computed from birthdate at call time so the prompt sees
    "age: 6" rather than a date the model would have to reason about.
    `age` is None when the user hasn't recorded a birthdate — the model
    can still match on gender and name.
    """

    id: str
    name: str
    gender: str | None  # "male" / "female" / "other" / None
    age: int | None


@dataclass
class ClassificationResult:
    """Result of image classification.

    `names` and `descriptions` are keyed by ISO language code, e.g.
    {"en": "Red sweater", "no": "Rød genser"}. The set of keys depends
    on AISettings.supported_languages at the time of generation.
    """

    names: dict[str, str] = field(default_factory=dict)
    descriptions: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    size: str = ""  # Size in EU format (e.g., "46", "M", "104")
    # Age range (in months) the size implies. Populated for kid-mapped
    # sizes (kids' clothing height-cm, kids' shoe sizes, etc.) and left
    # null for adult sizes or non-age-mapped items. Drives /outgrown.
    size_age_min_months: int | None = None
    size_age_max_months: int | None = None
    seasonal: str = ""  # Season: none, spring, summer, fall, winter, holiday
    confidence: float = 0.0
    # Phase 2 owner suggestion. The classifier returns None when no
    # candidate is a clear match (e.g. household items, generic adult
    # basics where multiple candidates would fit equally).
    suggested_owner_id: str | None = None
    owner_confidence: float = 0.0
    owner_reason: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ImageClassifier(Protocol):
    """Protocol for image classifiers."""

    async def classify(
        self,
        images: list[bytes],
        candidate_owners: list[CandidateOwner] | None = None,
    ) -> ClassificationResult:
        """
        Classify one or more images of the same item and return name, tags, and description.

        Args:
            images: List of image file contents as bytes (all images of the same item)
            candidate_owners: Optional list of users to consider for
                ownership suggestion. When None or empty, suggestion is
                skipped.

        Returns:
            ClassificationResult with name, tags, description, and confidence
        """
        ...


class BaseClassifier(ABC):
    """Abstract base class for image classifiers."""

    @abstractmethod
    async def classify(
        self,
        images: list[bytes],
        candidate_owners: list[CandidateOwner] | None = None,
    ) -> ClassificationResult:
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
