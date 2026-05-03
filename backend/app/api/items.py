"""Item API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.container import Container
from app.models.item import Item, ItemImage, ItemTag
from app.models.location import Location
from app.models.tag import Tag
from app.schemas.item import (
    ContainerPath,
    ItemCreate,
    ItemImageResponse,
    ItemResponse,
    ItemUpdate,
    ItemWithDetails,
    OwnerInfo,
    TagInfo,
)
from app.services.activity_logger import ActivityLogger
from app.services.image_storage import ImageStorageService

router = APIRouter()


async def build_item_path(item: Item, db) -> list[ContainerPath]:
    """Build the full path for an item."""
    path = []

    # Get container
    result = await db.execute(select(Container).where(Container.id == item.container_id))
    container = result.scalar_one()

    # Get location
    result = await db.execute(select(Location).where(Location.id == container.location_id))
    location = result.scalar_one()
    path.append(ContainerPath(id=location.id, name=location.name, type="location"))

    # Build container path
    container_path = []
    current_container = container
    while current_container:
        container_path.append(
            ContainerPath(id=current_container.id, name=current_container.name, type="container")
        )
        if current_container.parent_container_id:
            result = await db.execute(
                select(Container).where(Container.id == current_container.parent_container_id)
            )
            current_container = result.scalar_one_or_none()
        else:
            break

    # Add containers in reverse order (top-down)
    path.extend(reversed(container_path))
    return path


@router.get("", response_model=list[ItemResponse])
async def list_items(
    db: DbSession,
    container_id: UUID | None = None,
    owner_id: UUID | None = None,
) -> list[ItemResponse]:
    """List items, optionally filtered."""
    query = select(Item).order_by(Item.name)
    if container_id:
        query = query.where(Item.container_id == container_id)
    if owner_id:
        query = query.where(Item.owner_id == owner_id)

    result = await db.execute(query)
    items = result.scalars().all()
    return [ItemResponse.model_validate(i) for i in items]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemResponse:
    """Create a new item."""
    # Verify container exists
    result = await db.execute(select(Container).where(Container.id == item_data.container_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Container not found",
        )

    item = Item(**item_data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)

    logger = ActivityLogger(db)
    await logger.log_created(
        user_id=current_user.id,
        entity_type="item",
        entity_id=item.id,
        entity_name=item.name,
    )

    return ItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=ItemWithDetails)
async def get_item(item_id: UUID, db: DbSession) -> ItemWithDetails:
    """Get an item with full details."""
    result = await db.execute(
        select(Item)
        .where(Item.id == item_id)
        .options(
            selectinload(Item.images),
            selectinload(Item.item_tags).selectinload(ItemTag.tag),
            selectinload(Item.owner),
            selectinload(Item.suggested_owner),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    path = await build_item_path(item, db)
    storage = ImageStorageService()

    images = [
        ItemImageResponse(
            id=img.id,
            filename=img.filename,
            filepath=storage.get_url(img.filepath),
            ai_tags=img.ai_tags or [],
            ai_description=img.ai_description,
            ai_processed=img.ai_processed,
            created_at=img.created_at,
        )
        for img in item.images
    ]

    tags = [TagInfo(id=it.tag.id, name=it.tag.name) for it in item.item_tags]

    owner = None
    if item.owner:
        owner = OwnerInfo(
            id=item.owner.id, name=item.owner.name, avatar_url=item.owner.avatar_url
        )

    suggested_owner = None
    if item.suggested_owner:
        suggested_owner = OwnerInfo(
            id=item.suggested_owner.id,
            name=item.suggested_owner.name,
            avatar_url=item.suggested_owner.avatar_url,
        )

    return ItemWithDetails(
        **ItemResponse.model_validate(item).model_dump(),
        images=images,
        tags=tags,
        owner=owner,
        suggested_owner=suggested_owner,
        path=path,
        related_items=[],
    )


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: UUID,
    item_data: ItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemResponse:
    """Update an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    old_values = {}
    new_values = {}
    update_data = item_data.model_dump(exclude_unset=True)

    # clear_suggestion is a write-only flag, not a column; pop it before
    # the generic field loop below.
    clear_suggestion = update_data.pop("clear_suggestion", False)
    dismiss_outgrown = update_data.pop("dismiss_outgrown", None)

    for field, value in update_data.items():
        old_value = getattr(item, field)
        if old_value != value:
            old_values[field] = str(old_value) if old_value else None
            new_values[field] = str(value) if value else None
            setattr(item, field, value)

    if clear_suggestion:
        item.suggested_owner_id = None
        item.owner_suggestion_reason = None
    elif "owner_id" in update_data and item.owner_id is not None:
        # User picked an owner manually — drop the suggestion so it
        # doesn't sit in the DB forever pointing at a now-irrelevant
        # candidate.
        item.suggested_owner_id = None
        item.owner_suggestion_reason = None

    if dismiss_outgrown is True:
        from datetime import datetime as _dt
        item.outgrown_dismissed_at = _dt.utcnow()
    elif dismiss_outgrown is False:
        item.outgrown_dismissed_at = None

    if old_values:
        logger = ActivityLogger(db)
        await logger.log_updated(
            user_id=current_user.id,
            entity_type="item",
            entity_id=item.id,
            entity_name=item.name,
            old_values=old_values,
            new_values=new_values,
        )

    await db.flush()
    await db.refresh(item)
    return ItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    logger = ActivityLogger(db)
    await logger.log_deleted(
        user_id=current_user.id,
        entity_type="item",
        entity_id=item.id,
        entity_name=item.name,
    )

    await db.delete(item)


@router.post("/{item_id}/images", response_model=ItemImageResponse)
async def upload_image(
    item_id: UUID,
    file: UploadFile,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemImageResponse:
    """Upload an image for an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type",
        )

    storage = ImageStorageService()
    content = await file.read()
    filename, filepath = await storage.save_image(item_id, file.filename or "image.jpg", content)

    image = ItemImage(
        item_id=item_id,
        filename=filename,
        filepath=filepath,
        uploaded_by=current_user.id,
    )
    db.add(image)
    await db.commit()  # Commit before queuing task so worker can find the image

    # Queue background AI processing
    from app.worker.tasks import process_image_ai
    process_image_ai.delay(str(image.id))

    return ItemImageResponse(
        id=image.id,
        filename=image.filename,
        filepath=storage.get_url(image.filepath),
        ai_tags=image.ai_tags or [],
        ai_description=image.ai_description,
        ai_processed=image.ai_processed,
        created_at=image.created_at,
    )


@router.delete("/{item_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    item_id: UUID,
    image_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete an image from an item."""
    result = await db.execute(
        select(ItemImage).where(ItemImage.id == image_id, ItemImage.item_id == item_id)
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    storage = ImageStorageService()
    await storage.delete_image(image.filepath)
    await db.delete(image)


@router.post("/{item_id}/tags", response_model=TagInfo)
async def add_tag(
    item_id: UUID,
    tag_name: str,
    db: DbSession,
    current_user: CurrentUser,
) -> TagInfo:
    """Add a tag to an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Find or create tag
    result = await db.execute(select(Tag).where(Tag.name == tag_name.lower()))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=tag_name.lower(), user_created=True)
        db.add(tag)
        await db.flush()

    # Check if already linked
    result = await db.execute(
        select(ItemTag).where(ItemTag.item_id == item_id, ItemTag.tag_id == tag.id)
    )
    if not result.scalar_one_or_none():
        item_tag = ItemTag(item_id=item_id, tag_id=tag.id)
        db.add(item_tag)
        await db.flush()

    return TagInfo(id=tag.id, name=tag.name)


@router.delete("/{item_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(
    item_id: UUID,
    tag_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Remove a tag from an item."""
    result = await db.execute(
        select(ItemTag).where(ItemTag.item_id == item_id, ItemTag.tag_id == tag_id)
    )
    item_tag = result.scalar_one_or_none()
    if not item_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found on item",
        )

    await db.delete(item_tag)


@router.post("/{item_id}/images/{image_id}/reprocess")
async def reprocess_image(
    item_id: UUID,
    image_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Trigger AI reprocessing for an image."""
    result = await db.execute(
        select(ItemImage).where(ItemImage.id == image_id, ItemImage.item_id == item_id)
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    # Reset AI processed flag and queue for reprocessing
    image.ai_processed = False
    image.ai_tags = []
    image.ai_description = None
    await db.flush()

    from app.worker.tasks import process_image_ai
    task = process_image_ai.delay(str(image.id))

    return {"status": "queued", "task_id": task.id}


@router.post("/{item_id}/process-all-images")
async def process_all_item_images(
    item_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Trigger AI processing for all unprocessed images of an item."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    from app.worker.tasks import batch_process_item_images
    task = batch_process_item_images.delay(str(item_id))

    return {"status": "queued", "task_id": task.id}


@router.post("/{item_id}/move", response_model=ItemResponse)
async def move_item(
    item_id: UUID,
    container_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemResponse:
    """Move an item to a different container."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Verify target container exists
    result = await db.execute(select(Container).where(Container.id == container_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target container not found",
        )

    # Get old container name for logging
    result = await db.execute(select(Container).where(Container.id == item.container_id))
    old_container = result.scalar_one()

    old_container_id = item.container_id
    item.container_id = container_id
    await db.flush()
    await db.refresh(item)

    logger = ActivityLogger(db)
    await logger.log_moved(
        user_id=current_user.id,
        entity_type="item",
        entity_id=item.id,
        entity_name=item.name,
        from_location=old_container.name,
        to_location=target.name,
    )

    return ItemResponse.model_validate(item)


@router.post("/{item_id}/images/{image_id}/set-primary", response_model=ItemResponse)
async def set_primary_image(
    item_id: UUID,
    image_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ItemResponse:
    """Set an image as the primary (hero) image for an item."""
    # Verify image belongs to item
    result = await db.execute(
        select(ItemImage).where(ItemImage.id == image_id, ItemImage.item_id == item_id)
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    # Get the item
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    item.primary_image_id = image_id
    await db.flush()
    await db.refresh(item)

    return ItemResponse.model_validate(item)
