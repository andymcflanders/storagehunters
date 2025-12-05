"""AI-powered semantic search service for intelligent query understanding."""

import json
import re
from dataclasses import dataclass, field

import httpx

from app.config import get_settings

settings = get_settings()

# Color synonyms for semantic matching
COLOR_SYNONYMS = {
    "red": ["crimson", "scarlet", "ruby", "maroon", "burgundy", "cherry", "vermillion"],
    "blue": ["navy", "azure", "cobalt", "sapphire", "indigo", "teal", "cyan", "cerulean", "sky"],
    "green": ["emerald", "olive", "lime", "sage", "mint", "forest", "jade", "hunter", "teal"],
    "yellow": ["gold", "golden", "mustard", "lemon", "amber", "canary", "blonde"],
    "orange": ["tangerine", "peach", "coral", "rust", "amber", "apricot"],
    "purple": ["violet", "lavender", "plum", "lilac", "mauve", "magenta", "grape"],
    "pink": ["rose", "salmon", "coral", "fuchsia", "magenta", "blush", "hot pink"],
    "brown": ["tan", "beige", "chocolate", "caramel", "coffee", "mocha", "bronze", "chestnut"],
    "black": ["ebony", "onyx", "jet", "charcoal", "dark"],
    "white": ["ivory", "cream", "off-white", "pearl", "snow", "eggshell"],
    "gray": ["grey", "silver", "charcoal", "slate", "ash", "graphite"],
}

# Clothing type synonyms
CLOTHING_SYNONYMS = {
    "sweater": ["cardigan", "pullover", "jumper", "knit", "sweatshirt", "hoodie"],
    "jacket": ["coat", "blazer", "windbreaker", "parka", "anorak", "vest"],
    "pants": ["trousers", "jeans", "slacks", "chinos", "leggings", "joggers"],
    "shirt": ["blouse", "top", "tee", "t-shirt", "button-down", "polo"],
    "dress": ["gown", "frock", "sundress", "maxi", "midi"],
    "shoes": ["sneakers", "boots", "sandals", "heels", "flats", "loafers", "trainers"],
    "hat": ["cap", "beanie", "beret", "fedora", "bonnet"],
    "skirt": ["mini", "maxi", "midi", "a-line", "pencil"],
}


@dataclass
class ParsedQuery:
    """Parsed search query with extracted attributes."""

    original_query: str
    search_terms: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    color_synonyms: list[str] = field(default_factory=list)
    item_types: list[str] = field(default_factory=list)
    type_synonyms: list[str] = field(default_factory=list)
    sizes: list[str] = field(default_factory=list)
    owner_names: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    seasons: list[str] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    all_search_terms: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Build complete search term list."""
        self._build_all_terms()

    def _build_all_terms(self):
        """Combine all terms for searching."""
        terms = set(self.search_terms)
        terms.update(self.colors)
        terms.update(self.color_synonyms)
        terms.update(self.item_types)
        terms.update(self.type_synonyms)
        terms.update(self.sizes)
        terms.update(self.materials)
        terms.update(self.brands)
        self.all_search_terms = list(terms)


class SemanticSearchService:
    """AI-powered semantic search for understanding natural language queries."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.openai_api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def parse_query(self, query: str) -> ParsedQuery:
        """
        Parse a natural language search query and extract structured attributes.

        Examples:
        - "emerald cardigan" → colors=["green"], color_synonyms=["emerald"], types=["sweater", "cardigan"]
        - "Sonja's red dress size 104" → owner=["Sonja"], colors=["red"], types=["dress"], sizes=["104"]
        """
        # First, do local synonym expansion
        parsed = self._local_parse(query)

        # If we have an API key, enhance with AI
        if self.api_key:
            try:
                ai_parsed = await self._ai_parse(query)
                parsed = self._merge_parsed(parsed, ai_parsed)
            except Exception:
                # Fall back to local parsing if AI fails
                pass

        return parsed

    def _local_parse(self, query: str) -> ParsedQuery:
        """Parse query using local synonym dictionaries."""
        query_lower = query.lower()
        words = re.findall(r"[\w']+", query_lower)

        colors = []
        color_synonyms = []
        item_types = []
        type_synonyms = []
        sizes = []
        owner_names = []

        # Extract colors and their synonyms
        for word in words:
            # Check if it's a main color
            if word in COLOR_SYNONYMS:
                colors.append(word)
                color_synonyms.extend(COLOR_SYNONYMS[word])
            else:
                # Check if it's a color synonym
                for main_color, syns in COLOR_SYNONYMS.items():
                    if word in syns:
                        colors.append(main_color)
                        color_synonyms.append(word)
                        color_synonyms.extend([s for s in syns if s != word])
                        break

        # Extract clothing types and synonyms
        for word in words:
            if word in CLOTHING_SYNONYMS:
                item_types.append(word)
                type_synonyms.extend(CLOTHING_SYNONYMS[word])
            else:
                for main_type, syns in CLOTHING_SYNONYMS.items():
                    if word in syns:
                        item_types.append(main_type)
                        type_synonyms.append(word)
                        type_synonyms.extend([s for s in syns if s != word])
                        break

        # Extract sizes (numeric patterns like "104", "XL", "M", "size 10")
        size_patterns = re.findall(r"\b(?:size\s*)?(\d+(?:[/-]\d+)?|xs|s|m|l|xl|xxl|xxxl)\b", query_lower)
        sizes = list(set(size_patterns))

        # Extract possessive owner names (e.g., "Sonja's", "Mom's")
        possessive_pattern = re.findall(r"(\w+)(?:'s|s')\s", query, re.IGNORECASE)
        owner_names = [name.capitalize() for name in possessive_pattern]

        # All remaining words are general search terms
        search_terms = words

        return ParsedQuery(
            original_query=query,
            search_terms=search_terms,
            colors=list(set(colors)),
            color_synonyms=list(set(color_synonyms)),
            item_types=list(set(item_types)),
            type_synonyms=list(set(type_synonyms)),
            sizes=sizes,
            owner_names=owner_names,
        )

    async def _ai_parse(self, query: str) -> ParsedQuery:
        """Use AI to parse complex queries and generate synonyms."""
        prompt = f"""Analyze this search query for a home inventory/storage system and extract structured information.

Query: "{query}"

Return a JSON object with these fields:
{{
  "search_terms": ["main", "search", "words"],
  "colors": ["identified colors, normalized to basic color names"],
  "color_synonyms": ["related color terms that might match"],
  "item_types": ["type of item being searched for"],
  "type_synonyms": ["related item types that might match"],
  "sizes": ["any size information mentioned"],
  "owner_names": ["any person names mentioned as owners"],
  "materials": ["any materials mentioned"],
  "seasons": ["any seasonal references"],
  "brands": ["any brand names mentioned"]
}}

Examples:
- "emerald cardigan" → colors: ["green"], color_synonyms: ["emerald", "teal", "jade"], item_types: ["sweater"], type_synonyms: ["cardigan", "pullover", "knit"]
- "Sonja's red dress in size 104" → owner_names: ["Sonja"], colors: ["red"], item_types: ["dress"], sizes: ["104"]
- "winter boots" → seasons: ["winter"], item_types: ["boots"], type_synonyms: ["shoes", "footwear"]

Think about what terms someone might have used when cataloging this item. Be generous with synonyms.
Return ONLY the JSON object."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Parse response
        content = data["choices"][0]["message"]["content"]
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(content)

        return ParsedQuery(
            original_query=query,
            search_terms=parsed.get("search_terms", []),
            colors=parsed.get("colors", []),
            color_synonyms=parsed.get("color_synonyms", []),
            item_types=parsed.get("item_types", []),
            type_synonyms=parsed.get("type_synonyms", []),
            sizes=parsed.get("sizes", []),
            owner_names=parsed.get("owner_names", []),
            materials=parsed.get("materials", []),
            seasons=parsed.get("seasons", []),
            brands=parsed.get("brands", []),
        )

    def _merge_parsed(self, local: ParsedQuery, ai: ParsedQuery) -> ParsedQuery:
        """Merge local and AI parsing results."""
        return ParsedQuery(
            original_query=local.original_query,
            search_terms=list(set(local.search_terms + ai.search_terms)),
            colors=list(set(local.colors + ai.colors)),
            color_synonyms=list(set(local.color_synonyms + ai.color_synonyms)),
            item_types=list(set(local.item_types + ai.item_types)),
            type_synonyms=list(set(local.type_synonyms + ai.type_synonyms)),
            sizes=list(set(local.sizes + ai.sizes)),
            owner_names=list(set(local.owner_names + ai.owner_names)),
            materials=ai.materials,
            seasons=ai.seasons,
            brands=ai.brands,
        )


def get_semantic_search_service() -> SemanticSearchService:
    """Get semantic search service instance."""
    return SemanticSearchService()
