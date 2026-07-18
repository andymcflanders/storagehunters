"""Search API routes with AI-powered semantic search."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import Text, and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.container import Container
from app.models.item import ConditionEnum, Item, ItemImage, ItemTag, SeasonalEnum
from app.models.location import Location
from app.models.tag import Tag
from app.models.user import User
from app.schemas.search import PathElement, SearchResult, SearchResultItem
from app.services.image_storage import ImageStorageService
from app.services.semantic_search import get_semantic_search_service

router = APIRouter()


@router.get("/autocomplete", response_model=SearchResult)
async def autocomplete_items(
    db: DbSession,
    current_user: CurrentUser,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(8, le=20, description="Max results"),
) -> SearchResult:
    """
    Fast autocomplete search for instant suggestions.

    Skips AI semantic parsing for speed - uses only local matching.
    Optimized for low latency autocomplete dropdowns.
    """
    search_term = f"%{q.lower()}%"

    # Simple query with minimal joins for speed.
    # JSONB-cast match on ai_names/ai_descriptions catches Norwegian (and
    # any other supported language) translations without enumerating
    # languages here.
    query = (
        select(Item)
        .options(selectinload(Item.images))
        .where(
            or_(
                func.lower(Item.name).like(search_term),
                func.lower(Item.description).like(search_term),
                func.lower(func.cast(Item.ai_names, Text)).like(search_term),
                func.lower(func.cast(Item.ai_descriptions, Text)).like(search_term),
            )
        )
        .limit(limit)
    )

    result = await db.execute(query)
    items = result.scalars().all()

    # Build response with minimal processing
    storage = ImageStorageService()
    search_results = []

    for item in items:
        # Get path efficiently
        path = await build_item_search_path(item, db)

        # Get thumbnail
        thumbnail_url = None
        if item.images:
            thumbnail_url = storage.get_url(item.images[0].filepath)

        search_results.append(
            SearchResultItem(
                id=item.id,
                name=item.name,
                description=item.description,
                container_id=item.container_id,
                owner_id=item.owner_id,
                size=item.size,
                condition=item.condition,
                seasonal=item.seasonal,
                value_estimate=item.value_estimate,
                created_at=item.created_at,
                updated_at=item.updated_at,
                path=path,
                thumbnail_url=thumbnail_url,
                matching_tags=[],
            )
        )

    return SearchResult(
        query=q,
        total=len(search_results),
        items=search_results,
    )


@dataclass
class ScoredItem:
    """Item with relevance score."""

    item: Item
    score: float
    match_type: str  # "exact", "similar", "semantic"
    matched_terms: list[str]


async def build_item_search_path(item: Item, db) -> list[PathElement]:
    """Build the path for a search result item."""
    path = []

    # Get container
    result = await db.execute(
        select(Container).where(Container.id == item.container_id)
    )
    container = result.scalar_one()

    # Get location
    result = await db.execute(
        select(Location).where(Location.id == container.location_id)
    )
    location = result.scalar_one()
    path.append(PathElement(id=location.id, name=location.name, type="location"))

    # Build container path
    container_path = []
    current = container
    while current:
        container_path.append(
            PathElement(id=current.id, name=current.name, type="container")
        )
        if current.parent_container_id:
            result = await db.execute(
                select(Container).where(Container.id == current.parent_container_id)
            )
            current = result.scalar_one_or_none()
        else:
            break

    path.extend(reversed(container_path))
    return path


def calculate_relevance_score(
    item: Item,
    original_query: str,
    parsed_colors: list[str],
    parsed_color_synonyms: list[str],
    parsed_types: list[str],
    parsed_type_synonyms: list[str],
    parsed_sizes: list[str],
    parsed_owner_names: list[str],
    all_search_terms: list[str],
) -> ScoredItem:
    """
    Calculate relevance score for an item based on query matching.

    AI-generated translations (ai_names, ai_descriptions) are ranked
    alongside the manual fields — the Norwegian translation of an item
    is just as canonical as the English one, so a match in either
    should earn the same score.

    Scoring:
    - Exact match in name (any language): 100 points
    - Exact match in description (any language): 50 points
    - Original color match: 30 points
    - Color synonym match: 20 points
    - Original type match: 30 points
    - Type synonym match: 20 points
    - Size match: 25 points
    - Owner match: 40 points
    - Tag match: 15 points per tag
    - AI tag match: 10 points per tag
    """
    score = 0.0
    matched_terms = []
    match_type = "semantic"
    query_lower = original_query.lower()

    # Manual fields
    name_lower = item.name.lower()
    desc_lower = (item.description or "").lower()
    size_lower = (item.size or "").lower()

    # AI translations — flatten the JSONB dicts to lowercased strings.
    ai_names = [v.lower() for v in (item.ai_names or {}).values() if v]
    ai_descs = [v.lower() for v in (item.ai_descriptions or {}).values() if v]

    # Treat manual + AI names as one "name haystack". Same for description.
    name_haystack = " ".join([name_lower, *ai_names])
    desc_haystack = " ".join([desc_lower, *ai_descs])

    # Get all tags
    item_tags = []
    for it in item.item_tags:
        item_tags.append(it.tag.name.lower())

    ai_tags = []
    for img in item.images:
        if img.ai_tags:
            ai_tags.extend([t.lower() for t in img.ai_tags])

    all_item_text = " ".join([
        name_haystack,
        desc_haystack,
        " ".join(item_tags),
        " ".join(ai_tags),
    ])

    # Exact query match in name (highest priority)
    if query_lower in name_haystack:
        score += 100
        matched_terms.append(f"name:{original_query}")
        match_type = "exact"
    elif query_lower in desc_haystack:
        score += 50
        matched_terms.append(f"description:{original_query}")
        match_type = "exact"

    # Color matching
    for color in parsed_colors:
        if color in name_haystack or color in desc_haystack:
            score += 30
            matched_terms.append(f"color:{color}")
            if match_type != "exact":
                match_type = "similar"
        elif color in all_item_text:
            score += 20
            matched_terms.append(f"color:{color}")

    for color_syn in parsed_color_synonyms:
        if color_syn in all_item_text:
            score += 15
            matched_terms.append(f"color_synonym:{color_syn}")

    # Item type matching
    for item_type in parsed_types:
        if item_type in name_haystack or item_type in desc_haystack:
            score += 30
            matched_terms.append(f"type:{item_type}")
            if match_type != "exact":
                match_type = "similar"
        elif item_type in all_item_text:
            score += 20
            matched_terms.append(f"type:{item_type}")

    for type_syn in parsed_type_synonyms:
        if type_syn in all_item_text:
            score += 15
            matched_terms.append(f"type_synonym:{type_syn}")

    # Size matching
    for size in parsed_sizes:
        size_low = size.lower()
        if size_low == size_lower or size_low in name_haystack or size_low in desc_haystack:
            score += 25
            matched_terms.append(f"size:{size}")
            if match_type != "exact":
                match_type = "similar"

    # Owner matching
    if parsed_owner_names and item.owner:
        owner_name_lower = item.owner.name.lower()
        for owner in parsed_owner_names:
            if owner.lower() in owner_name_lower or owner_name_lower in owner.lower():
                score += 40
                matched_terms.append(f"owner:{owner}")
                if match_type != "exact":
                    match_type = "similar"

    # Tag matching (both manual and AI tags)
    for term in all_search_terms:
        term_lower = term.lower()
        for tag in item_tags:
            if term_lower in tag or tag in term_lower:
                score += 15
                matched_terms.append(f"tag:{tag}")
        for ai_tag in ai_tags:
            if term_lower in ai_tag or ai_tag in term_lower:
                score += 10
                matched_terms.append(f"ai_tag:{ai_tag}")

    # Bonus for multiple matches
    if len(matched_terms) > 3:
        score *= 1.2

    return ScoredItem(
        item=item,
        score=score,
        match_type=match_type,
        matched_terms=list(set(matched_terms))[:10],  # Limit to 10 unique matches
    )


@router.get("", response_model=SearchResult)
async def search_items(
    db: DbSession,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Search query"),
    owner: UUID | None = Query(None, description="Filter by owner ID"),
    location: UUID | None = Query(None, description="Filter by location ID"),
    container: UUID | None = Query(None, description="Filter by container ID"),
    size: str | None = Query(None, description="Filter by size"),
    condition: ConditionEnum | None = Query(None, description="Filter by condition"),
    seasonal: SeasonalEnum | None = Query(None, description="Filter by season"),
    tags: str | None = Query(None, description="Comma-separated tag names"),
    limit: int = Query(50, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    smart_search: bool = Query(True, description="Enable AI-powered semantic search"),
) -> SearchResult:
    """
    Search items with AI-powered semantic understanding.

    Features:
    - Understands color synonyms (emerald → green, cardigan → sweater)
    - Parses natural language queries (Sonja's red dress in size 104)
    - Ranks results by relevance (exact matches first, then similar, then semantic)

    Searches across:
    - Item name and description (manual + AI translations in any language)
    - Manual tags
    - AI-generated tags on images
    - Owner names
    - Size information
    """
    # Base query - load all relationships we need for scoring
    query = select(Item).options(
        selectinload(Item.images),
        selectinload(Item.item_tags).selectinload(ItemTag.tag),
        selectinload(Item.owner),
    )

    conditions = []

    # Parse query with semantic search
    parsed_query = None
    if q and smart_search:
        search_service = get_semantic_search_service()
        parsed_query = await search_service.parse_query(q)

        # Build expanded search conditions
        search_conditions = []

        # All terms to search (original + synonyms)
        all_terms = set()
        all_terms.update(t.lower() for t in parsed_query.search_terms)
        all_terms.update(t.lower() for t in parsed_query.colors)
        all_terms.update(t.lower() for t in parsed_query.color_synonyms)
        all_terms.update(t.lower() for t in parsed_query.item_types)
        all_terms.update(t.lower() for t in parsed_query.type_synonyms)
        all_terms.update(t.lower() for t in parsed_query.materials)
        all_terms.update(t.lower() for t in parsed_query.brands)

        for term in all_terms:
            if len(term) < 2:
                continue
            search_term = f"%{term}%"

            # Search in name and description (manual + AI translations).
            search_conditions.append(func.lower(Item.name).like(search_term))
            search_conditions.append(func.lower(Item.description).like(search_term))
            search_conditions.append(
                func.lower(func.cast(Item.ai_names, Text)).like(search_term)
            )
            search_conditions.append(
                func.lower(func.cast(Item.ai_descriptions, Text)).like(search_term)
            )

            # Search in tags
            tag_subquery = (
                select(ItemTag.item_id)
                .join(Tag)
                .where(func.lower(Tag.name).like(search_term))
            )
            search_conditions.append(Item.id.in_(tag_subquery))

            # Search in AI tags
            ai_tag_subquery = (
                select(ItemImage.item_id)
                .where(ItemImage.ai_tags.any(term))
            )
            search_conditions.append(Item.id.in_(ai_tag_subquery))

        # Size filter from parsed query
        for parsed_size in parsed_query.sizes:
            search_conditions.append(func.lower(Item.size).like(f"%{parsed_size.lower()}%"))

        # Owner filter from parsed query
        if parsed_query.owner_names:
            for owner_name in parsed_query.owner_names:
                owner_subquery = (
                    select(User.id)
                    .where(func.lower(User.name).like(f"%{owner_name.lower()}%"))
                )
                search_conditions.append(Item.owner_id.in_(owner_subquery))

        # Season filter from parsed query
        season_map = {
            "winter": SeasonalEnum.WINTER,
            "summer": SeasonalEnum.SUMMER,
            "spring": SeasonalEnum.SPRING,
            "fall": SeasonalEnum.FALL,
            "autumn": SeasonalEnum.FALL,
            "holiday": SeasonalEnum.HOLIDAY,
        }
        for season in parsed_query.seasons:
            if season.lower() in season_map:
                search_conditions.append(Item.seasonal == season_map[season.lower()])

        if search_conditions:
            conditions.append(or_(*search_conditions))

    elif q:
        # Simple search fallback
        search_term = f"%{q.lower()}%"
        text_conditions = [
            func.lower(Item.name).like(search_term),
            func.lower(Item.description).like(search_term),
            func.lower(func.cast(Item.ai_names, Text)).like(search_term),
            func.lower(func.cast(Item.ai_descriptions, Text)).like(search_term),
        ]

        tag_subquery = (
            select(ItemTag.item_id)
            .join(Tag)
            .where(func.lower(Tag.name).like(search_term))
        )
        text_conditions.append(Item.id.in_(tag_subquery))

        ai_tag_subquery = (
            select(ItemImage.item_id)
            .where(ItemImage.ai_tags.any(search_term.replace("%", "")))
        )
        text_conditions.append(Item.id.in_(ai_tag_subquery))

        conditions.append(or_(*text_conditions))

    # Explicit filter parameters (override parsed query)
    if owner:
        conditions.append(Item.owner_id == owner)

    if location:
        container_subquery = (
            select(Container.id)
            .where(Container.location_id == location)
        )
        conditions.append(Item.container_id.in_(container_subquery))

    if container:
        conditions.append(Item.container_id == container)

    if size:
        conditions.append(func.lower(Item.size) == size.lower())

    if condition:
        conditions.append(Item.condition == condition)

    if seasonal:
        conditions.append(Item.seasonal == seasonal)

    if tags:
        tag_names = [t.strip().lower() for t in tags.split(",") if t.strip()]
        for tag_name in tag_names:
            tag_subquery = (
                select(ItemTag.item_id)
                .join(Tag)
                .where(func.lower(Tag.name) == tag_name)
            )
            conditions.append(Item.id.in_(tag_subquery))

    # Apply conditions
    if conditions:
        query = query.where(and_(*conditions))

    # Execute query (get all matching items for scoring)
    result = await db.execute(query)
    items = result.scalars().all()

    # Score and rank results
    scored_items: list[ScoredItem] = []

    if q and parsed_query:
        for item in items:
            scored = calculate_relevance_score(
                item=item,
                original_query=q,
                parsed_colors=parsed_query.colors,
                parsed_color_synonyms=parsed_query.color_synonyms,
                parsed_types=parsed_query.item_types,
                parsed_type_synonyms=parsed_query.type_synonyms,
                parsed_sizes=parsed_query.sizes,
                parsed_owner_names=parsed_query.owner_names,
                all_search_terms=parsed_query.all_search_terms,
            )
            if scored.score > 0:
                scored_items.append(scored)

        # Sort by score descending
        scored_items.sort(key=lambda x: (-x.score, x.item.name))
    else:
        # No query, just return items sorted by name
        scored_items = [
            ScoredItem(item=item, score=0, match_type="none", matched_terms=[])
            for item in items
        ]
        scored_items.sort(key=lambda x: x.item.name)

    # Get total count
    total = len(scored_items)

    # Apply pagination
    paginated_items = scored_items[offset : offset + limit]

    # Build response
    storage = ImageStorageService()
    search_results = []

    for scored in paginated_items:
        item = scored.item

        # Get path
        path = await build_item_search_path(item, db)

        # Get thumbnail
        thumbnail_url = None
        if item.images:
            thumbnail_url = storage.get_url(item.images[0].filepath)

        # Get matching terms for display
        matching_tags = []
        if scored.matched_terms:
            for term in scored.matched_terms[:5]:
                # Extract just the value part
                if ":" in term:
                    matching_tags.append(term.split(":", 1)[1])
                else:
                    matching_tags.append(term)

        search_results.append(
            SearchResultItem(
                id=item.id,
                name=item.name,
                description=item.description,
                container_id=item.container_id,
                owner_id=item.owner_id,
                size=item.size,
                condition=item.condition,
                seasonal=item.seasonal,
                value_estimate=item.value_estimate,
                created_at=item.created_at,
                updated_at=item.updated_at,
                path=path,
                thumbnail_url=thumbnail_url,
                matching_tags=list(set(matching_tags)),
            )
        )

    return SearchResult(
        query=q,
        total=total,
        items=search_results,
    )
