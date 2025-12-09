"""API Key management routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyCreatedResponse,
    APIKeyResponse,
    APIKeyUpdate,
)
from app.services.auth import AuthService

router = APIRouter()


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: DbSession,
    current_user: CurrentUser,
) -> list[APIKeyResponse]:
    """List all API keys for the current user."""
    auth_service = AuthService(db)
    keys = await auth_service.list_api_keys(current_user.id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> APIKeyCreatedResponse:
    """Create a new API key.

    The key value is only returned once at creation time.
    Store it securely as it cannot be retrieved again.
    """
    auth_service = AuthService(db)
    api_key, raw_key = await auth_service.create_api_key(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        scopes=[s.value for s in data.scopes],
        expires_at=data.expires_at,
    )

    response = APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        key=raw_key,
    )
    return response


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> APIKeyResponse:
    """Get an API key by ID."""
    auth_service = AuthService(db)
    api_key = await auth_service.get_api_key_by_id(key_id)

    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return APIKeyResponse.model_validate(api_key)


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: UUID,
    data: APIKeyUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> APIKeyResponse:
    """Update an API key."""
    auth_service = AuthService(db)
    api_key = await auth_service.get_api_key_by_id(key_id)

    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    if "scopes" in update_data and update_data["scopes"]:
        update_data["scopes"] = [s.value for s in update_data["scopes"]]

    for field, value in update_data.items():
        setattr(api_key, field, value)

    await db.flush()
    await db.refresh(api_key)
    return APIKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete an API key."""
    auth_service = AuthService(db)
    api_key = await auth_service.get_api_key_by_id(key_id)

    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    await auth_service.delete_api_key(api_key)
