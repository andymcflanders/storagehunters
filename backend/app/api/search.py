"""Search API routes."""

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models.container import Container
from app.models.item import ConditionEnum, Item, ItemImage, ItemTag, SeasonalEnum
from app.models.location import Location
from app.models.tag import Tag
from app.schemas.search import PathElement, SearchResult, SearchResultItem
from app.services.image_storage import ImageStorageService

router = APIRouter()


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


@router.get("", response_model=SearchResult)
async def search_items(
    db: DbSession,
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
) -> SearchResult:
    """
    Search items with full-text search and filters.

    Searches across:
    - Item name
    - Item description
    - AI-generated tags on images
    - Manual tags
    """
    # Base query
    query = select(Item).options(
        selectinload(Item.images),
        selectinload(Item.item_tags).selectinload(ItemTag.tag),
    )

    conditions = []

    # Text search
    if q:
        search_term = f"%{q.lower()}%"

        # Search in item name and description
        text_conditions = [
            func.lower(Item.name).like(search_term),
            func.lower(Item.description).like(search_term),
        ]

        # Search in tags via subquery
        tag_subquery = (
            select(ItemTag.item_id)
            .join(Tag)
            .where(func.lower(Tag.name).like(search_term))
        )
        text_conditions.append(Item.id.in_(tag_subquery))

        # Search in AI tags on images via subquery
        ai_tag_subquery = (
            select(ItemImage.item_id)
            .where(ItemImage.ai_tags.any(search_term.replace("%", "")))
        )
        text_conditions.append(Item.id.in_(ai_tag_subquery))

        conditions.append(or_(*text_conditions))

    # Owner filter
    if owner:
        conditions.append(Item.owner_id == owner)

    # Location filter (requires join through container)
    if location:
        container_subquery = (
            select(Container.id)
            .where(Container.location_id == location)
        )
        conditions.append(Item.container_id.in_(container_subquery))

    # Container filter
    if container:
        conditions.append(Item.container_id == container)

    # Size filter
    if size:
        conditions.append(func.lower(Item.size) == size.lower())

    # Condition filter
    if condition:
        conditions.append(Item.condition == condition)

    # Seasonal filter
    if seasonal:
        conditions.append(Item.seasonal == seasonal)

    # Tags filter
    if tags:
        tag_names = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if tag_names:
            # Items must have ALL specified tags
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

    # Get total count before pagination
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(Item.name).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    items = result.scalars().all()

    # Build response
    storage = ImageStorageService()
    search_results = []

    for item in items:
        # Get path
        path = await build_item_search_path(item, db)

        # Get thumbnail (first image)
        thumbnail_url = None
        if item.images:
            thumbnail_url = storage.get_url(item.images[0].filepath)

        # Get matching tags
        matching_tags = []
        if q:
            search_lower = q.lower()
            for it in item.item_tags:
                if search_lower in it.tag.name.lower():
                    matching_tags.append(it.tag.name)
            for img in item.images:
                if img.ai_tags:
                    for ai_tag in img.ai_tags:
                        if search_lower in ai_tag.lower() and ai_tag not in matching_tags:
                            matching_tags.append(ai_tag)

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
                matching_tags=matching_tags[:5],  # Limit to 5 matching tags
            )
        )

    return SearchResult(
        query=q,
        total=total,
        items=search_results,
    )
