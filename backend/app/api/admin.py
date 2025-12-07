"""Admin API endpoints."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import AdminUser, DbSession
from app.models.activity import ActivityLog
from app.models.container import Container
from app.models.item import Item
from app.models.location import Location
from app.models.user import User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


# ============== Schemas ==============


class SystemStats(BaseModel):
    """System statistics."""

    total_users: int
    active_users: int
    admin_users: int
    total_locations: int
    total_containers: int
    total_items: int
    recent_activity_count: int
    users_created_last_30_days: int
    items_created_last_30_days: int


class UserListItem(BaseModel):
    """User list item for admin view."""

    id: UUID
    name: str
    email: str | None
    role: str
    is_active: bool
    requires_password: bool
    created_at: datetime
    updated_at: datetime
    item_count: int
    last_activity: datetime | None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user."""

    name: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None
    requires_password: bool | None = None
    password: str | None = None


class AdminUserCreate(BaseModel):
    """Schema for admin creating a user."""

    name: str
    email: str | None = None
    role: str = "user"
    requires_password: bool = False
    password: str | None = None


class ActivityLogItem(BaseModel):
    """Activity log item."""

    id: UUID
    user_id: UUID | None
    user_name: str | None
    action: str
    entity_type: str
    entity_id: UUID
    entity_name: str
    details: dict[str, Any] | None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    """Paginated activity log response."""

    items: list[ActivityLogItem]
    total: int
    page: int
    page_size: int


class SegmentationSettings(BaseModel):
    """Segmentation service settings."""

    enabled: bool
    provider: str  # "local" or "replicate"
    replicate_api_token_set: bool  # Don't expose actual token
    replicate_model: str
    confidence_threshold: float
    min_area_ratio: float


class SegmentationSettingsUpdate(BaseModel):
    """Schema for updating segmentation settings."""

    enabled: bool | None = None
    provider: str | None = None
    replicate_api_token: str | None = None
    replicate_model: str | None = None
    confidence_threshold: float | None = None
    min_area_ratio: float | None = None


class SegmentationHealth(BaseModel):
    """Segmentation service health status."""

    enabled: bool
    provider: str | None
    status: str
    model: str | None = None
    error: str | None = None


# ============== Endpoints ==============


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: DbSession,
    admin: AdminUser,
) -> SystemStats:
    """Get system-wide statistics (admin only)."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    # User stats
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )
    admin_users = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    )
    users_created_last_30_days = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    )

    # Entity stats
    total_locations = await db.scalar(select(func.count(Location.id)))
    total_containers = await db.scalar(select(func.count(Container.id)))
    total_items = await db.scalar(select(func.count(Item.id)))
    items_created_last_30_days = await db.scalar(
        select(func.count(Item.id)).where(Item.created_at >= thirty_days_ago)
    )

    # Activity stats
    recent_activity_count = await db.scalar(
        select(func.count(ActivityLog.id)).where(
            ActivityLog.created_at >= thirty_days_ago
        )
    )

    return SystemStats(
        total_users=total_users or 0,
        active_users=active_users or 0,
        admin_users=admin_users or 0,
        total_locations=total_locations or 0,
        total_containers=total_containers or 0,
        total_items=total_items or 0,
        recent_activity_count=recent_activity_count or 0,
        users_created_last_30_days=users_created_last_30_days or 0,
        items_created_last_30_days=items_created_last_30_days or 0,
    )


@router.get("/users", response_model=UserListResponse)
async def list_users_admin(
    db: DbSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> UserListResponse:
    """List all users with admin details (admin only)."""
    # Base query
    query = select(User)

    # Apply filters
    if search:
        query = query.where(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    # Build response with additional info
    items = []
    for user in users:
        # Get item count for user
        item_count = await db.scalar(
            select(func.count(Item.id)).where(Item.owner_id == user.id)
        )

        # Get last activity
        last_activity_result = await db.execute(
            select(ActivityLog.created_at)
            .where(ActivityLog.user_id == user.id)
            .order_by(ActivityLog.created_at.desc())
            .limit(1)
        )
        last_activity = last_activity_result.scalar_one_or_none()

        items.append(
            UserListItem(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role.value if hasattr(user.role, "value") else str(user.role),
                is_active=user.is_active,
                requires_password=user.requires_password,
                created_at=user.created_at,
                updated_at=user.updated_at,
                item_count=item_count or 0,
                last_activity=last_activity,
            )
        )

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    db: DbSession,
    admin: AdminUser,
    data: AdminUserCreate,
) -> UserListItem:
    """Create a new user (admin only)."""
    from argon2 import PasswordHasher

    # Check if email already exists
    if data.email:
        existing = await db.scalar(select(User).where(User.email == data.email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Create user
    password_hash = None
    if data.password:
        ph = PasswordHasher()
        password_hash = ph.hash(data.password)

    role = UserRole.ADMIN if data.role == "admin" else UserRole.USER

    user = User(
        name=data.name,
        email=data.email,
        role=role,
        requires_password=data.requires_password,
        password_hash=password_hash,
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserListItem(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=user.is_active,
        requires_password=user.requires_password,
        created_at=user.created_at,
        updated_at=user.updated_at,
        item_count=0,
        last_activity=None,
    )


@router.patch("/users/{user_id}", response_model=UserListItem)
async def update_user_admin(
    db: DbSession,
    admin: AdminUser,
    user_id: UUID,
    data: AdminUserUpdate,
) -> UserListItem:
    """Update a user (admin only)."""
    from argon2 import PasswordHasher

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deactivating themselves
    if data.is_active is False and user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Prevent admin from removing their own admin role
    if data.role and data.role != "admin" and user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin role",
        )

    # Update fields
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        # Check for duplicate email
        if data.email:
            existing = await db.scalar(
                select(User).where(User.email == data.email, User.id != user_id)
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
        user.email = data.email
    if data.role is not None:
        user.role = UserRole.ADMIN if data.role == "admin" else UserRole.USER
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.requires_password is not None:
        user.requires_password = data.requires_password
    if data.password is not None:
        ph = PasswordHasher()
        user.password_hash = ph.hash(data.password)

    await db.commit()
    await db.refresh(user)

    # Get item count
    item_count = await db.scalar(
        select(func.count(Item.id)).where(Item.owner_id == user.id)
    )

    # Get last activity
    last_activity_result = await db.execute(
        select(ActivityLog.created_at)
        .where(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(1)
    )
    last_activity = last_activity_result.scalar_one_or_none()

    return UserListItem(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=user.is_active,
        requires_password=user.requires_password,
        created_at=user.created_at,
        updated_at=user.updated_at,
        item_count=item_count or 0,
        last_activity=last_activity,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    db: DbSession,
    admin: AdminUser,
    user_id: UUID,
) -> None:
    """Delete a user (admin only)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    await db.delete(user)
    await db.commit()


@router.get("/activity", response_model=ActivityLogResponse)
async def list_activity_admin(
    db: DbSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    days: int = Query(30, ge=1, le=365),
) -> ActivityLogResponse:
    """List activity logs (admin only)."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Base query
    query = select(ActivityLog).where(ActivityLog.created_at >= cutoff)

    # Apply filters
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    if action:
        query = query.where(ActivityLog.action == action)
    if entity_type:
        query = query.where(ActivityLog.entity_type == entity_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(ActivityLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    # Get user names
    user_ids = {log.user_id for log in logs if log.user_id}
    user_names = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.name).where(User.id.in_(user_ids))
        )
        user_names = {row.id: row.name for row in users_result}

    items = [
        ActivityLogItem(
            id=log.id,
            user_id=log.user_id,
            user_name=user_names.get(log.user_id) if log.user_id else None,
            action=log.action.value if hasattr(log.action, "value") else str(log.action),
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            entity_name=log.entity_name,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return ActivityLogResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============== Segmentation Settings ==============


@router.get("/segmentation", response_model=SegmentationSettings)
async def get_segmentation_settings(
    admin: AdminUser,
) -> SegmentationSettings:
    """Get segmentation service settings (admin only)."""
    from app.config import get_settings

    settings = get_settings()

    return SegmentationSettings(
        enabled=settings.segmentation_enabled,
        provider=settings.segmentation_provider,
        replicate_api_token_set=bool(settings.replicate_api_token),
        replicate_model=settings.replicate_sam_model,
        confidence_threshold=settings.segmentation_confidence_threshold,
        min_area_ratio=settings.segmentation_min_area_ratio,
    )


@router.put("/segmentation", response_model=SegmentationSettings)
async def update_segmentation_settings(
    admin: AdminUser,
    data: SegmentationSettingsUpdate,
) -> SegmentationSettings:
    """Update segmentation service settings (admin only).

    Note: Settings are stored in environment variables.
    This endpoint updates the runtime settings but changes won't persist
    after a restart unless the .env file is also updated.
    """
    import os
    from app.config import get_settings, Settings

    # Update environment variables
    if data.enabled is not None:
        os.environ["SEGMENTATION_ENABLED"] = str(data.enabled).lower()
    if data.provider is not None:
        if data.provider not in ("local", "replicate"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider must be 'local' or 'replicate'",
            )
        os.environ["SEGMENTATION_PROVIDER"] = data.provider
    if data.replicate_api_token is not None:
        os.environ["REPLICATE_API_TOKEN"] = data.replicate_api_token
    if data.replicate_model is not None:
        os.environ["REPLICATE_SAM_MODEL"] = data.replicate_model
    if data.confidence_threshold is not None:
        os.environ["SEGMENTATION_CONFIDENCE_THRESHOLD"] = str(data.confidence_threshold)
    if data.min_area_ratio is not None:
        os.environ["SEGMENTATION_MIN_AREA_RATIO"] = str(data.min_area_ratio)

    # Clear the cached settings to force reload
    get_settings.cache_clear()

    # Get the updated settings
    settings = get_settings()

    return SegmentationSettings(
        enabled=settings.segmentation_enabled,
        provider=settings.segmentation_provider,
        replicate_api_token_set=bool(settings.replicate_api_token),
        replicate_model=settings.replicate_sam_model,
        confidence_threshold=settings.segmentation_confidence_threshold,
        min_area_ratio=settings.segmentation_min_area_ratio,
    )


@router.get("/segmentation/health", response_model=SegmentationHealth)
async def check_segmentation_health(
    admin: AdminUser,
) -> SegmentationHealth:
    """Check the health of the segmentation service (admin only)."""
    from app.services.segmentation import get_segmentation_service

    service = get_segmentation_service()
    health = await service.health_check()

    return SegmentationHealth(
        enabled=health.get("enabled", False),
        provider=health.get("provider"),
        status=health.get("status", "unknown"),
        model=health.get("model"),
        error=health.get("error"),
    )
