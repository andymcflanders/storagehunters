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

    def __init__(self, delay: float = 0.5):
        """
        Initialize mock classifier.

        Args:
            delay: Simulated processing delay in seconds
        """
        self.delay = delay

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        """Generate mock classification based on image hash."""
        import asyncio
        await asyncio.sleep(self.delay)

        # Use image hash for deterministic results
        image_hash = hashlib.md5(image_bytes).hexdigest()
        random.seed(image_hash)

        # Generate tags
        tags = []

        # Always add a color
        tags.append(random.choice(SAMPLE_COLORS))
        if random.random() > 0.5:
            tags.append(random.choice(SAMPLE_COLORS))

        # Add category and item type
        tags.append(random.choice(SAMPLE_CATEGORIES))
        tags.append(random.choice(SAMPLE_ITEMS))

        # Maybe add material
        if random.random() > 0.3:
            tags.append(random.choice(SAMPLE_MATERIALS))

        # Maybe add pattern
        if random.random() > 0.5:
            tags.append(random.choice(SAMPLE_PATTERNS))

        # Maybe add season
        if random.random() > 0.6:
            tags.append(random.choice(SAMPLE_SEASONS))

        # Maybe add size
        if random.random() > 0.7:
            tags.append(random.choice(SAMPLE_SIZES))

        # Normalize and dedupe
        tags = self._normalize_tags(tags)

        # Generate description
        color = tags[0] if tags else "unknown"
        item = next((t for t in tags if t in SAMPLE_ITEMS), "item")
        description = f"A {color} {item} in good condition."

        return ClassificationResult(
            tags=tags,
            description=description,
            confidence=0.85,
            raw_response={"mock": True, "hash": image_hash},
        )
