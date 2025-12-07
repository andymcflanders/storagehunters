"""Inventory API routes for God View."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.container import Container
from app.models.item import Item, ItemImage
from app.models.location import Location
from app.models.user import User
from app.schemas.inventory import (
    ContainerMoveRequest,
    GodViewContainer,
    GodViewItem,
    GodViewLocation,
    GodViewResponse,
    UserInfo,
)
from app.services.image_storage import ImageStorageService

router = APIRouter()


def get_thumbnail_url(item: Item) -> str | None:
    """Get the thumbnail URL for an item."""
    if not item.images:
        return None
    # Use primary image if set, otherwise first image
    if item.primary_image_id:
        for img in item.images:
            if img.id == item.primary_image_id:
                return f"/uploads/{img.filepath}"
    return f"/uploads/{item.images[0].filepath}"


def build_container_tree(
    containers: list[Container],
    parent_id: UUID | None,
    item_counts: dict[UUID, int],
) -> list[GodViewContainer]:
    """Recursively build container tree with nested children."""
    result = []
    for container in containers:
        if container.parent_container_id == parent_id:
            # Build items for this container
            items = [
                GodViewItem(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    size=item.size,
                    condition=item.condition.value if item.condition else "good",
                    seasonal=item.seasonal.value if item.seasonal else "none",
                    owner_id=item.owner_id,
                    owner_name=item.owner.name if item.owner else None,
                    thumbnail_url=get_thumbnail_url(item),
                    value_estimate=float(item.value_estimate) if item.value_estimate else None,
                    ai_name=item.ai_name,
                    ai_name_no=item.ai_name_no,
                    ai_description=item.ai_description,
                    ai_description_no=item.ai_description_no,
                    ai_processed=item.ai_processed,
                    needs_review=item.needs_review,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                for item in container.items
            ]

            # Recursively build children
            children = build_container_tree(containers, container.id, item_counts)

            result.append(
                GodViewContainer(
                    id=container.id,
                    name=container.name,
                    notes=container.notes,
                    qr_code=container.qr_code,
                    location_id=container.location_id,
                    parent_container_id=container.parent_container_id,
                    items=items,
                    children=children,
                    item_count=len(items),
                )
            )
    return result


@router.get("/tree", response_model=GodViewResponse)
async def get_inventory_tree(
    db: DbSession,
    current_user: CurrentUser,
) -> GodViewResponse:
    """Get complete inventory hierarchy for God View.

    Returns all locations with nested containers and items in a single response.
    """
    # Load all locations
    locations_result = await db.execute(
        select(Location).order_by(Location.sort_order, Location.name)
    )
    locations_list = list(locations_result.scalars().all())

    # Load all containers with items eagerly loaded
    containers_result = await db.execute(
        select(Container)
        .options(
            selectinload(Container.items).selectinload(Item.images),
            selectinload(Container.items).selectinload(Item.owner),
        )
        .order_by(Container.name)
    )
    all_containers = list(containers_result.scalars().all())

    # Group containers by location
    containers_by_location: dict[UUID, list[Container]] = {}
    for container in all_containers:
        if container.location_id not in containers_by_location:
            containers_by_location[container.location_id] = []
        containers_by_location[container.location_id].append(container)

    # Get item counts by container
    item_counts_result = await db.execute(
        select(Item.container_id, func.count(Item.id))
        .group_by(Item.container_id)
    )
    item_counts = dict(item_counts_result.all())

    # Build location tree
    god_view_locations = []
    total_containers = 0
    total_items = 0

    for location in locations_list:
        location_containers = containers_by_location.get(location.id, [])

        # Build container tree starting from top-level (parent_id = None)
        container_tree = build_container_tree(
            location_containers, None, item_counts
        )

        # Count items in this location
        location_item_count = sum(
            len(c.items) for c in location_containers
        )

        god_view_locations.append(
            GodViewLocation(
                id=location.id,
                name=location.name,
                description=location.description,
                address=location.address,
                sort_order=location.sort_order,
                containers=container_tree,
                container_count=len([c for c in location_containers if c.parent_container_id is None]),
                item_count=location_item_count,
            )
        )

        total_containers += len(location_containers)
        total_items += location_item_count

    # Load users for owner dropdown
    users_result = await db.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(User.name)
    )
    users_list = [
        UserInfo(id=u.id, name=u.name)
        for u in users_result.scalars().all()
    ]

    return GodViewResponse(
        locations=god_view_locations,
        users=users_list,
        total_locations=len(locations_list),
        total_containers=total_containers,
        total_items=total_items,
    )


async def check_circular_reference(
    db: DbSession,
    container_id: UUID,
    new_parent_id: UUID | None,
) -> bool:
    """Check if moving container to new_parent would create a circular reference.

    Returns True if circular reference would be created.
    """
    if new_parent_id is None:
        return False
    if container_id == new_parent_id:
        return True

    # Walk up the tree from new_parent
    current_id = new_parent_id
    visited: set[UUID] = set()

    while current_id:
        if current_id in visited:
            return True  # Already circular
        if current_id == container_id:
            return True  # Would create circular
        visited.add(current_id)

        result = await db.execute(
            select(Container.parent_container_id)
            .where(Container.id == current_id)
        )
        parent_id = result.scalar_one_or_none()
        current_id = parent_id

    return False


@router.post("/{container_id}/move")
async def move_container(
    container_id: UUID,
    move_data: ContainerMoveRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Move a container to a different location or parent container.

    - If location_id is provided, moves container to that location (as top-level or nested)
    - If parent_container_id is provided, makes it a child of that container
    - If parent_container_id is None, makes it a top-level container in the location
    """
    # Get the container
    result = await db.execute(
        select(Container).where(Container.id == container_id)
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Determine target location
    target_location_id = move_data.location_id or container.location_id

    # If moving to a parent container, get its location
    if move_data.parent_container_id:
        parent_result = await db.execute(
            select(Container).where(Container.id == move_data.parent_container_id)
        )
        parent_container = parent_result.scalar_one_or_none()
        if not parent_container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent container not found",
            )
        # Use parent's location
        target_location_id = parent_container.location_id

        # Check for circular reference
        is_circular = await check_circular_reference(
            db, container_id, move_data.parent_container_id
        )
        if is_circular:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move container into itself or its descendants",
            )
    elif move_data.location_id:
        # Verify location exists
        loc_result = await db.execute(
            select(Location).where(Location.id == move_data.location_id)
        )
        if not loc_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target location not found",
            )

    # Update container
    container.location_id = target_location_id
    container.parent_container_id = move_data.parent_container_id

    await db.flush()

    return {
        "success": True,
        "container_id": str(container_id),
        "location_id": str(target_location_id),
        "parent_container_id": str(move_data.parent_container_id) if move_data.parent_container_id else None,
    }
