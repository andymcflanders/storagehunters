"""Text-only size → age inference for the /outgrown backfill action.

Calls the cheap text model (gpt-4o-mini by default) with just a size
string. Used by the admin "recompute size age ranges" action that
backfills existing items so /outgrown can surface them — much cheaper
than re-running the vision classifier with images.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass

import httpx


SIZE_AGE_PROMPT_TEMPLATE = """A children's clothing or footwear size is "{size}".

Return JSON with the age range (in MONTHS) this size typically fits a child:
{{
  "size_age_min_months": <int or null>,
  "size_age_max_months": <int or null>
}}

Reference (children's height-cm clothing):
56=0-2mo, 62=2-4mo, 68=4-6mo, 74=6-9mo, 80=9-12mo, 86=12-18mo,
92=18-24mo, 98=24-36mo, 104=36-48mo, 110=48-60mo, 116=60-72mo,
122=72-84mo, 128=84-96mo, 134=96-108mo, 140=108-120mo

Reference (children's EU shoe sizes):
20=12-18mo, 24=24-36mo, 28=48-60mo, 32=72-84mo, 36=108-120mo

Return BOTH null for adult sizes, ambiguous letter sizes (S/M/L/XL),
or anything you can't confidently age-map.

Return ONLY the JSON, no other text."""


@dataclass
class SizeAgeResult:
    """Output of `infer_size_age_range`. Carries token counts so the
    caller can log usage even when the AI couldn't map the size."""

    min_months: int | None
    max_months: int | None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


async def infer_size_age_range(
    size: str,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> SizeAgeResult:
    """Infer the age range a size implies. Returns a SizeAgeResult.

    `min_months` and `max_months` are None when inference fails or
    the AI returns null — caller should leave the item's columns
    alone in that case rather than overwriting with a maybe-wrong
    guess.
    """
    if not size or not size.strip() or not api_key:
        return SizeAgeResult(min_months=None, max_months=None)

    prompt = SIZE_AGE_PROMPT_TEMPLATE.format(size=size.strip())

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        latency_ms = int((time.monotonic() - start) * 1000)

        content = data["choices"][0]["message"]["content"]
        json_match = re.search(r"\{[\s\S]*\}", content)
        parsed = json.loads(json_match.group()) if json_match else json.loads(content)

        from app.ai.openai_vision import _parse_age_months

        lo = _parse_age_months(parsed.get("size_age_min_months"))
        hi = _parse_age_months(parsed.get("size_age_max_months"))
        usage = data.get("usage", {}) or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        if lo is None or hi is None or lo > hi:
            return SizeAgeResult(
                min_months=None,
                max_months=None,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
            )
        return SizeAgeResult(
            min_months=lo,
            max_months=hi,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )

    except Exception:
        # Network blip / parse error / quota — caller will skip and
        # try again next backfill. Returns no token counts since we
        # don't know how far the call got.
        return SizeAgeResult(min_months=None, max_months=None)
