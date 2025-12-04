"""Tag API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.item import ItemTag
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagResponse

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(db: DbSession) -> list[TagResponse]:
    """List all tags."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [TagResponse.model_validate(t) for t in tags]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> TagResponse:
    """Create a new tag."""
    # Check if tag exists
    result = await db.execute(select(Tag).where(Tag.name == tag_data.name.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already exists",
        )

    tag = Tag(name=tag_data.name.lower(), user_created=True)
    db.add(tag)
    await db.flush()
    return TagResponse.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
async def rename_tag(
    tag_id: UUID,
    new_name: str,
    db: DbSession,
    current_user: CurrentUser,
) -> TagResponse:
    """Rename a tag."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    # Check if new name already exists
    result = await db.execute(select(Tag).where(Tag.name == new_name.lower()))
    existing = result.scalar_one_or_none()
    if existing and existing.id != tag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag name already exists",
        )

    tag.name = new_name.lower()
    await db.flush()
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a tag."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await db.delete(tag)


@router.post("/merge")
async def merge_tags(
    source_tag_ids: list[UUID],
    target_tag_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> TagResponse:
    """Merge multiple tags into one."""
    # Get target tag
    result = await db.execute(select(Tag).where(Tag.id == target_tag_id))
    target_tag = result.scalar_one_or_none()
    if not target_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target tag not found",
        )

    # Move all item associations from source tags to target
    for source_id in source_tag_ids:
        if source_id == target_tag_id:
            continue

        result = await db.execute(select(Tag).where(Tag.id == source_id))
        source_tag = result.scalar_one_or_none()
        if not source_tag:
            continue

        # Get all items with source tag
        result = await db.execute(select(ItemTag).where(ItemTag.tag_id == source_id))
        source_links = result.scalars().all()

        for link in source_links:
            # Check if item already has target tag
            result = await db.execute(
                select(ItemTag).where(
                    ItemTag.item_id == link.item_id, ItemTag.tag_id == target_tag_id
                )
            )
            if not result.scalar_one_or_none():
                new_link = ItemTag(item_id=link.item_id, tag_id=target_tag_id)
                db.add(new_link)

            await db.delete(link)

        # Delete source tag
        await db.delete(source_tag)

    await db.flush()
    return TagResponse.model_validate(target_tag)
