"""Background tasks for StorageHub."""

import asyncio
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.item import Item, ItemImage, ItemTag
from app.models.tag import Tag
from app.worker.celery_app import celery_app


def get_ai_classifier():
    """Get the configured AI classifier."""
    from app.ai import get_classifier
    return get_classifier()


async def _process_image_async(image_id: UUID) -> dict:
    """Process an image with AI classification (async implementation)."""
    from app.services.image_storage import ImageStorageService

    async with async_session_maker() as db:
        # Get the image
        result = await db.execute(
            select(ItemImage).where(ItemImage.id == image_id)
        )
        image = result.scalar_one_or_none()

        if not image:
            return {"status": "error", "message": "Image not found"}

        if image.ai_processed:
            return {"status": "skipped", "message": "Already processed"}

        # Get the image file
        storage = ImageStorageService()
        image_path = storage.get_full_path(image.filepath)

        if not image_path.exists():
            return {"status": "error", "message": "Image file not found"}

        # Read image bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Classify with AI
        classifier = get_ai_classifier()
        try:
            classification = await classifier.classify(image_bytes)
        except Exception as e:
            return {"status": "error", "message": str(e)}

        # Update image with AI results
        image.ai_tags = classification.tags
        image.ai_description = classification.description
        image.ai_processed = True

        # Create/link tags
        for tag_name in classification.tags:
            tag_name_lower = tag_name.lower().strip()
            if not tag_name_lower:
                continue

            # Find or create tag
            result = await db.execute(
                select(Tag).where(Tag.name == tag_name_lower)
            )
            tag = result.scalar_one_or_none()

            if not tag:
                tag = Tag(name=tag_name_lower, user_created=False)
                db.add(tag)
                await db.flush()

            # Link to item if not already linked
            result = await db.execute(
                select(ItemTag).where(
                    ItemTag.item_id == image.item_id,
                    ItemTag.tag_id == tag.id
                )
            )
            if not result.scalar_one_or_none():
                item_tag = ItemTag(item_id=image.item_id, tag_id=tag.id)
                db.add(item_tag)

        await db.commit()

        return {
            "status": "success",
            "tags": classification.tags,
            "description": classification.description,
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_ai(self, image_id: str) -> dict:
    """
    Process an image with AI classification.

    This task:
    1. Loads the image from storage
    2. Sends it to the AI classifier
    3. Stores the resulting tags and description
    4. Links tags to the item
    """
    try:
        result = asyncio.run(_process_image_async(UUID(image_id)))
        return result
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


async def _batch_process_images_async(item_id: UUID) -> dict:
    """Process all unprocessed images for an item."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(ItemImage).where(
                ItemImage.item_id == item_id,
                ItemImage.ai_processed == False
            )
        )
        images = result.scalars().all()

        processed = 0
        for image in images:
            try:
                await _process_image_async(image.id)
                processed += 1
            except Exception:
                continue

        return {"processed": processed, "total": len(images)}


@celery_app.task
def batch_process_item_images(item_id: str) -> dict:
    """Process all unprocessed images for an item."""
    return asyncio.run(_batch_process_images_async(UUID(item_id)))


@celery_app.task
def cleanup_orphan_tags() -> dict:
    """Remove tags that are not linked to any items."""
    async def _cleanup():
        async with async_session_maker() as db:
            # Find tags with no item links
            from sqlalchemy import func

            subquery = (
                select(ItemTag.tag_id)
                .group_by(ItemTag.tag_id)
            )

            result = await db.execute(
                select(Tag).where(
                    Tag.id.notin_(subquery),
                    Tag.user_created == False  # Only cleanup AI tags
                )
            )
            orphan_tags = result.scalars().all()

            count = len(orphan_tags)
            for tag in orphan_tags:
                await db.delete(tag)

            await db.commit()
            return {"deleted": count}

    return asyncio.run(_cleanup())
