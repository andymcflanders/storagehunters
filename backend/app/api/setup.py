"""First-run setup wizard.

Public endpoints (no auth required) that bootstrap a fresh install:
- GET /setup/status — does this instance need onboarding?
- POST /setup/complete — atomic admin-creation + initial config.

`complete` is one-shot: it refuses if any user already exists, so an
attacker can't take over an existing install by hitting the public
endpoint. The frontend uses `status` to decide whether to redirect
into the wizard.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.ai import _reset_classifier_cache
from app.api.deps import DbSession
from app.models.ai_settings import AISettings
from app.models.location import Location
from app.models.user import Language, User, UserRole
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter()


class SetupStatus(BaseModel):
    """Whether this instance still needs onboarding."""

    needs_setup: bool


class FirstLocationInput(BaseModel):
    """Optional first location captured during onboarding."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    address: str | None = None


class SetupCompleteRequest(BaseModel):
    """Onboarding payload. Only `admin_*` fields are required."""

    admin_name: str = Field(..., min_length=1, max_length=255)
    admin_email: str | None = None
    admin_password: str | None = None
    admin_language: Literal["en", "no"] = "en"

    openai_api_key: str | None = None
    supported_languages: list[str] | None = None
    default_language: str | None = None

    first_location: FirstLocationInput | None = None


class SetupCompleteResponse(BaseModel):
    """Result of completing the wizard."""

    user: UserResponse
    first_location_id: UUID | None = None


@router.get("/status", response_model=SetupStatus)
async def get_setup_status(db: DbSession) -> SetupStatus:
    """Public probe — is this instance still in 'no users' state?"""
    user_count = await db.scalar(select(func.count(User.id)))
    return SetupStatus(needs_setup=(user_count or 0) == 0)


@router.post("/complete", response_model=SetupCompleteResponse)
async def complete_setup(
    request: SetupCompleteRequest,
    response: Response,
    db: DbSession,
) -> SetupCompleteResponse:
    """Run the wizard atomically and log the new admin in.

    Refuses if any user already exists — that's the safety latch that
    keeps this public endpoint from being abused after the first user
    is created.
    """
    user_count = await db.scalar(select(func.count(User.id))) or 0
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup has already been completed",
        )

    auth_service = AuthService(db)

    # 1. Create the admin user.
    requires_password = bool(request.admin_password)
    password_hash = (
        auth_service.hash_password(request.admin_password)
        if request.admin_password
        else None
    )

    admin = User(
        name=request.admin_name.strip(),
        email=(request.admin_email.strip() or None) if request.admin_email else None,
        password_hash=password_hash,
        requires_password=requires_password,
        role=UserRole.ADMIN,
        language=Language(request.admin_language),
        is_active=True,
    )
    db.add(admin)
    await db.flush()

    # 2. Update AISettings (singleton row — create if missing).
    ai_result = await db.execute(select(AISettings).limit(1))
    ai_settings = ai_result.scalar_one_or_none()
    if not ai_settings:
        ai_settings = AISettings()
        db.add(ai_settings)
        await db.flush()

    if request.openai_api_key is not None:
        ai_settings.openai_api_key = request.openai_api_key.strip() or None
    if request.supported_languages:
        ai_settings.supported_languages = [
            code.strip().lower() for code in request.supported_languages if code.strip()
        ]
    if request.default_language:
        default = request.default_language.strip().lower()
        if default in (ai_settings.supported_languages or []):
            ai_settings.default_language = default

    # 3. Optional first location.
    first_location_id: UUID | None = None
    if request.first_location:
        location = Location(
            name=request.first_location.name.strip(),
            description=request.first_location.description,
            address=request.first_location.address,
        )
        db.add(location)
        await db.flush()
        first_location_id = location.id

    await db.commit()
    await db.refresh(admin)

    # AI classifier holds the previous (empty) settings in its cache;
    # bust it so the next call sees the new key + language config.
    _reset_classifier_cache()

    # 4. Log the admin in by creating a session and setting the cookie.
    session = await auth_service.create_session(admin)
    response.set_cookie(
        key="session_token",
        value=session.token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return SetupCompleteResponse(
        user=UserResponse.model_validate(admin),
        first_location_id=first_location_id,
    )
