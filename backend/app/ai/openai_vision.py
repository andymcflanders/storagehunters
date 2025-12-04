"""OpenAI Vision API implementation for image classification."""

import base64
import json
import re
from typing import Any

import httpx

from app.ai.base import BaseClassifier, ClassificationResult
from app.config import get_settings

settings = get_settings()

# Prompt for consistent tag generation
CLASSIFICATION_PROMPT = """Analyze this image of a stored item and provide detailed tags and description for a home inventory system.

Return a JSON object with the following structure:
{
  "tags": ["tag1", "tag2", ...],
  "description": "A brief description of the item"
}

For tags, include:
- Primary color(s): e.g., "red", "blue", "multicolor"
- Secondary colors if notable
- Item category: e.g., "clothing", "tools", "toys", "electronics", "kitchenware"
- Specific item type: e.g., "jacket", "drill", "stuffed animal", "laptop"
- Material: e.g., "cotton", "plastic", "metal", "wood", "leather"
- Pattern: e.g., "solid", "striped", "floral", "plaid", "checkered"
- Style descriptors: e.g., "vintage", "modern", "casual", "formal"
- Season if applicable: e.g., "winter", "summer"
- Size indicators if visible: e.g., "large", "small"
- Brand if clearly visible
- Any other distinctive features

Keep tags lowercase and single words or short phrases (2-3 words max).
Aim for 8-15 relevant tags.

For the description, write 1-2 sentences describing what the item is and its notable features.

IMPORTANT: Return ONLY the JSON object, no other text."""


class OpenAIVisionClassifier(BaseClassifier):
    """Image classifier using OpenAI Vision API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 500,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.max_tokens = max_tokens
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def classify(self, image_bytes: bytes) -> ClassificationResult:
        """Classify an image using OpenAI Vision API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        # Encode image as base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Detect image type from magic bytes
        image_type = self._detect_image_type(image_bytes)

        # Build request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{image_b64}",
                                "detail": "low",  # Use low detail for cost efficiency
                            },
                        },
                    ],
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.3,  # Lower temperature for more consistent output
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Parse response
        return self._parse_response(data)

    def _detect_image_type(self, image_bytes: bytes) -> str:
        """Detect image MIME type from magic bytes."""
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif image_bytes[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        else:
            return "image/jpeg"  # Default to JPEG

    def _parse_response(self, data: dict[str, Any]) -> ClassificationResult:
        """Parse OpenAI API response into ClassificationResult."""
        try:
            content = data["choices"][0]["message"]["content"]

            # Try to extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                # If no JSON found, try parsing the whole content
                parsed = json.loads(content)

            tags = parsed.get("tags", [])
            description = parsed.get("description", "")

            # Normalize tags
            tags = self._normalize_tags(tags)

            return ClassificationResult(
                tags=tags,
                description=description,
                confidence=0.9,  # OpenAI doesn't provide confidence scores
                raw_response=data,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # If parsing fails, return empty result
            return ClassificationResult(
                tags=[],
                description="",
                confidence=0.0,
                raw_response={"error": str(e), "raw": data},
            )
