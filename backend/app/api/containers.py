"""Container API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.container import Container
from app.models.item import Item, ItemImage
from app.models.location import Location
from app.models.share import ShareLink
from app.models.pending_upload import PendingUpload
from app.schemas.container import (
    ContainerCreate,
    ContainerResponse,
    ContainerUpdate,
    ContainerWithItems,
    ItemSummary,
)
from app.services.activity_logger import ActivityLogger
from app.services.image_storage import ImageStorageService
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
    await db.refresh(container)

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
            selectinload(Container.items).selectinload(Item.images),
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
    storage = ImageStorageService()
    items = []
    for item in container.items:
        thumbnail_url = None
        if item.images:
            thumbnail_url = storage.get_url(item.images[0].filepath)
        items.append(ItemSummary(id=item.id, name=item.name, thumbnail_url=thumbnail_url))
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
            selectinload(Container.items).selectinload(Item.images),
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
    storage = ImageStorageService()
    items = []
    for item in container.items:
        thumbnail_url = None
        if item.images:
            thumbnail_url = storage.get_url(item.images[0].filepath)
        items.append(ItemSummary(id=item.id, name=item.name, thumbnail_url=thumbnail_url))
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
    await db.refresh(container)
    return ContainerResponse.model_validate(container)


@router.delete("/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_container(
    container_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    mode: str = "fail",  # "fail", "recursive", or "transfer"
    transfer_to: UUID | None = None,
) -> None:
    """Delete a container.

    Args:
        container_id: The container to delete
        mode: How to handle items/children:
            - "fail": Fail if container has items or children (default)
            - "recursive": Delete all items and nested containers recursively
            - "transfer": Move items to another container (requires transfer_to)
        transfer_to: Target container ID when mode="transfer"
    """
    result = await db.execute(
        select(Container)
        .where(Container.id == container_id)
        .options(
            selectinload(Container.items).selectinload(Item.images),
            selectinload(Container.child_containers),
        )
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Count items and children (including nested)
    async def count_nested(cont_id: UUID) -> tuple[int, int]:
        """Count items and child containers recursively."""
        res = await db.execute(
            select(Container)
            .where(Container.id == cont_id)
            .options(
                selectinload(Container.items),
                selectinload(Container.child_containers),
            )
        )
        cont = res.scalar_one_or_none()
        if not cont:
            return 0, 0

        items = len(cont.items)
        children = len(cont.child_containers)

        for child in cont.child_containers:
            child_items, child_children = await count_nested(child.id)
            items += child_items
            children += child_children

        return items, children

    total_items, total_children = await count_nested(container_id)
    has_contents = total_items > 0 or total_children > 0

    if mode == "fail" and has_contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Container has {total_items} item(s) and {total_children} nested container(s). Use mode='recursive' to delete all, or mode='transfer' to move items.",
        )

    if mode == "transfer":
        if not transfer_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="transfer_to is required when mode='transfer'",
            )
        if transfer_to == container_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer items to the same container being deleted",
            )

        # Verify target container exists
        target_result = await db.execute(
            select(Container).where(Container.id == transfer_to)
        )
        target_container = target_result.scalar_one_or_none()
        if not target_container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target container not found",
            )

        # Transfer all items from this container and nested containers
        async def transfer_items(cont_id: UUID):
            res = await db.execute(
                select(Container)
                .where(Container.id == cont_id)
                .options(
                    selectinload(Container.items),
                    selectinload(Container.child_containers),
                )
            )
            cont = res.scalar_one_or_none()
            if not cont:
                return

            # Move items to target
            for item in cont.items:
                item.container_id = transfer_to

            # Recursively handle children
            for child in cont.child_containers:
                await transfer_items(child.id)

        await transfer_items(container_id)
        await db.flush()

    # Helper to delete related records for a container
    async def delete_container_relations(cont_id: UUID):
        """Delete share links and pending uploads for a container."""
        # Delete share links
        share_links_result = await db.execute(
            select(ShareLink).where(ShareLink.container_id == cont_id)
        )
        for share_link in share_links_result.scalars().all():
            await db.delete(share_link)

        # Delete pending uploads
        pending_result = await db.execute(
            select(PendingUpload).where(PendingUpload.container_id == cont_id)
        )
        for pending in pending_result.scalars().all():
            await db.delete(pending)

    if mode == "recursive":
        # Delete all items and their images recursively
        storage = ImageStorageService()

        async def delete_recursive(cont_id: UUID):
            res = await db.execute(
                select(Container)
                .where(Container.id == cont_id)
                .options(
                    selectinload(Container.items).selectinload(Item.images),
                    selectinload(Container.child_containers),
                )
            )
            cont = res.scalar_one_or_none()
            if not cont:
                return

            # Delete child containers first (recursively)
            for child in cont.child_containers:
                await delete_recursive(child.id)

            # Delete items and their images
            for item in cont.items:
                for image in item.images:
                    await storage.delete_image(image.filepath)
                    await db.delete(image)
                await db.delete(item)

            # Delete related records (share links, pending uploads)
            await delete_container_relations(cont_id)

            # Delete the container
            await db.delete(cont)

        # Delete recursively
        await delete_recursive(container_id)
    else:
        # Mode is "fail" (with no contents) or "transfer" (items already moved)
        # Still need to delete any empty child containers
        async def delete_empty_children(cont_id: UUID):
            res = await db.execute(
                select(Container)
                .where(Container.id == cont_id)
                .options(selectinload(Container.child_containers))
            )
            cont = res.scalar_one_or_none()
            if not cont:
                return

            for child in cont.child_containers:
                await delete_empty_children(child.id)

            # Delete related records (share links, pending uploads)
            await delete_container_relations(cont_id)

            await db.delete(cont)

        await delete_empty_children(container_id)

    logger = ActivityLogger(db)
    await logger.log_deleted(
        user_id=current_user.id,
        entity_type="container",
        entity_id=container.id,
        entity_name=container.name,
    )


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
