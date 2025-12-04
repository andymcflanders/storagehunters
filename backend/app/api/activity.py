"""Activity log API routes."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import desc, select

from app.api.deps import CurrentUser, DbSession
from app.models.activity import ActionEnum, ActivityLog

router = APIRouter()


class ActivityUserResponse(BaseModel):
    """User info in activity response."""

    id: UUID
    name: str


class ActivityResponse(BaseModel):
    """Activity log response schema."""

    id: UUID
    user_id: UUID | None
    user_name: str | None
    action: ActionEnum
    entity_type: str
    entity_id: UUID
    entity_name: str
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    """Paginated activity list response."""

    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: str | None = None,
    action: ActionEnum | None = None,
) -> ActivityListResponse:
    """List activity logs with pagination."""
    from app.models.user import User

    # Build query
    query = select(ActivityLog)

    if entity_type:
        query = query.where(ActivityLog.entity_type == entity_type)
    if action:
        query = query.where(ActivityLog.action == action)

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(desc(ActivityLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    activities = result.scalars().all()

    # Get user names
    user_ids = {a.user_id for a in activities if a.user_id}
    user_names: dict[UUID, str] = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.name).where(User.id.in_(user_ids))
        )
        user_names = {row[0]: row[1] for row in users_result}

    # Build response
    items = [
        ActivityResponse(
            id=a.id,
            user_id=a.user_id,
            user_name=user_names.get(a.user_id) if a.user_id else None,
            action=a.action,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            entity_name=a.entity_name,
            details=a.details,
            created_at=a.created_at,
        )
        for a in activities
    ]

    return ActivityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/my", response_model=ActivityListResponse)
async def list_my_activities(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ActivityListResponse:
    """List current user's activity logs."""
    from sqlalchemy import func

    query = select(ActivityLog).where(ActivityLog.user_id == current_user.id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(desc(ActivityLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    activities = result.scalars().all()

    items = [
        ActivityResponse(
            id=a.id,
            user_id=a.user_id,
            user_name=current_user.name,
            action=a.action,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            entity_name=a.entity_name,
            details=a.details,
            created_at=a.created_at,
        )
        for a in activities
    ]

    return ActivityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )
