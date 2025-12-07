"""Background tasks for StorageHub."""

import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.database import get_sync_db
from app.models.item import Item, ItemImage, ItemTag, SeasonalEnum
from app.models.pending_upload import PendingUpload, UploadStatus
from app.models.tag import Tag
from app.worker.celery_app import celery_app


def get_ai_classifier():
    """Get the configured AI classifier."""
    from app.ai import get_classifier
    return get_classifier()


def get_segmentation_service():
    """Get the segmentation service."""
    from app.services.segmentation import get_segmentation_service
    return get_segmentation_service()


def _process_item_sync(item_id: UUID) -> dict:
    """
    Process all images for an item together with AI classification.

    This processes all images as a collection of the same item,
    combining information from all photos (different angles, labels, etc.)
    Uses synchronous database access for Celery compatibility.
    """
    from app.services.image_storage import ImageStorageService

    with get_sync_db() as db:
        # Get the item with its images
        result = db.execute(
            select(Item)
            .where(Item.id == item_id)
            .options(selectinload(Item.images))
        )
        item = result.scalar_one_or_none()

        if not item:
            return {"status": "error", "message": "Item not found"}

        if item.ai_processed:
            return {"status": "skipped", "message": "Already processed"}

        # Get all unprocessed images
        unprocessed_images = [img for img in item.images if not img.ai_processed]
        if not unprocessed_images:
            # Mark item as processed if no images to process
            item.ai_processed = True
            db.commit()
            return {"status": "skipped", "message": "No images to process"}

        # Load all image bytes
        storage = ImageStorageService()
        image_bytes_list = []

        for img in unprocessed_images:
            image_path = storage.get_full_path(img.filepath)
            if image_path.exists():
                with open(image_path, "rb") as f:
                    image_bytes_list.append(f.read())

        if not image_bytes_list:
            return {"status": "error", "message": "No image files found"}

        # Classify all images together (async call wrapped in asyncio.run)
        classifier = get_ai_classifier()
        try:
            classification = asyncio.run(classifier.classify(image_bytes_list))
        except Exception as e:
            return {"status": "error", "message": str(e)}

        # Update item with AI results
        item.ai_name = classification.name
        item.ai_name_no = classification.name_no
        item.ai_description = classification.description
        item.ai_description_no = classification.description_no
        item.ai_processed = True

        # Update size if extracted and not already set
        if classification.size and not item.size:
            item.size = classification.size

        # Update description if not already set
        if classification.description and not item.description:
            item.description = classification.description

        # Update seasonal if extracted and currently set to default
        if classification.seasonal and classification.seasonal != "none":
            seasonal_map = {
                "spring": SeasonalEnum.SPRING,
                "summer": SeasonalEnum.SUMMER,
                "fall": SeasonalEnum.FALL,
                "winter": SeasonalEnum.WINTER,
                "holiday": SeasonalEnum.HOLIDAY,
            }
            if classification.seasonal in seasonal_map:
                # Only update if currently set to NONE (default)
                if item.seasonal == SeasonalEnum.NONE:
                    item.seasonal = seasonal_map[classification.seasonal]

        # Mark all images as processed and store per-image data
        for img in unprocessed_images:
            img.ai_tags = classification.tags
            img.ai_description = classification.description
            img.ai_processed = True

        # Create/link tags to item
        for tag_name in classification.tags:
            tag_name_lower = tag_name.lower().strip()
            if not tag_name_lower:
                continue

            # Find or create tag
            result = db.execute(
                select(Tag).where(Tag.name == tag_name_lower)
            )
            tag = result.scalar_one_or_none()

            if not tag:
                tag = Tag(name=tag_name_lower, user_created=False)
                db.add(tag)
                db.flush()

            # Link to item (use INSERT ... ON CONFLICT to handle race conditions)
            stmt = insert(ItemTag).values(
                item_id=item.id,
                tag_id=tag.id
            ).on_conflict_do_nothing(index_elements=['item_id', 'tag_id'])
            db.execute(stmt)

        db.commit()

        return {
            "status": "success",
            "name": classification.name,
            "name_no": classification.name_no,
            "tags": classification.tags,
            "description": classification.description,
            "description_no": classification.description_no,
            "images_processed": len(image_bytes_list),
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_image_ai(self, image_id: str) -> dict:
    """
    Process an item by its image ID.

    This task finds the item associated with the image and processes
    ALL images for that item together as a collection.
    """
    try:
        with get_sync_db() as db:
            result = db.execute(
                select(ItemImage.item_id).where(ItemImage.id == UUID(image_id))
            )
            item_id = result.scalar_one_or_none()

        if not item_id:
            return {"status": "error", "message": "Image not found"}

        return _process_item_sync(item_id)
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_item_ai(self, item_id: str) -> dict:
    """
    Process all images for an item together.

    This is the main task for AI classification - it processes all images
    of an item as a collection to extract combined information.
    """
    try:
        return _process_item_sync(UUID(item_id))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def batch_process_item_images(item_id: str) -> dict:
    """Process all images for an item together."""
    return _process_item_sync(UUID(item_id))


@celery_app.task
def cleanup_orphan_tags() -> dict:
    """Remove tags that are not linked to any items."""
    with get_sync_db() as db:
        # Find tags with no item links
        subquery = (
            select(ItemTag.tag_id)
            .group_by(ItemTag.tag_id)
        )

        result = db.execute(
            select(Tag).where(
                Tag.id.notin_(subquery),
                Tag.user_created == False  # Only cleanup AI tags
            )
        )
        orphan_tags = result.scalars().all()

        count = len(orphan_tags)
        for tag in orphan_tags:
            db.delete(tag)

        db.commit()
        return {"deleted": count}


def _segment_pending_upload_sync(pending_upload_id: UUID) -> dict:
    """
    Process a pending upload through segmentation.

    This task:
    1. Loads the pending upload record
    2. Reads the temporary image file
    3. Calls segmentation service (local or cloud) to segment the image
    4. Creates Item + ItemImage for each detected segment
    5. Queues AI classification for each item
    6. Deletes the temporary file
    """
    from app.services.image_storage import ImageStorageService

    storage = ImageStorageService()
    segmentation = get_segmentation_service()

    with get_sync_db() as db:
        # 1. Get the pending upload
        result = db.execute(
            select(PendingUpload).where(PendingUpload.id == pending_upload_id)
        )
        pending = result.scalar_one_or_none()

        if not pending:
            return {"status": "error", "message": "Pending upload not found"}

        if pending.status != UploadStatus.PENDING.value:
            return {"status": "skipped", "message": f"Upload status is {pending.status}"}

        # Check if segmentation is enabled
        if not segmentation.is_enabled:
            pending.status = UploadStatus.FAILED.value
            pending.error_message = "Segmentation is disabled"
            db.commit()
            return {"status": "error", "message": "Segmentation is disabled"}

        # Mark as processing
        pending.status = UploadStatus.PROCESSING.value
        db.commit()

        try:
            # 2. Read the temporary image file
            temp_path = storage.get_temp_path(pending.temp_filepath)
            if not temp_path.exists():
                pending.status = UploadStatus.FAILED.value
                pending.error_message = "Temporary file not found"
                db.commit()
                return {"status": "error", "message": "Temporary file not found"}

            with open(temp_path, "rb") as f:
                image_bytes = f.read()

            # 3. Call segmentation service (async, so wrap in asyncio.run)
            if pending.multi_item_mode:
                # Multi-item mode: detect multiple objects
                seg_result = asyncio.run(segmentation.segment_multi(
                    image_bytes,
                    max_objects=10,
                ))
                if not seg_result.success:
                    # Fall back to single item
                    single_result = asyncio.run(segmentation.segment_single(image_bytes))
                    segments = [single_result] if single_result.success else []
                else:
                    segments = seg_result.segments
            else:
                # Single item mode: get largest object
                seg_result = asyncio.run(segmentation.segment_single(image_bytes))
                segments = [seg_result] if seg_result.success else []

            if not segments:
                # No segments found - create item with original image
                # (fallback: save the original without segmentation)
                pending.status = UploadStatus.FAILED.value
                pending.error_message = "No objects detected in image"
                db.commit()
                return {"status": "error", "message": "No objects detected in image"}

            # 4. Create Item + ItemImage for each segment
            created_items = []
            for idx, segment in enumerate(segments):
                if not segment.success or not segment.image_bytes:
                    continue

                # Create the Item
                item = Item(
                    name=f"Item {idx + 1}",  # Placeholder, AI will update
                    container_id=pending.container_id,
                    needs_review=True,
                    source_upload_id=pending.id,
                )
                db.add(item)
                db.flush()  # Get the item ID

                # Save the segmented PNG (async call)
                filename, filepath = asyncio.run(storage.save_segmented_image(
                    item.id,
                    segment.image_bytes,
                ))

                # Create the ItemImage
                image = ItemImage(
                    item_id=item.id,
                    filename=filename,
                    filepath=filepath,
                    is_segmented=True,
                    uploaded_by=pending.uploaded_by,
                )
                db.add(image)
                db.flush()

                created_items.append(str(item.id))

            db.commit()

            # 5. Queue AI classification for each item
            for item_id in created_items:
                process_item_ai.delay(item_id)

            # 6. Update pending upload status and delete temp file
            pending.status = UploadStatus.COMPLETED.value
            pending.items_created = len(created_items)
            pending.processed_at = datetime.utcnow()
            db.commit()

            # Delete the temporary file (async call)
            asyncio.run(storage.delete_temp_upload(pending.temp_filepath))

            return {
                "status": "success",
                "items_created": len(created_items),
                "item_ids": created_items,
            }

        except Exception as e:
            # Mark as failed
            pending.status = UploadStatus.FAILED.value
            pending.error_message = str(e)
            db.commit()
            raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def segment_pending_upload(self, pending_upload_id: str) -> dict:
    """
    Process a pending upload through FastSAM segmentation.

    This task segments the uploaded image, creates items with
    transparent background PNGs, and queues AI classification.
    """
    try:
        return _segment_pending_upload_sync(UUID(pending_upload_id))
    except Exception as exc:
        raise self.retry(exc=exc)
