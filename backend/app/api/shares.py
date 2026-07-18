"""Share link API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models import Container, Item, ShareLink

router = APIRouter()


# Schemas
class ShareLinkCreate(BaseModel):
    """Schema for creating a share link."""

    container_id: uuid.UUID
    allow_item_view: bool = True
    expires_in_days: int | None = None  # None = never expires


class ShareLinkResponse(BaseModel):
    """Schema for share link response."""

    id: uuid.UUID
    container_id: uuid.UUID
    token: str
    is_active: bool
    allow_item_view: bool
    expires_at: datetime | None
    created_at: datetime
    view_count: int
    share_url: str

    class Config:
        from_attributes = True


class ShareLinkListResponse(BaseModel):
    """Schema for list of share links."""

    items: list[ShareLinkResponse]
    total: int


class PublicContainerResponse(BaseModel):
    """Schema for public container view."""

    id: uuid.UUID
    name: str
    notes: str | None
    location_name: str
    item_count: int


class PublicItemResponse(BaseModel):
    """Schema for public item view."""

    id: uuid.UUID
    name: str
    description: str | None
    image_url: str | None


class PublicShareResponse(BaseModel):
    """Schema for public share view."""

    container: PublicContainerResponse
    items: list[PublicItemResponse] | None  # None if item view not allowed


# Endpoints
@router.post("", response_model=ShareLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    data: ShareLinkCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShareLinkResponse:
    """Create a new share link for a container."""
    # Verify container exists and belongs to user's location
    result = await db.execute(
        select(Container)
        .options(selectinload(Container.location))
        .where(Container.id == data.container_id)
    )
    container = result.scalar_one_or_none()

    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Calculate expiration
    expires_at = None
    if data.expires_in_days:
        from datetime import timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)

    # Create share link
    share_link = ShareLink(
        container_id=data.container_id,
        user_id=current_user.id,
        allow_item_view=data.allow_item_view,
        expires_at=expires_at,
    )
    db.add(share_link)
    await db.flush()
    await db.refresh(share_link)

    return ShareLinkResponse(
        id=share_link.id,
        container_id=share_link.container_id,
        token=share_link.token,
        is_active=share_link.is_active,
        allow_item_view=share_link.allow_item_view,
        expires_at=share_link.expires_at,
        created_at=share_link.created_at,
        view_count=share_link.view_count,
        share_url=f"/s/{share_link.token}",
    )


@router.get("", response_model=ShareLinkListResponse)
async def list_share_links(
    db: DbSession,
    current_user: CurrentUser,
    container_id: Annotated[uuid.UUID | None, Query()] = None,
) -> ShareLinkListResponse:
    """List share links created by the current user."""
    query = select(ShareLink).where(ShareLink.user_id == current_user.id)

    if container_id:
        query = query.where(ShareLink.container_id == container_id)

    query = query.order_by(ShareLink.created_at.desc())
    result = await db.execute(query)
    share_links = result.scalars().all()

    items = [
        ShareLinkResponse(
            id=link.id,
            container_id=link.container_id,
            token=link.token,
            is_active=link.is_active,
            allow_item_view=link.allow_item_view,
            expires_at=link.expires_at,
            created_at=link.created_at,
            view_count=link.view_count,
            share_url=f"/s/{link.token}",
        )
        for link in share_links
    ]

    return ShareLinkListResponse(items=items, total=len(items))


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_link(
    share_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a share link."""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.id == share_id,
            ShareLink.user_id == current_user.id,
        )
    )
    share_link = result.scalar_one_or_none()

    if not share_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )

    await db.delete(share_link)


@router.patch("/{share_id}/toggle", response_model=ShareLinkResponse)
async def toggle_share_link(
    share_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ShareLinkResponse:
    """Toggle a share link active status."""
    result = await db.execute(
        select(ShareLink).where(
            ShareLink.id == share_id,
            ShareLink.user_id == current_user.id,
        )
    )
    share_link = result.scalar_one_or_none()

    if not share_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )

    share_link.is_active = not share_link.is_active
    await db.flush()
    await db.refresh(share_link)

    return ShareLinkResponse(
        id=share_link.id,
        container_id=share_link.container_id,
        token=share_link.token,
        is_active=share_link.is_active,
        allow_item_view=share_link.allow_item_view,
        expires_at=share_link.expires_at,
        created_at=share_link.created_at,
        view_count=share_link.view_count,
        share_url=f"/s/{share_link.token}",
    )


@router.get("/public/{token}", response_model=PublicShareResponse)
async def get_public_share(
    token: str,
    db: DbSession,
) -> PublicShareResponse:
    """Get public share data (no authentication required)."""
    result = await db.execute(
        select(ShareLink)
        .options(
            selectinload(ShareLink.container).selectinload(Container.location),
            selectinload(ShareLink.container)
            .selectinload(Container.items)
            .selectinload(Item.images),
        )
        .where(ShareLink.token == token)
    )
    share_link = result.scalar_one_or_none()

    if not share_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )

    # Check if link is active
    if not share_link.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share link has been deactivated",
        )

    # Check expiration
    if share_link.expires_at and share_link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share link has expired",
        )

    # Increment view count atomically (concurrent views must not lose counts)
    share_link.view_count = ShareLink.view_count + 1

    container = share_link.container
    items = None

    if share_link.allow_item_view:
        items = [
            PublicItemResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                image_url=f"/uploads/{item.images[0].filepath}" if item.images else None,
            )
            for item in container.items
        ]

    return PublicShareResponse(
        container=PublicContainerResponse(
            id=container.id,
            name=container.name,
            notes=container.notes,
            location_name=container.location.name,
            item_count=len(container.items),
        ),
        items=items,
    )
