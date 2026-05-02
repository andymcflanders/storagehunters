"""Mock classifier for development and testing."""

import hashlib
import random

from app.ai.base import BaseClassifier, ClassificationResult

# Sample tags for mock classification
SAMPLE_COLORS = ["red", "blue", "green", "black", "white", "gray", "brown", "yellow", "orange", "purple", "pink"]
SAMPLE_CATEGORIES = ["clothing", "tools", "electronics", "kitchenware", "toys", "books", "sports", "outdoor", "decor"]
SAMPLE_MATERIALS = ["cotton", "plastic", "metal", "wood", "leather", "fabric", "polyester", "rubber"]
SAMPLE_PATTERNS = ["solid", "striped", "plaid", "floral", "checkered", "printed"]
SAMPLE_SEASONS = ["winter", "summer", "spring", "fall", "all-season"]
SAMPLE_SIZES = ["small", "medium", "large", "extra-large"]
SAMPLE_ITEMS = [
    "jacket", "shirt", "pants", "dress", "sweater", "coat",
    "drill", "hammer", "screwdriver", "wrench", "saw",
    "laptop", "phone", "charger", "cable", "headphones",
    "pot", "pan", "plate", "cup", "utensils",
    "ball", "game", "puzzle", "doll", "blocks",
    "book", "notebook", "folder", "binder",
]


class MockClassifier(BaseClassifier):
    """Mock classifier that generates deterministic tags based on image hash."""

    def __init__(self, delay: float = 0.5, languages: list[str] | None = None):
        """
        Initialize mock classifier.

        Args:
            delay: Simulated processing delay in seconds
            languages: ISO codes to populate in the mock translations dict
        """
        self.delay = delay
        self.languages = languages or ["en"]

    async def classify(self, images: list[bytes]) -> ClassificationResult:
        """Generate mock classification based on combined image hashes."""
        import asyncio
        await asyncio.sleep(self.delay)

        if not images:
            return ClassificationResult()

        # Combine all image hashes for deterministic results
        combined_hash = hashlib.md5(b"".join(images)).hexdigest()
        random.seed(combined_hash)

        # Generate tags
        tags = []

        # Always add a color
        color = random.choice(SAMPLE_COLORS)
        tags.append(color)
        if random.random() > 0.5:
            tags.append(random.choice(SAMPLE_COLORS))

        # Add category and item type
        tags.append(random.choice(SAMPLE_CATEGORIES))
        item_type = random.choice(SAMPLE_ITEMS)
        tags.append(item_type)

        # Maybe add material
        material = None
        if random.random() > 0.3:
            material = random.choice(SAMPLE_MATERIALS)
            tags.append(material)

        # Maybe add pattern
        if random.random() > 0.5:
            tags.append(random.choice(SAMPLE_PATTERNS))

        # Maybe add season
        if random.random() > 0.6:
            tags.append(random.choice(SAMPLE_SEASONS))

        # Maybe add size
        size = None
        if random.random() > 0.7:
            size = random.choice(SAMPLE_SIZES)
            tags.append(size)

        # Normalize and dedupe
        tags = self._normalize_tags(tags)

        # Generate name (2-5 words)
        name_parts = [color.title()]
        if material:
            name_parts.append(material.title())
        name_parts.append(item_type.title())
        if size:
            name_parts.append(f"({size.title()})")
        name = " ".join(name_parts)

        # Generate description
        description = f"A {color} {item_type}"
        if material:
            description += f" made of {material}"
        description += " in good condition."
        if len(images) > 1:
            description += f" (Analyzed from {len(images)} photos)"

        # Mock fills the same string for every supported language so
        # downstream code paths see populated dicts during dev/testing.
        names = {lang: name for lang in self.languages}
        descriptions = {lang: description for lang in self.languages}

        return ClassificationResult(
            names=names,
            descriptions=descriptions,
            tags=tags,
            confidence=0.85,
            raw_response={"mock": True, "hash": combined_hash, "image_count": len(images)},
        )
