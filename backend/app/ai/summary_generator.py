"""AI-powered summary generator for container labels."""

import json
import re
import time
from dataclasses import dataclass

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class ContainerItem:
    """Simplified item data for summary generation."""

    name: str
    description: str | None = None
    ai_description: str | None = None
    seasonal: str | None = None
    size: str | None = None
    owner_name: str | None = None


@dataclass
class SummaryResult:
    """Result of summary generation."""

    summary: str
    success: bool
    error: str | None = None
    # Populated when an actual OpenAI call was made (not the fallback);
    # callers use these to feed the ai_usage_log.
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    model: str = ""


SUMMARY_PROMPT = """You are generating a descriptive summary for a storage container label.
The summary should be 2-4 sentences that help identify what's in this container.

Container: "{container_name}"
Location: "{location_name}"
{owner_info}Items ({item_count} total):
{items_list}

Generate a HELPFUL summary (2-4 sentences, max {max_chars} characters) that:
1. If items belong to a specific person, START with their name (e.g., "Marte's summer clothes...")
2. Captures the MAIN CATEGORY or THEME of items
3. Mentions key details like season, size range, type, or notable items
4. Is useful for someone quickly scanning labels to find things

Examples of good summaries:
- "Marte's summer clothes and shoes. Dresses, sandals, and swimwear in sizes S-M."
- "Kids toys for ages 3-8. Board games, LEGO sets, and stuffed animals."
- "Christmas decorations. Tree ornaments, lights, and outdoor decorations."
- "Kitchen appliances. Mixer, blender, food processor, and accessories."
- "Winter sports gear. Ski boots (42), poles, goggles, and thermal layers."

Return ONLY the summary text, no quotes, no explanation.
"""


class SummaryGenerator:
    """Generates AI-powered summaries for container labels."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 150,
        temperature: float = 0.3,
        enabled: bool = True,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enabled = enabled
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_summary(
        self,
        container_name: str,
        location_name: str,
        items: list[ContainerItem],
        max_length: int = 300,
    ) -> SummaryResult:
        """Generate an AI summary for a container's contents.

        Args:
            container_name: Name of the container
            location_name: Name of the location
            items: List of items in the container
            max_length: Maximum character length for summary (default 300 for 2-4 sentences)

        Returns:
            SummaryResult with the generated summary
        """
        if not self.api_key or not self.enabled:
            # Fall back to simple summary if no API key or disabled
            return self._generate_fallback_summary(items, max_length)

        if not items:
            return SummaryResult(summary="Empty container", success=True)

        # Build items list for prompt
        items_list = self._format_items_for_prompt(items)

        # Determine owner info - check if most items have the same owner
        owner_info = self._get_owner_info(items)

        prompt = SUMMARY_PROMPT.format(
            container_name=container_name,
            location_name=location_name,
            owner_info=owner_info,
            item_count=len(items),
            items_list=items_list,
            max_chars=max_length,
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            latency_ms = int((time.monotonic() - start) * 1000)

            summary = data["choices"][0]["message"]["content"].strip()

            # Remove any quotes that might have been added
            summary = summary.strip('"\'')

            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[: max_length - 3] + "..."

            usage = data.get("usage", {}) or {}
            return SummaryResult(
                summary=summary,
                success=True,
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                completion_tokens=int(usage.get("completion_tokens") or 0),
                latency_ms=latency_ms,
                model=self.model,
            )

        except httpx.HTTPStatusError as e:
            return SummaryResult(
                summary=self._generate_fallback_summary(items, max_length).summary,
                success=False,
                error=f"API error: {e.response.status_code}",
            )
        except Exception as e:
            return SummaryResult(
                summary=self._generate_fallback_summary(items, max_length).summary,
                success=False,
                error=str(e),
            )

    def _get_owner_info(self, items: list[ContainerItem]) -> str:
        """Determine if items have a common owner and return info string."""
        owner_counts: dict[str, int] = {}
        for item in items:
            if item.owner_name:
                owner_counts[item.owner_name] = owner_counts.get(item.owner_name, 0) + 1

        if not owner_counts:
            return ""

        # Find the dominant owner (if any)
        dominant_owner = max(owner_counts, key=owner_counts.get)  # type: ignore
        dominant_count = owner_counts[dominant_owner]

        # If more than 50% of items belong to one person, mention them
        if dominant_count >= len(items) * 0.5:
            if len(owner_counts) == 1:
                return f"Owner: {dominant_owner} (all items)\n"
            else:
                other_owners = [o for o in owner_counts if o != dominant_owner]
                return f"Primary owner: {dominant_owner} ({dominant_count}/{len(items)} items). Other owners: {', '.join(other_owners)}\n"

        # Multiple owners, list them
        owners_list = ", ".join(f"{name} ({count})" for name, count in owner_counts.items())
        return f"Owners: {owners_list}\n"

    def _format_items_for_prompt(self, items: list[ContainerItem]) -> str:
        """Format items for the prompt, limiting to avoid token overflow."""
        lines = []
        for item in items[:20]:  # Limit to 20 items
            parts = [f"- {item.name}"]
            if item.owner_name:
                parts.append(f"(owner: {item.owner_name})")
            if item.size:
                parts.append(f"(size: {item.size})")
            if item.seasonal and item.seasonal != "none":
                parts.append(f"[{item.seasonal}]")
            if item.ai_description:
                # Add truncated AI description
                desc = item.ai_description[:50]
                if len(item.ai_description) > 50:
                    desc += "..."
                parts.append(f"- {desc}")
            lines.append(" ".join(parts))

        result = "\n".join(lines)
        if len(items) > 20:
            result += f"\n... and {len(items) - 20} more items"

        return result

    def _generate_fallback_summary(
        self, items: list[ContainerItem], max_length: int
    ) -> SummaryResult:
        """Generate a simple fallback summary without AI."""
        if not items:
            return SummaryResult(summary="Empty container", success=True)

        # Try to extract common themes
        seasonal_counts: dict[str, int] = {}
        names: list[str] = []

        for item in items:
            names.append(item.name)
            if item.seasonal and item.seasonal != "none":
                seasonal_counts[item.seasonal] = seasonal_counts.get(item.seasonal, 0) + 1

        # Check for dominant season
        if seasonal_counts:
            dominant_season = max(seasonal_counts, key=seasonal_counts.get)  # type: ignore
            if seasonal_counts[dominant_season] >= len(items) * 0.5:
                # More than half items are this season
                summary = f"{dominant_season.capitalize()} items: "
                remaining = max_length - len(summary)
                item_names = ", ".join(names[:3])
                if len(item_names) > remaining:
                    item_names = item_names[: remaining - 3] + "..."
                summary += item_names
                return SummaryResult(summary=summary, success=True)

        # Default: just list item names
        summary = ", ".join(names)
        if len(summary) > max_length:
            summary = summary[: max_length - 3] + "..."

        return SummaryResult(summary=summary, success=True)
