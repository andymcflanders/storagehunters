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


class ModelOption(BaseModel):
    """Model option for dropdown selection."""

    id: str
    name: str
    description: str


class CostEstimate(BaseModel):
    """Cost estimate for an API call."""

    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    cost_per_image_usd: float | None = None


class OpenAISettings(BaseModel):
    """OpenAI configuration settings."""

    # Vision classification settings
    vision_enabled: bool
    vision_model: str
    vision_max_tokens: int
    vision_temperature: float
    vision_cost_estimate: CostEstimate

    # Summary generation settings
    summary_enabled: bool
    summary_model: str
    summary_max_tokens: int
    summary_temperature: float
    summary_cost_estimate: CostEstimate

    # Available model options
    vision_models: list[ModelOption]
    text_models: list[ModelOption]

    # API key status
    api_key_set: bool


class OpenAISettingsUpdate(BaseModel):
    """Schema for updating OpenAI settings."""

    vision_enabled: bool | None = None
    vision_model: str | None = None
    vision_max_tokens: int | None = None
    vision_temperature: float | None = None

    summary_enabled: bool | None = None
    summary_model: str | None = None
    summary_max_tokens: int | None = None
    summary_temperature: float | None = None


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



# ============== OpenAI Settings ==============


async def get_or_create_ai_settings(db: DbSession):
    """Get or create the singleton AI settings record."""
    from app.models.ai_settings import AISettings

    result = await db.execute(select(AISettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = AISettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.get("/openai", response_model=OpenAISettings)
async def get_openai_settings(
    db: DbSession,
    admin: AdminUser,
) -> OpenAISettings:
    """Get OpenAI configuration settings (admin only)."""
    from app.config import get_settings
    from app.models.ai_settings import (
        VISION_MODELS,
        TEXT_MODELS,
        estimate_vision_cost,
        estimate_summary_cost,
    )

    config = get_settings()
    ai_settings = await get_or_create_ai_settings(db)

    # Get cost estimates
    vision_cost = estimate_vision_cost(ai_settings.vision_model)
    summary_cost = estimate_summary_cost(ai_settings.summary_model)

    return OpenAISettings(
        vision_enabled=ai_settings.vision_enabled,
        vision_model=ai_settings.vision_model,
        vision_max_tokens=ai_settings.vision_max_tokens,
        vision_temperature=ai_settings.vision_temperature,
        vision_cost_estimate=CostEstimate(
            model=vision_cost["model"],
            estimated_input_tokens=vision_cost["estimated_input_tokens"],
            estimated_output_tokens=vision_cost["estimated_output_tokens"],
            estimated_cost_usd=vision_cost["estimated_cost_usd"],
            cost_per_image_usd=vision_cost["cost_per_image_usd"],
        ),
        summary_enabled=ai_settings.summary_enabled,
        summary_model=ai_settings.summary_model,
        summary_max_tokens=ai_settings.summary_max_tokens,
        summary_temperature=ai_settings.summary_temperature,
        summary_cost_estimate=CostEstimate(
            model=summary_cost["model"],
            estimated_input_tokens=summary_cost["estimated_input_tokens"],
            estimated_output_tokens=summary_cost["estimated_output_tokens"],
            estimated_cost_usd=summary_cost["estimated_cost_usd"],
        ),
        vision_models=[ModelOption(**m) for m in VISION_MODELS],
        text_models=[ModelOption(**m) for m in TEXT_MODELS],
        api_key_set=bool(config.openai_api_key),
    )


@router.put("/openai", response_model=OpenAISettings)
async def update_openai_settings(
    db: DbSession,
    admin: AdminUser,
    data: OpenAISettingsUpdate,
) -> OpenAISettings:
    """Update OpenAI configuration settings (admin only)."""
    from app.config import get_settings
    from app.models.ai_settings import (
        VISION_MODELS,
        TEXT_MODELS,
        OPENAI_MODEL_PRICING,
        estimate_vision_cost,
        estimate_summary_cost,
    )
    from app.ai import _reset_classifier_cache

    ai_settings = await get_or_create_ai_settings(db)

    # Validate and update vision settings
    if data.vision_enabled is not None:
        ai_settings.vision_enabled = data.vision_enabled
    if data.vision_model is not None:
        if data.vision_model not in OPENAI_MODEL_PRICING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid vision model: {data.vision_model}",
            )
        ai_settings.vision_model = data.vision_model
    if data.vision_max_tokens is not None:
        if not 100 <= data.vision_max_tokens <= 4096:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vision_max_tokens must be between 100 and 4096",
            )
        ai_settings.vision_max_tokens = data.vision_max_tokens
    if data.vision_temperature is not None:
        if not 0.0 <= data.vision_temperature <= 2.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vision_temperature must be between 0.0 and 2.0",
            )
        ai_settings.vision_temperature = data.vision_temperature

    # Validate and update summary settings
    if data.summary_enabled is not None:
        ai_settings.summary_enabled = data.summary_enabled
    if data.summary_model is not None:
        if data.summary_model not in OPENAI_MODEL_PRICING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid summary model: {data.summary_model}",
            )
        ai_settings.summary_model = data.summary_model
    if data.summary_max_tokens is not None:
        if not 50 <= data.summary_max_tokens <= 2048:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="summary_max_tokens must be between 50 and 2048",
            )
        ai_settings.summary_max_tokens = data.summary_max_tokens
    if data.summary_temperature is not None:
        if not 0.0 <= data.summary_temperature <= 2.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="summary_temperature must be between 0.0 and 2.0",
            )
        ai_settings.summary_temperature = data.summary_temperature

    await db.commit()
    await db.refresh(ai_settings)

    # Reset the classifier cache so new settings are used
    _reset_classifier_cache()

    config = get_settings()

    # Get updated cost estimates
    vision_cost = estimate_vision_cost(ai_settings.vision_model)
    summary_cost = estimate_summary_cost(ai_settings.summary_model)

    return OpenAISettings(
        vision_enabled=ai_settings.vision_enabled,
        vision_model=ai_settings.vision_model,
        vision_max_tokens=ai_settings.vision_max_tokens,
        vision_temperature=ai_settings.vision_temperature,
        vision_cost_estimate=CostEstimate(
            model=vision_cost["model"],
            estimated_input_tokens=vision_cost["estimated_input_tokens"],
            estimated_output_tokens=vision_cost["estimated_output_tokens"],
            estimated_cost_usd=vision_cost["estimated_cost_usd"],
            cost_per_image_usd=vision_cost["cost_per_image_usd"],
        ),
        summary_enabled=ai_settings.summary_enabled,
        summary_model=ai_settings.summary_model,
        summary_max_tokens=ai_settings.summary_max_tokens,
        summary_temperature=ai_settings.summary_temperature,
        summary_cost_estimate=CostEstimate(
            model=summary_cost["model"],
            estimated_input_tokens=summary_cost["estimated_input_tokens"],
            estimated_output_tokens=summary_cost["estimated_output_tokens"],
            estimated_cost_usd=summary_cost["estimated_cost_usd"],
        ),
        vision_models=[ModelOption(**m) for m in VISION_MODELS],
        text_models=[ModelOption(**m) for m in TEXT_MODELS],
        api_key_set=bool(config.openai_api_key),
    )


# ============== Language Settings ==============


import re as _re_lang


class LanguageSettings(BaseModel):
    """Languages the AI generates content in."""

    supported_languages: list[str]
    default_language: str


class LanguageSettingsUpdate(BaseModel):
    """Update payload for language settings."""

    supported_languages: list[str] | None = None
    default_language: str | None = None


_LANGUAGE_CODE_PATTERN = _re_lang.compile(r"^[a-z]{2}(-[a-z]{2})?$")


def _normalize_language_codes(codes: list[str]) -> list[str]:
    """Lowercase, strip, dedupe, and validate ISO-style language codes."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in codes:
        code = raw.strip().lower()
        if not code or code in seen:
            continue
        if not _LANGUAGE_CODE_PATTERN.match(code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid language code: {raw!r} (use ISO codes like 'en', 'no', 'de')",
            )
        seen.add(code)
        out.append(code)
    return out


@router.get("/languages", response_model=LanguageSettings)
async def get_language_settings(
    db: DbSession,
    admin: AdminUser,
) -> LanguageSettings:
    """Get the languages the AI generates content in (admin only)."""
    ai_settings = await get_or_create_ai_settings(db)
    return LanguageSettings(
        supported_languages=list(ai_settings.supported_languages or ["en"]),
        default_language=ai_settings.default_language or "en",
    )


@router.put("/languages", response_model=LanguageSettings)
async def update_language_settings(
    db: DbSession,
    admin: AdminUser,
    data: LanguageSettingsUpdate,
) -> LanguageSettings:
    """Update language settings (admin only).

    - At least one language is required.
    - default_language must be present in supported_languages.
    - Existing items are NOT re-translated when adding a language.
    """
    from app.ai import _reset_classifier_cache

    ai_settings = await get_or_create_ai_settings(db)

    if data.supported_languages is not None:
        codes = _normalize_language_codes(data.supported_languages)
        if not codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="supported_languages must contain at least one language",
            )
        ai_settings.supported_languages = codes

    if data.default_language is not None:
        default = data.default_language.strip().lower()
        if not _LANGUAGE_CODE_PATTERN.match(default):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid default_language: {data.default_language!r}",
            )
        if default not in (ai_settings.supported_languages or []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="default_language must be one of supported_languages",
            )
        ai_settings.default_language = default

    await db.commit()
    await db.refresh(ai_settings)

    _reset_classifier_cache()

    return LanguageSettings(
        supported_languages=list(ai_settings.supported_languages),
        default_language=ai_settings.default_language,
    )
