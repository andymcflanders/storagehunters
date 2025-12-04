"""Container API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.container import Container
from app.models.item import Item
from app.models.location import Location
from app.schemas.container import (
    ContainerCreate,
    ContainerResponse,
    ContainerUpdate,
    ContainerWithItems,
    ItemSummary,
)
from app.services.activity_logger import ActivityLogger
from app.services.qr_generator import QRGeneratorService

router = APIRouter()


async def build_container_path(
    container: Container, db
) -> list[dict[str, str]]:
    """Build the full path from location to container."""
    path = []

    # Add location
    result = await db.execute(
        select(Location).where(Location.id == container.location_id)
    )
    location = result.scalar_one()
    path.append({"id": str(location.id), "name": location.name, "type": "location"})

    # Add parent containers
    parent_path = []
    parent_id = container.parent_container_id
    while parent_id:
        result = await db.execute(select(Container).where(Container.id == parent_id))
        parent = result.scalar_one_or_none()
        if parent:
            parent_path.append(
                {"id": str(parent.id), "name": parent.name, "type": "container"}
            )
            parent_id = parent.parent_container_id
        else:
            break

    # Reverse to get top-down order
    path.extend(reversed(parent_path))
    return path


@router.get("", response_model=list[ContainerResponse])
async def list_containers(
    db: DbSession,
    location_id: UUID | None = None,
) -> list[ContainerResponse]:
    """List containers, optionally filtered by location."""
    query = select(Container).order_by(Container.name)
    if location_id:
        query = query.where(Container.location_id == location_id)

    result = await db.execute(query)
    containers = result.scalars().all()
    return [ContainerResponse.model_validate(c) for c in containers]


@router.post("", response_model=ContainerResponse, status_code=status.HTTP_201_CREATED)
async def create_container(
    container_data: ContainerCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ContainerResponse:
    """Create a new container."""
    # Verify location exists
    result = await db.execute(
        select(Location).where(Location.id == container_data.location_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location not found",
        )

    # Verify parent container exists if specified
    if container_data.parent_container_id:
        result = await db.execute(
            select(Container).where(Container.id == container_data.parent_container_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent container not found",
            )

    container = Container(**container_data.model_dump())
    db.add(container)
    await db.flush()

    logger = ActivityLogger(db)
    await logger.log_created(
        user_id=current_user.id,
        entity_type="container",
        entity_id=container.id,
        entity_name=container.name,
    )

    return ContainerResponse.model_validate(container)


@router.get("/qr/{qr_code}", response_model=ContainerWithItems)
async def get_container_by_qr(qr_code: str, db: DbSession) -> ContainerWithItems:
    """Get a container by QR code."""
    result = await db.execute(
        select(Container)
        .where(Container.qr_code == qr_code)
        .options(
            selectinload(Container.items),
            selectinload(Container.child_containers),
        )
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    path = await build_container_path(container, db)
    items = [
        ItemSummary(id=item.id, name=item.name, thumbnail_url=None)
        for item in container.items
    ]
    children = [ContainerResponse.model_validate(c) for c in container.child_containers]

    return ContainerWithItems(
        **ContainerResponse.model_validate(container).model_dump(),
        items=items,
        child_containers=children,
        path=path,
    )


@router.get("/{container_id}", response_model=ContainerWithItems)
async def get_container(container_id: UUID, db: DbSession) -> ContainerWithItems:
    """Get a container with its items."""
    result = await db.execute(
        select(Container)
        .where(Container.id == container_id)
        .options(
            selectinload(Container.items),
            selectinload(Container.child_containers),
        )
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    path = await build_container_path(container, db)
    items = [
        ItemSummary(id=item.id, name=item.name, thumbnail_url=None)
        for item in container.items
    ]
    children = [ContainerResponse.model_validate(c) for c in container.child_containers]

    return ContainerWithItems(
        **ContainerResponse.model_validate(container).model_dump(),
        items=items,
        child_containers=children,
        path=path,
    )


@router.patch("/{container_id}", response_model=ContainerResponse)
async def update_container(
    container_id: UUID,
    container_data: ContainerUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ContainerResponse:
    """Update a container."""
    result = await db.execute(select(Container).where(Container.id == container_id))
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    old_values = {}
    new_values = {}
    update_data = container_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        old_value = getattr(container, field)
        if old_value != value:
            old_values[field] = str(old_value) if old_value else None
            new_values[field] = str(value) if value else None
            setattr(container, field, value)

    if old_values:
        logger = ActivityLogger(db)
        await logger.log_updated(
            user_id=current_user.id,
            entity_type="container",
            entity_id=container.id,
            entity_name=container.name,
            old_values=old_values,
            new_values=new_values,
        )

    await db.flush()
    return ContainerResponse.model_validate(container)


@router.delete("/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_container(
    container_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a container."""
    result = await db.execute(select(Container).where(Container.id == container_id))
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    logger = ActivityLogger(db)
    await logger.log_deleted(
        user_id=current_user.id,
        entity_type="container",
        entity_id=container.id,
        entity_name=container.name,
    )

    await db.delete(container)


@router.get("/{container_id}/qr")
async def get_container_qr_code(container_id: UUID, db: DbSession) -> Response:
    """Get the QR code image for a container."""
    result = await db.execute(select(Container).where(Container.id == container_id))
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    qr_service = QRGeneratorService()
    image_bytes = qr_service.generate_container_qr(container.qr_code)

    return Response(content=image_bytes, media_type="image/png")


@router.get("/{container_id}/path")
async def get_container_path(
    container_id: UUID, db: DbSession
) -> list[dict[str, str]]:
    """Get the full path to a container."""
    result = await db.execute(select(Container).where(Container.id == container_id))
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    return await build_container_path(container, db)
