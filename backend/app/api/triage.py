"""Triage API: the "Tinder for items" / declutter flow.

The user sees one item at a time and picks Love / Undecided / Hate.
Decisions are shared per-household (one row per item, no per-user
fork). Cooldowns:
  - Love     → 12 months invisible
  - Undecided→ 3 months invisible
  - Hate     → no cooldown; lives on /declutter/discard until
              acted on (delete / mark donated / undo)

Adult items only: anything with size_age_max_months set is excluded
because /outgrown already covers that workflow.
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.api.items import build_item_path
from app.models.item import Item, ItemTag
from app.models.tag import Tag
from app.models.user import User, UserRole
from app.schemas.item import (
    ContainerPath,
    ItemImageResponse,
    OwnerInfo,
    TagInfo,
)
from app.services.activity_logger import ActivityLogger
from app.services.image_storage import ImageStorageService

router = APIRouter()


# Cooldowns. Hard-coded for v1; we can expose admin overrides later
# if usage shows the defaults are wrong.
COOLDOWN_LOVE = timedelta(days=365)
COOLDOWN_UNDECIDED = timedelta(days=90)


class TriageDecisionRequest(BaseModel):
    """User's verdict on the current item."""

    decision: str = Field(..., pattern="^(love|undecided|hate)$")


class TriageNextItem(BaseModel):
    """One item to be triaged, with everything the card needs to render."""

    id: UUID
    name: str
    description: str | None
    size: str | None
    primary_image_url: str | None
    images: list[ItemImageResponse]
    tags: list[TagInfo]
    owner: OwnerInfo | None
    path: list[ContainerPath]
    # The previous decision, if any — non-null when the user is
    # re-visiting an item past its cooldown. Lets the UI hint
    # "you said Undecided last time".
    previous_decision: str | None
    previous_decided_at: datetime | None


class TriageNextResponse(BaseModel):
    """Next-card response. `item` is null when the pool is empty."""

    item: TriageNextItem | None
    remaining_estimate: int  # rough count of eligible items (current item included)


class TriageFilterOption(BaseModel):
    """One option in the filter dropdowns, with its eligible-item count."""

    id: str  # owner UUID stringified, or tag name
    label: str
    count: int


class TriageFiltersResponse(BaseModel):
    """Filter dropdown contents for the /declutter page."""

    owners: list[TriageFilterOption]
    tags: list[TriageFilterOption]


class DiscardItem(BaseModel):
    """One row on the discard pile."""

    id: UUID
    name: str
    size: str | None
    primary_image_url: str | None
    owner: OwnerInfo | None
    decided_at: datetime | None


class DiscardGroup(BaseModel):
    """Discard items grouped by their container path so the user can
    do a single physical sweep."""

    container_id: UUID
    path_label: str  # "Garage / Shelf B / Box 3"
    items: list[DiscardItem]


class DiscardResponse(BaseModel):
    groups: list[DiscardGroup]
    total: int


def _eligible_pool_query(owner_id: UUID | None, tag_name: str | None):
    """Build the SELECT for the pool of items eligible for triage.

    Eligibility:
    - AI-processed (no placeholder cards)
    - Not currently in cooldown (show_after NULL or in the past)
    - Not already hated (those live on /declutter/discard)
    - Not age-mapped (kid stuff is /outgrown's domain)
    - Optional owner / tag filters
    """
    now = datetime.utcnow()
    query = select(Item).where(
        Item.ai_processed == True,  # noqa: E712
        Item.size_age_max_months.is_(None),
        or_(Item.triage_decision.is_(None), Item.triage_decision != "hate"),
        or_(Item.triage_show_after.is_(None), Item.triage_show_after <= now),
    )
    if owner_id is not None:
        query = query.where(Item.owner_id == owner_id)
    if tag_name:
        tag_subquery = (
            select(ItemTag.item_id)
            .join(Tag, Tag.id == ItemTag.tag_id)
            .where(func.lower(Tag.name) == tag_name.strip().lower())
        )
        query = query.where(Item.id.in_(tag_subquery))
    return query


@router.get("/next", response_model=TriageNextResponse)
async def triage_next(
    db: DbSession,
    current_user: CurrentUser,
    owner_id: UUID | None = None,
    tag: str | None = None,
) -> TriageNextResponse:
    """Return one random eligible item to triage, plus a rough remaining count."""
    # Cheap count first so we can populate remaining_estimate even
    # when the pool is empty. Use func.count() (no column arg) so
    # SQLAlchemy doesn't add the items table back into the FROM
    # alongside the subquery — that creates a cartesian product
    # and inflates the count by the table's total row count.
    count = await db.scalar(
        select(func.count()).select_from(
            _eligible_pool_query(owner_id, tag).subquery()
        )
    ) or 0

    if count == 0:
        return TriageNextResponse(item=None, remaining_estimate=0)

    # Random pick. Postgres random() ordering is fine at our scale
    # — typical household = thousands of items, not millions.
    pick_query = (
        _eligible_pool_query(owner_id, tag)
        .options(
            selectinload(Item.images),
            selectinload(Item.item_tags).selectinload(ItemTag.tag),
            selectinload(Item.owner),
        )
        .order_by(func.random())
        .limit(1)
    )
    result = await db.execute(pick_query)
    item = result.scalar_one_or_none()
    if not item:
        return TriageNextResponse(item=None, remaining_estimate=0)

    storage = ImageStorageService()
    images = [
        ItemImageResponse(
            id=img.id,
            filename=img.filename,
            filepath=storage.get_url(img.filepath),
            ai_tags=img.ai_tags or [],
            ai_description=img.ai_description,
            ai_processed=img.ai_processed,
            created_at=img.created_at,
        )
        for img in item.images
    ]
    primary_url: str | None = None
    if item.primary_image_id:
        primary = next(
            (i for i in images if i.id == item.primary_image_id), None
        )
        if primary:
            primary_url = primary.filepath
    if primary_url is None and images:
        primary_url = images[0].filepath

    tags = [TagInfo(id=it.tag.id, name=it.tag.name) for it in item.item_tags]
    owner = (
        OwnerInfo(id=item.owner.id, name=item.owner.name, avatar_url=item.owner.avatar_url)
        if item.owner
        else None
    )
    path = await build_item_path(item, db)

    return TriageNextResponse(
        item=TriageNextItem(
            id=item.id,
            name=item.name,
            description=item.description,
            size=item.size,
            primary_image_url=primary_url,
            images=images,
            tags=tags,
            owner=owner,
            path=path,
            previous_decision=item.triage_decision,
            previous_decided_at=item.triage_decided_at,
        ),
        remaining_estimate=count,
    )


@router.post("/{item_id}/decide", status_code=status.HTTP_204_NO_CONTENT)
async def triage_decide(
    item_id: UUID,
    payload: TriageDecisionRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Record a Love/Undecided/Hate verdict and apply the cooldown."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    now = datetime.utcnow()
    item.triage_decision = payload.decision
    item.triage_decided_at = now
    if payload.decision == "love":
        item.triage_show_after = now + COOLDOWN_LOVE
    elif payload.decision == "undecided":
        item.triage_show_after = now + COOLDOWN_UNDECIDED
    else:  # hate
        # No cooldown — the item goes to the discard list and stays
        # off the next-card pool indefinitely.
        item.triage_show_after = None

    await db.flush()


@router.get("/filters", response_model=TriageFiltersResponse)
async def triage_filters(
    db: DbSession,
    current_user: CurrentUser,
) -> TriageFiltersResponse:
    """Filter dropdown options.

    Owners: every non-admin user that owns at least one eligible
    item. Tags: top tags by eligible-item count, capped at 30 to
    keep the dropdown sane.
    """
    base_subquery = _eligible_pool_query(None, None).subquery()

    # Owners with at least one eligible item.
    owner_rows = await db.execute(
        select(User.id, User.name, func.count(base_subquery.c.id).label("cnt"))
        .join(base_subquery, base_subquery.c.owner_id == User.id)
        .where(User.role != UserRole.ADMIN)
        .group_by(User.id, User.name)
        .order_by(func.count(base_subquery.c.id).desc())
    )
    owners = [
        TriageFilterOption(id=str(uid), label=name, count=cnt)
        for uid, name, cnt in owner_rows.all()
    ]

    # Tags applied to at least one eligible item, top-30 by count.
    tag_rows = await db.execute(
        select(Tag.name, func.count(base_subquery.c.id).label("cnt"))
        .join(ItemTag, ItemTag.tag_id == Tag.id)
        .join(base_subquery, base_subquery.c.id == ItemTag.item_id)
        .group_by(Tag.name)
        .order_by(func.count(base_subquery.c.id).desc())
        .limit(30)
    )
    tags = [
        TriageFilterOption(id=name, label=name, count=cnt)
        for name, cnt in tag_rows.all()
    ]

    return TriageFiltersResponse(owners=owners, tags=tags)


@router.get("/discard", response_model=DiscardResponse)
async def triage_discard(
    db: DbSession,
    current_user: CurrentUser,
) -> DiscardResponse:
    """All items the household has decided to toss, grouped by
    container path so a single sweep handles a whole shelf."""
    result = await db.execute(
        select(Item)
        .where(Item.triage_decision == "hate")
        .options(
            selectinload(Item.images),
            selectinload(Item.owner),
        )
        .order_by(Item.triage_decided_at.desc())
    )
    items = result.scalars().all()

    storage = ImageStorageService()
    # Group by container_id but render the path as a "/"-joined label
    # so the user can scan visually.
    groups_by_container: dict[UUID, DiscardGroup] = {}
    for item in items:
        if item.container_id not in groups_by_container:
            path = await build_item_path(item, db)
            label = " / ".join(p.name for p in path)
            groups_by_container[item.container_id] = DiscardGroup(
                container_id=item.container_id,
                path_label=label,
                items=[],
            )

        primary_url: str | None = None
        if item.primary_image_id:
            primary = next(
                (i for i in item.images if i.id == item.primary_image_id), None
            )
            if primary:
                primary_url = storage.get_url(primary.filepath)
        if primary_url is None and item.images:
            primary_url = storage.get_url(item.images[0].filepath)

        groups_by_container[item.container_id].items.append(
            DiscardItem(
                id=item.id,
                name=item.name,
                size=item.size,
                primary_image_url=primary_url,
                owner=(
                    OwnerInfo(
                        id=item.owner.id,
                        name=item.owner.name,
                        avatar_url=item.owner.avatar_url,
                    )
                    if item.owner
                    else None
                ),
                decided_at=item.triage_decided_at,
            )
        )

    return DiscardResponse(
        groups=list(groups_by_container.values()),
        total=len(items),
    )


@router.post("/{item_id}/undo", status_code=status.HTTP_204_NO_CONTENT)
async def triage_undo(
    item_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Clear a triage decision (e.g. user re-thinks a Hate)."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    item.triage_decision = None
    item.triage_decided_at = None
    item.triage_show_after = None
    await db.flush()


@router.post("/{item_id}/mark-donated", status_code=status.HTTP_204_NO_CONTENT)
async def triage_mark_donated(
    item_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Soft action: log a donation in the activity feed and delete
    the item. Distinct from a plain delete so the activity feed
    captures intent."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    logger = ActivityLogger(db)
    await logger.log_deleted(
        user_id=current_user.id,
        entity_type="item",
        entity_id=item.id,
        entity_name=f"{item.name} (donated)",
    )
    await db.delete(item)
