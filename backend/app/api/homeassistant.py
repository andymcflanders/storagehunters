"""Home Assistant integration API routes.

This module provides a clean, stable API designed specifically for Home Assistant
integration. All endpoints use API key authentication and are optimized for
sensor data and automations.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Text, func, or_, select
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
    # Stable per-database UUID. The HA integration uses this as its
    # config-entry unique_id so the user can change the StorageHub
    # host URL without forking a fresh HA entry and orphaning all
    # existing entities. None on legacy installs that pre-date
    # migration 023, so the integration must tolerate that case.
    instance_id: str | None = None


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
    for Home Assistant discovery and health checks. Includes the
    instance UUID so HA can stably identify the same install across
    URL changes.
    """
    from app.ai import _load_ai_settings_sync

    ai_settings = _load_ai_settings_sync()
    return SystemStatus(instance_id=ai_settings.instance_uuid)


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
        selectinload(Item.item_tags).selectinload(ItemTag.tag),
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


@router.get("/items/index")
async def items_index(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.READ))],
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
) -> Response:
    """Lite item index for the HA Lovelace card's instant filter.

    Pre-loads a minimal record per item so the card can substring-
    filter in JavaScript without a network round-trip per keystroke.
    Heavy fields (images, tags, descriptions, full container
    objects) are deliberately omitted — target wire size for a
    10k-item inventory is under 200 KB gzipped.

    The response carries an ETag derived from the MAX(updated_at)
    across items, containers, locations, and users — the four
    tables whose changes can invalidate the card's cached index.
    Clients send `If-None-Match` to get a 304 on the no-change path.

    Note: this endpoint reads the card's view of every item the API
    key can see; it does NOT scope per-user since the integration
    is configured with one shared key per HA install.
    """

    # Single round-trip ETag over the four tables that can
    # invalidate a cached client copy.
    fingerprint_row = await db.execute(
        select(
            func.greatest(
                select(func.max(Item.updated_at)).scalar_subquery(),
                select(func.max(Container.updated_at)).scalar_subquery(),
                select(func.max(Location.updated_at)).scalar_subquery(),
                select(func.max(User.updated_at)).scalar_subquery(),
            )
        )
    )
    fingerprint = fingerprint_row.scalar_one_or_none()
    # Empty install — return a stable etag so 304s still work.
    fingerprint_str = fingerprint.isoformat() if fingerprint else "empty"
    etag = '"' + hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16] + '"'

    cache_headers = {
        "ETag": etag,
        "Cache-Control": "private, max-age=900",
    }

    if if_none_match and if_none_match.strip() == etag:
        return Response(status_code=304, headers=cache_headers)

    # Tuple-yielding select keeps the query lean — no selectinload
    # of images/tags/etc, just the five columns the card needs.
    stmt = (
        select(
            Item.id,
            Item.name,
            Item.ai_names,
            User.name.label("owner_name"),
            Container.name.label("container_name"),
            Location.name.label("location_name"),
        )
        .outerjoin(User, Item.owner_id == User.id)
        .outerjoin(Container, Item.container_id == Container.id)
        .outerjoin(Location, Container.location_id == Location.id)
        .order_by(Item.name)
    )
    rows = (await db.execute(stmt)).all()

    payload = [
        {
            "id": str(row.id),
            "name": row.name,
            "owner_name": row.owner_name,
            "container_name": row.container_name,
            "location_name": row.location_name,
            # Flatten the JSONB language-keyed dict to a list of
            # values — the card just wants searchable strings, it
            # doesn't care which language each one is in.
            "ai_names": [v for v in (row.ai_names or {}).values() if v],
        }
        for row in rows
    ]

    # Use JSONResponse directly so the ETag header rides on the
    # body. GZipMiddleware compresses on the way out.
    return JSONResponse(content=payload, headers=cache_headers)


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
            selectinload(Item.item_tags).selectinload(ItemTag.tag),
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


def _build_token_patterns(q: str) -> list[list[str]]:
    """Turn a query string into one pattern-set per typed token.

    Each set is the list of substrings to try for that token; the
    token matches a field if ANY pattern in its set occurs in the
    field. For most tokens the set is just `[token]`, but Norwegian
    possessive "s" is unmarked (no apostrophe) — so for tokens
    ending in `s` we ALSO try the stem so "Sverres" matches an
    owner named "Sverre". `LIKE %sverres%` against "Sverre" returns
    false (the substring goes the wrong direction), which is why
    the spec's earlier "substring matching covers it" wasn't true.

    English apostrophe-s ("Sverre's") is stripped before tokens are
    inspected. Tokens shorter than 2 chars are dropped to avoid
    runaway matches; the stem is only added when the token is at
    least 4 chars so we don't strip "is"/"us"/"his" into nothing
    useful.
    """
    out: list[list[str]] = []
    for raw in q.lower().split():
        if raw.endswith("'s"):
            raw = raw[:-2]
        if len(raw) < 2:
            continue
        patterns = [raw]
        if len(raw) >= 4 and raw.endswith("s"):
            patterns.append(raw[:-1])
        out.append(patterns)
    return out


@router.get("/search", response_model=SearchResult)
async def search_items(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.SEARCH))],
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, le=100),
) -> SearchResult:
    """Search for items.

    Searches item names, descriptions, AI-generated content, and the
    owner's name. Use for voice-activated searches via Home Assistant
    ("Hey Google, where is Sverre's red sweater?").

    Multi-token queries require *every* token to match *some* field —
    that's how "Sverre jakke" finds Sverre's jackets without the
    caller passing an explicit owner filter. Owner-name and
    item-name tokens can land in the same query in any order.

    Norwegian possessive `s` (no apostrophe) is handled by also
    trying the stem-stripped form per token, so "Sverres jakke"
    behaves the same as "Sverre jakke".
    """
    user, api_key = api_user

    token_patterns = _build_token_patterns(q)
    if not token_patterns:
        # Nothing meaningful to search for; return an empty result
        # rather than raising so the integration's error path stays
        # quiet on noise queries.
        return SearchResult(items=[], total_count=0, query=q)

    # Build per-token "matches any field via any pattern" predicates
    # and AND them together. The JSONB cast-to-text catches every
    # language the AI has stored — adding German etc. doesn't require
    # a code change here. Owner name is searched via a left-joined
    # User.
    def token_predicate(patterns: list[str]):
        clauses = []
        for p in patterns:
            pat = f"%{p}%"
            clauses.extend(
                [
                    func.lower(Item.name).like(pat),
                    func.lower(Item.description).like(pat),
                    func.lower(func.cast(Item.ai_names, Text)).like(pat),
                    func.lower(func.cast(Item.ai_descriptions, Text)).like(pat),
                    func.lower(User.name).like(pat),
                ]
            )
        return or_(*clauses)

    base = select(Item).join(Item.owner, isouter=True)
    for patterns in token_patterns:
        base = base.where(token_predicate(patterns))

    query = base.options(
        selectinload(Item.container).selectinload(Container.location),
        selectinload(Item.owner),
        selectinload(Item.item_tags).selectinload(ItemTag.tag),
        selectinload(Item.images),
    ).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    count_base = select(func.count(Item.id)).join(Item.owner, isouter=True)
    for patterns in token_patterns:
        count_base = count_base.where(token_predicate(patterns))
    total = await db.scalar(count_base) or 0

    return SearchResult(
        items=[_item_to_summary(item) for item in items],
        total_count=total,
        query=q,
    )


@router.get("/search/semantic", response_model=SearchResult)
async def search_items_semantic(
    db: DbSession,
    api_user: Annotated[tuple, Depends(require_scope(APIKeyScope.SEARCH))],
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, le=100),
) -> SearchResult:
    """Semantic search with owner pre-filter and synonym expansion.

    Note: this endpoint is "semantic" in the same sense the web UI's
    /api/search is — synonym-expanded LIKE matching plus optional
    GPT-4o-mini query parsing for attribute extraction. There are
    no item embeddings or vector similarity at this layer; the
    synonym dictionaries (color + clothing terms in EN+NO) are how
    queries like `genser` reach items named `Cardigan`. If those
    dictionaries fall short for a real query, extending them is
    cheaper than introducing a vector index.

    Behavior:
    - Owner pre-filter: tokens whose stem (English `'s` strip,
      Norwegian `s` ≥ 4 chars) substring-matches a User.name are
      pulled out as owner filters. The rest go to content search.
    - Content search: parse_query() expands the remaining tokens
      to colors/types/synonyms/etc, then OR-of-LIKE across name /
      description / ai_names / ai_descriptions / tags / AI image tags.
    - When all tokens are owner-matching (e.g. `?q=Sverre`), the
      content search is skipped and every item owned by that user
      is returned.

    Same response shape as /api/ha/search so callers can switch
    drop-in.
    """
    from app.models.item import SeasonalEnum
    from app.services.semantic_search import get_semantic_search_service

    user, api_key = api_user

    token_patterns = _build_token_patterns(q)
    if not token_patterns:
        return SearchResult(items=[], total_count=0, query=q)

    # Owner pre-filter. Pull every active non-admin user once and
    # check each token's pattern set against User.name (case-
    # insensitive substring). A token "hit" yanks it out of the
    # content stream so we don't waste a LIKE round on
    # owner-as-content.
    from app.models.user import UserRole

    users_result = await db.execute(
        select(User).where(
            User.role != UserRole.ADMIN,
            User.is_active == True,  # noqa: E712
        )
    )
    all_users = users_result.scalars().all()

    matched_owner_ids: set = set()
    content_tokens: list[str] = []
    for patterns in token_patterns:
        hit = False
        for u in all_users:
            uname = u.name.lower()
            if any(p in uname for p in patterns):
                matched_owner_ids.add(u.id)
                hit = True
        if not hit:
            # Use the longest pattern (which is the user's typed
            # token, not the stem) as the content term.
            content_tokens.append(patterns[0])

    # Content search via the synonym expander. Skip parse_query
    # entirely when there's no content portion — the owner filter
    # alone is enough to return every item belonging to the
    # matched user(s).
    content_conditions = []
    if content_tokens:
        content_query = " ".join(content_tokens)
        search_service = get_semantic_search_service()
        try:
            parsed = await search_service.parse_query(content_query)
        except Exception:
            # parse_query already swallows AI failures via _local_parse
            # fallback, but defensive in case the local path also
            # blows up on weird input.
            parsed = None

        all_terms: set[str] = set()
        if parsed:
            all_terms.update(t.lower() for t in parsed.search_terms)
            all_terms.update(t.lower() for t in parsed.colors)
            all_terms.update(t.lower() for t in parsed.color_synonyms)
            all_terms.update(t.lower() for t in parsed.item_types)
            all_terms.update(t.lower() for t in parsed.type_synonyms)
            all_terms.update(t.lower() for t in parsed.materials)
            all_terms.update(t.lower() for t in parsed.brands)
        # Always include the raw content tokens so we don't lose
        # signal if parse_query returns thin results.
        all_terms.update(content_tokens)

        for term in all_terms:
            if len(term) < 2:
                continue
            pat = f"%{term}%"
            content_conditions.extend(
                [
                    func.lower(Item.name).like(pat),
                    func.lower(Item.description).like(pat),
                    func.lower(func.cast(Item.ai_names, Text)).like(pat),
                    func.lower(func.cast(Item.ai_descriptions, Text)).like(pat),
                ]
            )
            # Tag table match (manual + AI tags share the Tag table
            # via item_tags) and the per-image AI-tag array.
            tag_subquery = (
                select(ItemTag.item_id)
                .join(Tag, Tag.id == ItemTag.tag_id)
                .where(func.lower(Tag.name).like(pat))
            )
            content_conditions.append(Item.id.in_(tag_subquery))
            ai_tag_subquery = (
                select(ItemImage.item_id).where(ItemImage.ai_tags.any(term))
            )
            content_conditions.append(Item.id.in_(ai_tag_subquery))

        # Size + season filters from parse_query — same idea as
        # the web UI's smart-search path.
        if parsed:
            for parsed_size in parsed.sizes:
                content_conditions.append(
                    func.lower(Item.size).like(f"%{parsed_size.lower()}%")
                )
            season_map = {
                "winter": SeasonalEnum.WINTER,
                "summer": SeasonalEnum.SUMMER,
                "spring": SeasonalEnum.SPRING,
                "fall": SeasonalEnum.FALL,
                "autumn": SeasonalEnum.FALL,
                "holiday": SeasonalEnum.HOLIDAY,
            }
            for season in parsed.seasons:
                if season.lower() in season_map:
                    content_conditions.append(Item.seasonal == season_map[season.lower()])

    # Compose owner filter AND content filter.
    base = select(Item)
    where_clauses = []
    if matched_owner_ids:
        where_clauses.append(Item.owner_id.in_(matched_owner_ids))
    if content_conditions:
        where_clauses.append(or_(*content_conditions))
    if not where_clauses:
        # Empty query after stripping noise — return empty rather
        # than every item in the system.
        return SearchResult(items=[], total_count=0, query=q)

    for clause in where_clauses:
        base = base.where(clause)

    fetch = base.options(
        selectinload(Item.container).selectinload(Container.location),
        selectinload(Item.owner),
        selectinload(Item.item_tags).selectinload(ItemTag.tag),
        selectinload(Item.images),
    ).order_by(Item.name).limit(limit)

    rows = (await db.execute(fetch)).scalars().all()

    count_base = select(func.count(Item.id))
    for clause in where_clauses:
        count_base = count_base.where(clause)
    total = await db.scalar(count_base) or 0

    return SearchResult(
        items=[_item_to_summary(item) for item in rows],
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
        # Count via the join table directly — `Item.tags` doesn't
        # exist; the M2M lives on Item.item_tags / ItemTag.tag.
        item_count = await db.scalar(
            select(func.count(ItemTag.item_id)).where(ItemTag.tag_id == tag.id)
        ) or 0

        tag_list.append({
            "id": str(tag.id),
            "name": tag.name,
            # Tag.user_created is True when the user added it manually;
            # invert for the integration's "AI-generated" flag so the
            # boolean's semantic is what HA expects.
            "is_ai_generated": not tag.user_created,
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
            # The model column is `filepath` (no underscore). Route
            # through ImageStorageService to mirror what /api/items
            # does — gives the integration a consistent URL shape.
            from app.services.image_storage import ImageStorageService
            primary_image_url = ImageStorageService().get_url(primary.filepath)

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
        # Item has no `.tags` shortcut — walk the M2M through item_tags.
        # Callers must selectinload(Item.item_tags).selectinload(ItemTag.tag)
        # to avoid a lazy-load explosion here.
        tags=[it.tag.name for it in item.item_tags] if item.item_tags else [],
    )
