"""Outgrown items API.

Surfaces items the household has aged out of: a kid's size 92 parka
when the kid is now 5 years old, etc. Drives the /outgrown page.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.item import Item
from app.models.user import User, UserRole
from app.schemas.item import OwnerInfo

router = APIRouter()


# How far ahead we look when picking inherit candidates. Wool tights
# that don't fit Sonja today but will in ~6 months are still useful;
# something Magnus won't fit for 3 years is too speculative — by then
# he might be wearing a different size and we'll re-classify the item
# anyway.
INHERIT_LOOKAHEAD_MONTHS = 12


class OutgrownInheritCandidate(BaseModel):
    """A household member the item could be inherited to."""

    user: OwnerInfo
    user_age_months: int
    # 0 when the item fits the candidate today; positive when they
    # still need to grow into it (months_until_fit). Negative would
    # mean already past size_age_max — those candidates aren't picked.
    months_until_fit: int


class OutgrownItem(BaseModel):
    """One row on the /outgrown page."""

    id: UUID
    name: str
    size: str | None
    primary_image_url: str | None
    container_id: UUID
    # The user who has outgrown this — owner if set, otherwise the AI's
    # suggested owner. Both forms get surfaced because an AI suggestion
    # the user never applied is still useful information.
    effective_owner: OwnerInfo
    is_suggested_owner: bool  # true when effective_owner came from suggested_owner_id
    effective_owner_age_months: int
    size_age_min_months: int
    size_age_max_months: int
    # owner_age - size_age_max. Always > 0 (we filter on it).
    months_outgrown: int
    inherit_to: OutgrownInheritCandidate | None


class OutgrownResponse(BaseModel):
    """Outgrown listing, sorted most-outgrown first."""

    items: list[OutgrownItem]


def _age_months(birthdate: date | None, today: date) -> int | None:
    if birthdate is None:
        return None
    years = today.year - birthdate.year
    months = today.month - birthdate.month
    days = today.day - birthdate.day
    total = years * 12 + months - (1 if days < 0 else 0)
    return max(total, 0)


def _best_inherit_candidate(
    item: Item,
    effective_owner_id: UUID,
    candidates: list[tuple[User, int]],
) -> OutgrownInheritCandidate | None:
    """Pick the household member best positioned to inherit the item.

    Eligible candidates: users (excluding the current effective owner)
    whose [age, age + LOOKAHEAD] overlaps the size's age range. Among
    those, prefer the candidate who fits *soonest* — fits-now beats
    fits-in-six-months. Ties broken by youngest age (longer wear life).
    """
    if item.size_age_min_months is None or item.size_age_max_months is None:
        return None

    best: tuple[int, int, User, int] | None = None  # (months_until_fit, age, user, age)
    for user, age_months in candidates:
        if user.id == effective_owner_id:
            continue
        # Already aged past the upper bound → would be outgrown for
        # them too, skip.
        if age_months > item.size_age_max_months:
            continue
        # Will they reach the lower bound within our lookahead window?
        if age_months + INHERIT_LOOKAHEAD_MONTHS < item.size_age_min_months:
            continue

        months_until_fit = max(0, item.size_age_min_months - age_months)
        candidate = (months_until_fit, age_months, user, age_months)
        if best is None or candidate < best:
            best = candidate

    if best is None:
        return None

    months_until_fit, _, user, age_months = best
    return OutgrownInheritCandidate(
        user=OwnerInfo(id=user.id, name=user.name, avatar_url=user.avatar_url),
        user_age_months=age_months,
        months_until_fit=months_until_fit,
    )


@router.get("", response_model=OutgrownResponse)
async def list_outgrown(
    db: DbSession,
    current_user: CurrentUser,
) -> OutgrownResponse:
    """List items the household has aged out of, with inherit suggestions."""
    from app.services.image_storage import ImageStorageService

    today = date.today()

    # Pre-fetch every active non-admin user once. We need both the
    # candidate pool for inheriting AND a quick lookup of the
    # effective owner's age, so cache by id.
    users_result = await db.execute(
        select(User).where(
            User.role != UserRole.ADMIN,
            User.is_active == True,  # noqa: E712
        )
    )
    all_users = users_result.scalars().all()
    user_age: dict[UUID, int | None] = {
        u.id: _age_months(u.birthdate, today) for u in all_users
    }
    candidates_for_inherit = [
        (u, user_age[u.id])
        for u in all_users
        if user_age[u.id] is not None
    ]

    # Pull every candidate item: any age-mapped item with at least
    # one user attached (real or suggested) that hasn't been
    # explicitly dismissed.
    items_result = await db.execute(
        select(Item)
        .where(
            Item.size_age_max_months.is_not(None),
            Item.outgrown_dismissed_at.is_(None),
            or_(Item.owner_id.is_not(None), Item.suggested_owner_id.is_not(None)),
        )
        .options(
            selectinload(Item.owner),
            selectinload(Item.suggested_owner),
            selectinload(Item.images),
        )
    )
    items = items_result.scalars().all()

    storage = ImageStorageService()
    results: list[OutgrownItem] = []

    for item in items:
        # Effective owner: the real owner takes precedence over the
        # AI's suggestion. Either way, we need their age in months.
        if item.owner_id is not None and item.owner is not None:
            effective_owner = item.owner
            is_suggested = False
        elif item.suggested_owner_id is not None and item.suggested_owner is not None:
            effective_owner = item.suggested_owner
            is_suggested = True
        else:
            continue

        owner_age = user_age.get(effective_owner.id)
        if owner_age is None:
            # No birthdate on the owner — we can't determine outgrown
            # status. Skip rather than guess.
            continue

        if owner_age <= item.size_age_max_months:
            continue  # not outgrown yet

        # Resolve a primary image URL for the row thumbnail.
        primary_image_url: str | None = None
        if item.primary_image_id:
            primary = next(
                (i for i in item.images if i.id == item.primary_image_id), None
            )
            if primary:
                primary_image_url = storage.get_url(primary.filepath)
        if primary_image_url is None and item.images:
            primary_image_url = storage.get_url(item.images[0].filepath)

        inherit = _best_inherit_candidate(
            item, effective_owner.id, candidates_for_inherit
        )

        results.append(
            OutgrownItem(
                id=item.id,
                name=item.name,
                size=item.size,
                primary_image_url=primary_image_url,
                container_id=item.container_id,
                effective_owner=OwnerInfo(
                    id=effective_owner.id,
                    name=effective_owner.name,
                    avatar_url=effective_owner.avatar_url,
                ),
                is_suggested_owner=is_suggested,
                effective_owner_age_months=owner_age,
                size_age_min_months=item.size_age_min_months,
                size_age_max_months=item.size_age_max_months,
                months_outgrown=owner_age - item.size_age_max_months,
                inherit_to=inherit,
            )
        )

    # Most-outgrown first so the longest-stuck items surface at the top.
    results.sort(key=lambda r: r.months_outgrown, reverse=True)

    return OutgrownResponse(items=results)
