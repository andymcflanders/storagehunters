"""Location API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.activity import ActionEnum
from app.models.container import Container
from app.models.item import Item
from app.models.location import Location
from app.schemas.location import (
    ContainerSummary,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    LocationWithContainers,
)
from app.services.activity_logger import ActivityLogger

router = APIRouter()


@router.get("", response_model=list[LocationResponse])
async def list_locations(db: DbSession) -> list[LocationResponse]:
    """List all locations."""
    result = await db.execute(select(Location).order_by(Location.sort_order, Location.name))
    locations = result.scalars().all()
    return [LocationResponse.model_validate(loc) for loc in locations]


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> LocationResponse:
    """Create a new location."""
    location = Location(**location_data.model_dump())
    db.add(location)
    await db.flush()

    # Log activity
    logger = ActivityLogger(db)
    await logger.log_created(
        user_id=current_user.id,
        entity_type="location",
        entity_id=location.id,
        entity_name=location.name,
    )

    return LocationResponse.model_validate(location)


@router.get("/{location_id}", response_model=LocationWithContainers)
async def get_location(location_id: UUID, db: DbSession) -> LocationWithContainers:
    """Get a location with its containers."""
    result = await db.execute(
        select(Location)
        .where(Location.id == location_id)
        .options(selectinload(Location.containers))
    )
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    # Get item counts for containers
    container_ids = [c.id for c in location.containers]
    item_counts: dict[UUID, int] = {}
    if container_ids:
        count_result = await db.execute(
            select(Item.container_id, func.count(Item.id))
            .where(Item.container_id.in_(container_ids))
            .group_by(Item.container_id)
        )
        item_counts = dict(count_result.all())

    containers = [
        ContainerSummary(
            id=c.id,
            name=c.name,
            qr_code=c.qr_code,
            item_count=item_counts.get(c.id, 0),
        )
        for c in location.containers
        if c.parent_container_id is None  # Only top-level containers
    ]

    return LocationWithContainers(
        **LocationResponse.model_validate(location).model_dump(),
        containers=containers,
    )


@router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    location_data: LocationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> LocationResponse:
    """Update a location."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    old_values = {}
    new_values = {}
    update_data = location_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        old_value = getattr(location, field)
        if old_value != value:
            old_values[field] = old_value
            new_values[field] = value
            setattr(location, field, value)

    if old_values:
        logger = ActivityLogger(db)
        await logger.log_updated(
            user_id=current_user.id,
            entity_type="location",
            entity_id=location.id,
            entity_name=location.name,
            old_values=old_values,
            new_values=new_values,
        )

    await db.flush()
    return LocationResponse.model_validate(location)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a location."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    logger = ActivityLogger(db)
    await logger.log_deleted(
        user_id=current_user.id,
        entity_type="location",
        entity_id=location.id,
        entity_name=location.name,
    )

    await db.delete(location)
