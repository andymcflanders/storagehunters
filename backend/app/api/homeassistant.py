"""Home Assistant integration API routes.

This module provides a clean, stable API designed specifically for Home Assistant
integration. All endpoints use API key authentication and are optimized for
sensor data and automations.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import Text, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import APIUser, DbSession, require_scope
from app.models.api_key import APIKeyScope
from app.models.container import Container
from app.models.item import Item, ItemImage, ItemTag
from app.models.location import Location
from app.models.reminder import Reminder, ReminderType
from app.models.tag import Tag
from app.models.user import User

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class SystemStatus(BaseModel):
    """System status for Home Assistant discovery."""

    status: str = "online"
    version: str = "1.0.0"
    api_version: str = "v1"
    name: str = "StorageHub"


class InventoryStats(BaseModel):
    """Inventory statistics for Home Assistant sensors."""

    total_locations: int
    total_containers: int
    total_items: int
    total_photos: int
    total_tags: int
    items_needing_review: int
    items_by_condition: dict[str, int]
    items_by_season: dict[str, int]
    last_updated: datetime


class ReminderSummary(BaseModel):
    """Reminder summary for Home Assistant sensors."""

    total_reminders: int
    pending_reminders: int
    overdue_reminders: int
    due_today: int
    due_this_week: int
    reminders_by_type: dict[str, int]


class ReminderItem(BaseModel):
    """Single reminder for Home Assistant."""

    id: UUID
    title: str
    reminder_type: str
    due_date: datetime
    is_overdue: bool
    item_name: str | None = None
    container_name: str | None = None


class LocationSummary(BaseModel):
    """Location summary for Home Assistant."""

    id: UUID
    name: str
    description: str | None
    container_count: int
    item_count: int


class ContainerSummary(BaseModel):
    """Container summary for Home Assistant."""

    id: UUID
    name: str
    qr_code: str
    location_name: str | None
    item_count: int
    child_container_count: int


class ItemSummary(BaseModel):
    """Item summary for Home Assistant."""

    id: UUID
    name: str
    description: str | None
    container_name: str | None
    location_name: str | None
    condition: str | None
    seasonal: str | None
    value_estimate: float | None
    owner_name: str | None
    primary_image_url: str | None
    tags: list[str]


class SearchResult(BaseModel):
    """Search result for Home Assistant."""

    items: list[ItemSummary]
    total_count: int
    query: str


class RecentActivity(BaseModel):
    """Recent activity for Home Assistant."""

    action: str
    entity_type: str
    entity_name: str
    user_name: str
    timestamp: datetime


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/status", response_model=SystemStatus)
async def get_status() -> SystemStatus:
    """Get system status.

    This endpoint does not require authentication and can be used
    for Home Assistant discovery and health checks.
    """
    return SystemStatus()


@router.get("/stats", response_model=InventoryStats)
async def get_inventory_stats(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> InventoryStats:
    """Get comprehensive inventory statistics.

    Use this endpoint to create Home Assistant sensors for:
    - Total items in inventory
    - Items by condition
    - Items by season
    - Storage utilization
    """
    user, api_key = api_user

    # Basic counts
    locations_count = await db.scalar(select(func.count(Location.id))) or 0
    containers_count = await db.scalar(select(func.count(Container.id))) or 0
    items_count = await db.scalar(select(func.count(Item.id))) or 0
    photos_count = await db.scalar(select(func.count(ItemImage.id))) or 0
    tags_count = await db.scalar(select(func.count(Tag.id))) or 0

    # Items needing review
    needs_review_count = await db.scalar(
        select(func.count(Item.id)).where(Item.needs_review == True)
    ) or 0

    # Items by condition
    condition_result = await db.execute(
        select(Item.condition, func.count(Item.id))
        .where(Item.condition.isnot(None))
        .group_by(Item.condition)
    )
    items_by_condition = {
        str(row[0]): row[1] for row in condition_result.all()
    }

    # Items by season
    season_result = await db.execute(
        select(Item.seasonal, func.count(Item.id))
        .where(Item.seasonal.isnot(None))
        .group_by(Item.seasonal)
    )
    items_by_season = {
        str(row[0]): row[1] for row in season_result.all()
    }

    return InventoryStats(
        total_locations=locations_count,
        total_containers=containers_count,
        total_items=items_count,
        total_photos=photos_count,
        total_tags=tags_count,
        items_needing_review=needs_review_count,
        items_by_condition=items_by_condition,
        items_by_season=items_by_season,
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/reminders", response_model=ReminderSummary)
async def get_reminder_summary(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> ReminderSummary:
    """Get reminder summary for Home Assistant sensors.

    Create sensors for:
    - Overdue reminders count
    - Reminders due today
    - Pending reminders by type
    """
    user, api_key = api_user
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    week_end = today_start.replace(day=today_start.day + 7)

    # Total reminders
    total = await db.scalar(
        select(func.count(Reminder.id)).where(Reminder.is_completed == False)
    ) or 0

    # Pending (not completed, not overdue)
    pending = await db.scalar(
        select(func.count(Reminder.id))
        .where(Reminder.is_completed == False)
        .where(Reminder.due_date >= now)
    ) or 0

    # Overdue
    overdue = await db.scalar(
        select(func.count(Reminder.id))
        .where(Reminder.is_completed == False)
        .where(Reminder.due_date < now)
    ) or 0

    # Due today
    due_today = await db.scalar(
        select(func.count(Reminder.id))
        .where(Reminder.is_completed == False)
        .where(Reminder.due_date >= today_start)
        .where(Reminder.due_date <= today_end)
    ) or 0

    # Due this week
    due_week = await db.scalar(
        select(func.count(Reminder.id))
        .where(Reminder.is_completed == False)
        .where(Reminder.due_date >= today_start)
        .where(Reminder.due_date <= week_end)
    ) or 0

    # By type
    type_result = await db.execute(
        select(Reminder.reminder_type, func.count(Reminder.id))
        .where(Reminder.is_completed == False)
        .group_by(Reminder.reminder_type)
    )
    reminders_by_type = {
        row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1]
        for row in type_result.all()
    }

    return ReminderSummary(
        total_reminders=total,
        pending_reminders=pending,
        overdue_reminders=overdue,
        due_today=due_today,
        due_this_week=due_week,
        reminders_by_type=reminders_by_type,
    )


@router.get("/reminders/list", response_model=list[ReminderItem])
async def list_reminders(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
    include_completed: bool = False,
    limit: int = Query(default=20, le=100),
) -> list[ReminderItem]:
    """List reminders for Home Assistant notifications.

    Use this to create automations that notify about upcoming or overdue items.
    """
    user, api_key = api_user
    now = datetime.now(timezone.utc)

    query = select(Reminder).options(
        selectinload(Reminder.item),
        selectinload(Reminder.container),
    )

    if not include_completed:
        query = query.where(Reminder.is_completed == False)

    query = query.order_by(Reminder.due_date).limit(limit)
    result = await db.execute(query)
    reminders = result.scalars().all()

    return [
        ReminderItem(
            id=r.id,
            title=r.title,
            reminder_type=r.reminder_type.value if hasattr(r.reminder_type, 'value') else str(r.reminder_type),
            due_date=r.due_date,
            is_overdue=r.due_date < now,
            item_name=r.item.name if r.item else None,
            container_name=r.container.name if r.container else None,
        )
        for r in reminders
    ]


@router.get("/locations", response_model=list[LocationSummary])
async def list_locations(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> list[LocationSummary]:
    """List all locations with summary information.

    Use for Home Assistant to display storage locations and their utilization.
    """
    user, api_key = api_user

    result = await db.execute(
        select(Location).order_by(Location.sort_order, Location.name)
    )
    locations = result.scalars().all()

    summaries = []
    for loc in locations:
        container_count = await db.scalar(
            select(func.count(Container.id))
            .where(Container.location_id == loc.id)
        ) or 0

        item_count = await db.scalar(
            select(func.count(Item.id))
            .join(Container)
            .where(Container.location_id == loc.id)
        ) or 0

        summaries.append(LocationSummary(
            id=loc.id,
            name=loc.name,
            description=loc.description,
            container_count=container_count,
            item_count=item_count,
        ))

    return summaries


@router.get("/locations/{location_id}", response_model=LocationSummary)
async def get_location(
    location_id: UUID,
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> LocationSummary:
    """Get a single location by ID."""
    user, api_key = api_user

    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    loc = result.scalar_one_or_none()

    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    container_count = await db.scalar(
        select(func.count(Container.id))
        .where(Container.location_id == loc.id)
    ) or 0

    item_count = await db.scalar(
        select(func.count(Item.id))
        .join(Container)
        .where(Container.location_id == loc.id)
    ) or 0

    return LocationSummary(
        id=loc.id,
        name=loc.name,
        description=loc.description,
        container_count=container_count,
        item_count=item_count,
    )


@router.get("/containers", response_model=list[ContainerSummary])
async def list_containers(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
    location_id: UUID | None = None,
    limit: int = Query(default=50, le=200),
) -> list[ContainerSummary]:
    """List containers with summary information.

    Optionally filter by location_id.
    """
    user, api_key = api_user

    query = select(Container).options(selectinload(Container.location))
    if location_id:
        query = query.where(Container.location_id == location_id)
    query = query.order_by(Container.name).limit(limit)

    result = await db.execute(query)
    containers = result.scalars().all()

    summaries = []
    for c in containers:
        item_count = await db.scalar(
            select(func.count(Item.id)).where(Item.container_id == c.id)
        ) or 0

        child_count = await db.scalar(
            select(func.count(Container.id))
            .where(Container.parent_container_id == c.id)
        ) or 0

        summaries.append(ContainerSummary(
            id=c.id,
            name=c.name,
            qr_code=c.qr_code,
            location_name=c.location.name if c.location else None,
            item_count=item_count,
            child_container_count=child_count,
        ))

    return summaries


@router.get("/containers/{container_id}", response_model=ContainerSummary)
async def get_container(
    container_id: UUID,
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> ContainerSummary:
    """Get a single container by ID."""
    user, api_key = api_user

    result = await db.execute(
        select(Container)
        .options(selectinload(Container.location))
        .where(Container.id == container_id)
    )
    c = result.scalar_one_or_none()

    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    item_count = await db.scalar(
        select(func.count(Item.id)).where(Item.container_id == c.id)
    ) or 0

    child_count = await db.scalar(
        select(func.count(Container.id))
        .where(Container.parent_container_id == c.id)
    ) or 0

    return ContainerSummary(
        id=c.id,
        name=c.name,
        qr_code=c.qr_code,
        location_name=c.location.name if c.location else None,
        item_count=item_count,
        child_container_count=child_count,
    )


@router.get("/containers/qr/{qr_code}", response_model=ContainerSummary)
async def get_container_by_qr(
    qr_code: str,
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> ContainerSummary:
    """Get a container by its QR code.

    Useful for NFC/QR scanning automations in Home Assistant.
    """
    user, api_key = api_user

    result = await db.execute(
        select(Container)
        .options(selectinload(Container.location))
        .where(Container.qr_code == qr_code)
    )
    c = result.scalar_one_or_none()

    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    item_count = await db.scalar(
        select(func.count(Item.id)).where(Item.container_id == c.id)
    ) or 0

    child_count = await db.scalar(
        select(func.count(Container.id))
        .where(Container.parent_container_id == c.id)
    ) or 0

    return ContainerSummary(
        id=c.id,
        name=c.name,
        qr_code=c.qr_code,
        location_name=c.location.name if c.location else None,
        item_count=item_count,
        child_container_count=child_count,
    )


@router.get("/items", response_model=list[ItemSummary])
async def list_items(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
    container_id: UUID | None = None,
    condition: str | None = None,
    seasonal: str | None = None,
    needs_review: bool | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ItemSummary]:
    """List items with filtering options.

    Filter by container, condition, seasonal classification, or review status.
    """
    user, api_key = api_user

    query = select(Item).options(
        selectinload(Item.container).selectinload(Container.location),
        selectinload(Item.owner),
        selectinload(Item.tags),
        selectinload(Item.images),
    )

    if container_id:
        query = query.where(Item.container_id == container_id)
    if condition:
        query = query.where(Item.condition == condition)
    if seasonal:
        query = query.where(Item.seasonal == seasonal)
    if needs_review is not None:
        query = query.where(Item.needs_review == needs_review)

    query = query.order_by(Item.name).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return [_item_to_summary(item) for item in items]


@router.get("/items/{item_id}", response_model=ItemSummary)
async def get_item(
    item_id: UUID,
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> ItemSummary:
    """Get a single item by ID."""
    user, api_key = api_user

    result = await db.execute(
        select(Item)
        .options(
            selectinload(Item.container).selectinload(Container.location),
            selectinload(Item.owner),
            selectinload(Item.tags),
            selectinload(Item.images),
        )
        .where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return _item_to_summary(item)


@router.get("/search", response_model=SearchResult)
async def search_items(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.SEARCH))],
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, le=100),
) -> SearchResult:
    """Search for items.

    Searches item names, descriptions, and tags. Use for voice-activated
    searches via Home Assistant ("Hey Google, where is my red sweater?").
    """
    user, api_key = api_user

    search_term = f"%{q.lower()}%"

    # Search in name, description, and AI-generated fields
    # Search across the manual fields plus any AI translation. The JSONB
    # cast-to-text catches every language without us having to enumerate
    # them — an item with German names becomes searchable as soon as it's
    # saved, no code change required.
    where = (
        func.lower(Item.name).like(search_term)
        | func.lower(Item.description).like(search_term)
        | func.lower(func.cast(Item.ai_names, Text)).like(search_term)
        | func.lower(func.cast(Item.ai_descriptions, Text)).like(search_term)
    )

    query = (
        select(Item)
        .options(
            selectinload(Item.container).selectinload(Container.location),
            selectinload(Item.owner),
            selectinload(Item.item_tags).selectinload(ItemTag.tag),
            selectinload(Item.images),
        )
        .where(where)
        .limit(limit)
    )

    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(func.count(Item.id)).where(where)
    total = await db.scalar(count_query) or 0

    return SearchResult(
        items=[_item_to_summary(item) for item in items],
        total_count=total,
        query=q,
    )


@router.get("/tags", response_model=list[dict])
async def list_tags(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
) -> list[dict]:
    """List all tags with item counts.

    Useful for building tag-based filters in Home Assistant dashboards.
    """
    user, api_key = api_user

    result = await db.execute(
        select(Tag).order_by(Tag.name)
    )
    tags = result.scalars().all()

    tag_list = []
    for tag in tags:
        item_count = await db.scalar(
            select(func.count())
            .select_from(Item)
            .join(Item.tags)
            .where(Tag.id == tag.id)
        ) or 0

        tag_list.append({
            "id": str(tag.id),
            "name": tag.name,
            "is_ai_generated": tag.is_ai_generated,
            "item_count": item_count,
        })

    return tag_list


# ============================================================================
# Helper Functions
# ============================================================================


def _item_to_summary(item: Item) -> ItemSummary:
    """Convert an Item model to ItemSummary."""
    primary_image_url = None
    if item.images:
        # Find primary image or use first image
        primary = next(
            (img for img in item.images if item.primary_image_id and img.id == item.primary_image_id),
            item.images[0] if item.images else None,
        )
        if primary:
            primary_image_url = f"/uploads/{primary.file_path}"

    return ItemSummary(
        id=item.id,
        name=item.name,
        description=item.description,
        container_name=item.container.name if item.container else None,
        location_name=item.container.location.name if item.container and item.container.location else None,
        condition=item.condition,
        seasonal=item.seasonal,
        value_estimate=item.value_estimate,
        owner_name=item.owner.name if item.owner else None,
        primary_image_url=primary_image_url,
        tags=[tag.name for tag in item.tags] if item.tags else [],
    )
