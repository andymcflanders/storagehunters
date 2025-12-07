"""OpenAI Vision API implementation for image classification."""

import base64
import json
import re
from typing import Any

import httpx

from app.ai.base import BaseClassifier, ClassificationResult
from app.config import get_settings

settings = get_settings()

# Prompt for consistent classification with name generation in both English and Norwegian
CLASSIFICATION_PROMPT_SINGLE = """Analyze this image of a stored item for a home inventory system.

Return a JSON object with:
{
  "name": "Short item name in English (2-5 words)",
  "name_no": "Short item name in Norwegian (2-5 words)",
  "tags": ["tag1", "tag2", ...],
  "description": "Brief description in English",
  "description_no": "Brief description in Norwegian",
  "size": "Size in EU format or null",
  "seasonal": "none|spring|summer|fall|winter|holiday"
}

For NAME (both English and Norwegian):
- Keep it short and descriptive (2-5 words)
- Include the most specific item type
- Include brand if clearly visible (keep brand names unchanged)
- English examples: "Blue Nike Running Shoes", "IKEA Billy Bookshelf", "Red Wool Sweater"
- Norwegian examples: "Blå Nike Løpesko", "IKEA Billy Bokhylle", "Rød Ullgenser"

For TAGS, include:
- Primary color(s), item category, specific type, material, pattern
- Style, season if applicable, size if visible, brand if visible
- Keep tags lowercase in English, 8-15 relevant tags

For DESCRIPTION (both languages):
- 1-2 sentences about the item and notable features

For SIZE:
- Extract size if visible on labels/tags
- ALWAYS use EU/European sizing (convert if needed):
  * Clothing: EU sizes like 46, 48, 50, 52 (not US 16, 18)
  * Children's clothes: Use height in cm (e.g., "104", "110", "116", "122")
  * Shoes: EU sizes like 38, 40, 42 (not US 8, 10)
  * Generic: Use S, M, L, XL if EU conversion unclear
- Return null if no size visible

For SEASONAL:
- Determine the most appropriate season for the item
- "winter" for heavy coats, wool sweaters, boots, scarves, gloves
- "summer" for shorts, tank tops, sandals, swimwear
- "spring" or "fall" for light jackets, transitional clothing
- "holiday" for Christmas decorations, Halloween items, etc.
- "none" for non-seasonal items (tools, electronics, furniture)

IMPORTANT: Return ONLY the JSON object, no other text."""


CLASSIFICATION_PROMPT_MULTI = """Analyze these {count} images showing DIFFERENT ANGLES/DETAILS of the SAME item for a home inventory system.

The images may show:
- Different angles of the item
- Close-ups of labels, tags, or size information
- Brand logos or product details
- The item in use or context

Combine ALL information from ALL images to provide a complete classification.

Return a JSON object with:
{{
  "name": "Short item name in English (2-5 words)",
  "name_no": "Short item name in Norwegian (2-5 words)",
  "tags": ["tag1", "tag2", ...],
  "description": "Brief description in English",
  "description_no": "Brief description in Norwegian",
  "size": "Size in EU format or null",
  "seasonal": "none|spring|summer|fall|winter|holiday"
}}

For NAME (both English and Norwegian):
- Keep it short and descriptive (2-5 words)
- Include the most specific item type
- Include brand if visible in any image (keep brand names unchanged)
- English examples: "Blue Nike Running Shoes", "IKEA Billy Bookshelf White"
- Norwegian examples: "Blå Nike Løpesko", "IKEA Billy Bokhylle Hvit"

For TAGS, include information from ALL images:
- Colors, item category, specific type, material, pattern
- Style, season, size (from labels), brand (from logos)
- Any text visible on labels or tags
- Keep tags lowercase in English, 8-15 relevant tags

For DESCRIPTION (both languages):
- 1-2 sentences combining details from all images

For SIZE:
- Extract size from labels/tags visible in any image
- ALWAYS use EU/European sizing (convert if needed):
  * Clothing: EU sizes like 46, 48, 50, 52 (not US 16, 18)
  * Children's clothes: Use height in cm (e.g., "104", "110", "116", "122")
  * Shoes: EU sizes like 38, 40, 42 (not US 8, 10)
  * Generic: Use S, M, L, XL if EU conversion unclear
- Return null if no size visible

For SEASONAL:
- Determine the most appropriate season for the item
- "winter" for heavy coats, wool sweaters, boots, scarves, gloves
- "summer" for shorts, tank tops, sandals, swimwear
- "spring" or "fall" for light jackets, transitional clothing
- "holiday" for Christmas decorations, Halloween items, etc.
- "none" for non-seasonal items (tools, electronics, furniture)

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

    async def classify(self, images: list[bytes]) -> ClassificationResult:
        """Classify one or more images of the same item using OpenAI Vision API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        if not images:
            return ClassificationResult()

        # Build request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Build content with all images
        content: list[dict] = []

        # Add prompt (different for single vs multiple images)
        if len(images) == 1:
            content.append({"type": "text", "text": CLASSIFICATION_PROMPT_SINGLE})
        else:
            content.append({
                "type": "text",
                "text": CLASSIFICATION_PROMPT_MULTI.format(count=len(images))
            })

        # Add all images
        for image_bytes in images:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_type = self._detect_image_type(image_bytes)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_b64}",
                    "detail": "low",  # Use low detail for cost efficiency
                },
            })

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.max_tokens,
            "temperature": 0.3,  # Lower temperature for more consistent output
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
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

            name = parsed.get("name", "")
            name_no = parsed.get("name_no", "")
            tags = parsed.get("tags", [])
            description = parsed.get("description", "")
            description_no = parsed.get("description_no", "")
            size = parsed.get("size") or ""  # Handle null
            seasonal = parsed.get("seasonal", "none")

            # Normalize tags
            tags = self._normalize_tags(tags)

            # Validate seasonal value
            valid_seasons = {"none", "spring", "summer", "fall", "winter", "holiday"}
            if seasonal.lower() not in valid_seasons:
                seasonal = "none"
            else:
                seasonal = seasonal.lower()

            return ClassificationResult(
                name=name,
                name_no=name_no,
                tags=tags,
                description=description,
                description_no=description_no,
                size=size,
                seasonal=seasonal,
                confidence=0.9,  # OpenAI doesn't provide confidence scores
                raw_response=data,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # If parsing fails, return empty result
            return ClassificationResult(
                name="",
                tags=[],
                description="",
                confidence=0.0,
                raw_response={"error": str(e), "raw": data},
            )
