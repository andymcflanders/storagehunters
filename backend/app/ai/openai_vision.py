"""OpenAI Vision API implementation for image classification."""

import base64
import json
import re
from typing import Any

import httpx

from app.ai.base import BaseClassifier, CandidateOwner, ClassificationResult
from app.config import get_settings

settings = get_settings()


# ISO language code -> human-readable name shown to the model in the prompt.
# When a user adds a language outside this map (e.g. "fr"), the code falls
# back to the ISO code itself, which GPT-4o handles fine for common languages.
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "no": "Norwegian",
    "nb": "Norwegian Bokmål",
    "nn": "Norwegian Nynorsk",
    "sv": "Swedish",
    "da": "Danish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "fi": "Finnish",
}


def _language_label(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def _candidate_block(candidates: list[CandidateOwner]) -> str:
    """Render the candidate-owner section of the prompt.

    Empty string when no candidates — the prompt builder then omits
    every owner-related field so the model doesn't try to fill them.
    """
    if not candidates:
        return ""

    lines = []
    for c in candidates:
        bits = [f'id: "{c.id}"', f'name: "{c.name}"']
        if c.gender:
            bits.append(f"gender: {c.gender}")
        if c.age is not None:
            bits.append(f"age: {c.age}")
        else:
            bits.append("age: unknown")
        lines.append("  - " + ", ".join(bits))

    return "\n".join(lines)


def build_classification_prompt(
    languages: list[str],
    image_count: int,
    candidates: list[CandidateOwner] | None = None,
) -> str:
    """Construct the classification prompt for the configured languages.

    The prompt asks GPT to return a JSON object with one `name_<code>`
    and one `description_<code>` field per supported language, plus
    shared fields (tags, size, seasonal). The parser pulls the
    translations out by prefix. When `candidates` is non-empty, the
    prompt also asks for an owner suggestion based on each candidate's
    age + gender vs the item's size and motif.
    """
    if not languages:
        languages = ["en"]
    candidates = candidates or []

    name_lines = "\n".join(
        f'  "name_{code}": "Short item name in {_language_label(code)} (2-5 words)",'
        for code in languages
    )
    desc_lines = "\n".join(
        f'  "description_{code}": "Brief description in {_language_label(code)}",'
        for code in languages
    )

    name_examples = "\n".join(
        f"- {_language_label(code)} examples: " + _name_examples_for(code)
        for code in languages
    )

    if image_count <= 1:
        intro = "Analyze this image of a stored item for a home inventory system."
        desc_guidance = "1-2 sentences about the item and notable features"
    else:
        intro = (
            f"Analyze these {image_count} images showing DIFFERENT ANGLES/DETAILS "
            "of the SAME item for a home inventory system.\n\n"
            "The images may show:\n"
            "- Different angles of the item\n"
            "- Close-ups of labels, tags, or size information\n"
            "- Brand logos or product details\n"
            "- The item in use or context\n\n"
            "Combine ALL information from ALL images to provide a complete classification."
        )
        desc_guidance = "1-2 sentences combining details from all images"

    owner_field_lines = ""
    owner_section = ""
    if candidates:
        owner_field_lines = (
            ',\n  "suggested_owner_id": "<id from candidates list, or null>",'
            '\n  "owner_confidence": 0.0,'
            '\n  "owner_reason": "<one short sentence, or null>"'
        )
        owner_section = f"""

CANDIDATE OWNERS (members of this household):
{_candidate_block(candidates)}

For SUGGESTED_OWNER_ID:
- Pick the candidate whose age + gender most clearly fits this item, based on
  size and motif (e.g. children's size 98 with a dinosaur print fits a
  toddler boy; size 42 wool socks fit any adult).
- Return the candidate's literal `id` value, exactly as listed above.
- Return null when the item is generic enough that multiple candidates
  could equally own it (household items, adult-sized basics where
  several adults match), or when nothing fits well. **Do not guess.**
- owner_confidence is 0.0–1.0; use < 0.5 only when you are unsure.
- owner_reason is one short sentence pointing at the specific signals
  you used (e.g. "size 98 + dinosaur motif fits a toddler boy"). Return
  null when suggested_owner_id is null."""

    return f"""{intro}

Return a JSON object with:
{{
{name_lines}
  "tags": ["tag1", "tag2", ...],
{desc_lines}
  "size": "Size in EU format or null",
  "seasonal": "none|spring|summer|fall|winter|holiday"{owner_field_lines}
}}{owner_section}

For NAME (in every language listed above):
- Keep it short and descriptive (2-5 words)
- Include the most specific item type
- Include brand if clearly visible (keep brand names unchanged)
{name_examples}

For TAGS, include:
- Primary color(s), item category, specific type, material, pattern
- Style, season if applicable, size if visible, brand if visible
- Keep tags lowercase in English, 8-15 relevant tags

For DESCRIPTION (in every language listed above):
- {desc_guidance}

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


def _name_examples_for(code: str) -> str:
    """Per-language naming examples to anchor the model's tone."""
    examples = {
        "en": '"Blue Nike Running Shoes", "IKEA Billy Bookshelf", "Red Wool Sweater"',
        "no": '"Blå Nike Løpesko", "IKEA Billy Bokhylle", "Rød Ullgenser"',
        "nb": '"Blå Nike Løpesko", "IKEA Billy Bokhylle", "Rød Ullgenser"',
        "sv": '"Blå Nike Löparskor", "IKEA Billy Bokhylla", "Röd Ulltröja"',
        "da": '"Blå Nike Løbesko", "IKEA Billy Bogreol", "Rød Uldsweater"',
        "de": '"Blaue Nike Laufschuhe", "IKEA Billy Bücherregal", "Roter Wollpullover"',
        "fr": '"Chaussures de Course Nike Bleues", "Bibliothèque IKEA Billy", "Pull en Laine Rouge"',
        "es": '"Zapatillas Nike Azules", "Estantería IKEA Billy", "Suéter de Lana Rojo"',
        "it": '"Scarpe Nike Blu", "Libreria IKEA Billy", "Maglione di Lana Rosso"',
    }
    return examples.get(code, "(short, item-type-first)")


class OpenAIVisionClassifier(BaseClassifier):
    """Image classifier using OpenAI Vision API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        max_tokens: int = 500,
        temperature: float = 0.3,
        languages: list[str] | None = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.languages = languages or ["en", "no"]
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def classify(
        self,
        images: list[bytes],
        candidate_owners: list[CandidateOwner] | None = None,
    ) -> ClassificationResult:
        """Classify one or more images of the same item using OpenAI Vision API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        if not images:
            return ClassificationResult()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        prompt = build_classification_prompt(
            self.languages,
            image_count=len(images),
            candidates=candidate_owners,
        )
        content: list[dict] = [{"type": "text", "text": prompt}]

        for image_bytes in images:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_type = self._detect_image_type(image_bytes)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_b64}",
                    "detail": "auto",
                },
            })

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, candidate_owners or [])

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
            return "image/jpeg"

    def _parse_response(
        self,
        data: dict[str, Any],
        candidates: list[CandidateOwner],
    ) -> ClassificationResult:
        """Parse OpenAI API response into ClassificationResult."""
        try:
            content = data["choices"][0]["message"]["content"]

            json_match = re.search(r"\{[\s\S]*\}", content)
            parsed = json.loads(json_match.group()) if json_match else json.loads(content)

            # Pull any name_<code> / description_<code> keys back out into dicts.
            # We also accept legacy "name"/"description" (without suffix) as the
            # default-language value, in case the model omits the suffix.
            names: dict[str, str] = {}
            descriptions: dict[str, str] = {}
            for key, value in parsed.items():
                if not isinstance(value, str) or not value:
                    continue
                if key == "name":
                    names.setdefault(self.languages[0], value)
                elif key.startswith("name_"):
                    names[key.removeprefix("name_")] = value
                elif key == "description":
                    descriptions.setdefault(self.languages[0], value)
                elif key.startswith("description_"):
                    descriptions[key.removeprefix("description_")] = value

            tags = self._normalize_tags(parsed.get("tags", []))
            size = parsed.get("size") or ""
            seasonal = (parsed.get("seasonal") or "none").lower()
            valid_seasons = {"none", "spring", "summer", "fall", "winter", "holiday"}
            if seasonal not in valid_seasons:
                seasonal = "none"

            # Owner suggestion. Defensively validate the model's id
            # against the candidates we sent — models occasionally
            # hallucinate a UUID, and silently dropping that is safer
            # than persisting a dangling reference.
            suggested_owner_id: str | None = None
            owner_confidence = 0.0
            owner_reason: str | None = None
            if candidates:
                raw_id = parsed.get("suggested_owner_id")
                valid_ids = {c.id for c in candidates}
                if isinstance(raw_id, str) and raw_id in valid_ids:
                    suggested_owner_id = raw_id
                    owner_reason_raw = parsed.get("owner_reason")
                    if isinstance(owner_reason_raw, str) and owner_reason_raw.strip():
                        owner_reason = owner_reason_raw.strip()
                    try:
                        owner_confidence = float(parsed.get("owner_confidence", 0.0))
                    except (TypeError, ValueError):
                        owner_confidence = 0.0
                    owner_confidence = max(0.0, min(1.0, owner_confidence))

            return ClassificationResult(
                names=names,
                descriptions=descriptions,
                tags=tags,
                size=size,
                seasonal=seasonal,
                confidence=0.9,
                suggested_owner_id=suggested_owner_id,
                owner_confidence=owner_confidence,
                owner_reason=owner_reason,
                raw_response=data,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return ClassificationResult(
                tags=[],
                confidence=0.0,
                raw_response={"error": str(e), "raw": data},
            )
