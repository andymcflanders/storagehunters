"""Upload API endpoints for item creation with optional segmentation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Container, Item, ItemImage, PendingUpload, User
from app.models.pending_upload import UploadStatus
from app.services.image_storage import ImageStorageService
from app.worker.tasks import process_item_ai, segment_pending_upload

router = APIRouter()


class PendingUploadResponse(BaseModel):
    """Response for a pending upload."""

    id: str
    container_id: str
    status: str
    multi_item_mode: bool
    items_created: int
    error_message: Optional[str]
    created_at: str
    processed_at: Optional[str]

    class Config:
        from_attributes = True


class PendingUploadWithItems(PendingUploadResponse):
    """Response including created item IDs."""

    item_ids: list[str] = []


class BatchUploadResponse(BaseModel):
    """Response for batch upload."""

    pending_uploads: list[PendingUploadResponse]


@router.post("/containers/{container_id}/upload", response_model=BatchUploadResponse)
async def upload_to_container(
    container_id: UUID,
    files: list[UploadFile] = File(...),
    multi_item_mode: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload images to a container for processing.

    If segmentation is enabled, images are queued for FastSAM segmentation
    where each detected object becomes a separate Item.

    If segmentation is disabled, each image creates one Item directly
    and is sent to AI for classification.

    Args:
        container_id: Target container for created items
        files: Image files to process
        multi_item_mode: If True and segmentation enabled, detect multiple objects per image
    """
    settings = get_settings()

    # Verify container exists
    result = await db.execute(
        select(Container).where(Container.id == container_id)
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    # Validate files
    valid_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    for file in files:
        if file.content_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed: {valid_types}",
            )

    storage = ImageStorageService()
    pending_uploads = []

    for file in files:
        content = await file.read()

        if settings.segmentation_enabled:
            # Segmentation enabled: use PendingUpload + segmentation pipeline
            upload_id, temp_filepath = await storage.save_temp_upload(
                content, file.filename or "image.jpg"
            )

            pending = PendingUpload(
                id=upload_id,
                container_id=container_id,
                uploaded_by=current_user.id,
                temp_filepath=temp_filepath,
                multi_item_mode=multi_item_mode,
            )
            db.add(pending)
            await db.flush()
            pending_uploads.append(pending)

            # Queue segmentation task
            segment_pending_upload.delay(str(pending.id))
        else:
            # Segmentation disabled: create Item directly with original image
            item = Item(
                name="Processing...",
                container_id=container_id,
                needs_review=True,
            )
            db.add(item)
            await db.flush()

            # Save image directly to item storage
            filename, filepath = await storage.save_image(
                item.id,
                file.filename or "image.jpg",
                content,
            )

            # Create ItemImage record
            image = ItemImage(
                item_id=item.id,
                filename=filename,
                filepath=filepath,
                is_segmented=False,
                uploaded_by=current_user.id,
            )
            db.add(image)
            await db.flush()

            # Create a PendingUpload record for tracking (already completed)
            pending = PendingUpload(
                container_id=container_id,
                uploaded_by=current_user.id,
                temp_filepath="",
                multi_item_mode=False,
                status=UploadStatus.COMPLETED.value,
                items_created=1,
                processed_at=datetime.utcnow(),
            )
            db.add(pending)
            await db.flush()
            pending_uploads.append(pending)

            # Queue AI classification
            process_item_ai.delay(str(item.id))

    await db.commit()

    return BatchUploadResponse(
        pending_uploads=[
            PendingUploadResponse(
                id=str(p.id),
                container_id=str(p.container_id),
                status=p.status,
                multi_item_mode=p.multi_item_mode,
                items_created=p.items_created,
                error_message=p.error_message,
                created_at=p.created_at.isoformat(),
                processed_at=p.processed_at.isoformat() if p.processed_at else None,
            )
            for p in pending_uploads
        ]
    )


@router.get("/pending", response_model=list[PendingUploadResponse])
async def get_pending_uploads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all pending uploads for the current user."""
    result = await db.execute(
        select(PendingUpload)
        .where(PendingUpload.uploaded_by == current_user.id)
        .order_by(PendingUpload.created_at.desc())
        .limit(50)
    )
    uploads = result.scalars().all()

    return [
        PendingUploadResponse(
            id=str(u.id),
            container_id=str(u.container_id),
            status=u.status,
            multi_item_mode=u.multi_item_mode,
            items_created=u.items_created,
            error_message=u.error_message,
            created_at=u.created_at.isoformat(),
            processed_at=u.processed_at.isoformat() if u.processed_at else None,
        )
        for u in uploads
    ]


@router.get("/pending/{upload_id}", response_model=PendingUploadWithItems)
async def get_pending_upload(
    upload_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get status of a specific pending upload."""
    result = await db.execute(
        select(PendingUpload)
        .where(
            PendingUpload.id == upload_id,
            PendingUpload.uploaded_by == current_user.id,
        )
        .options(selectinload(PendingUpload.created_items))
    )
    upload = result.scalar_one_or_none()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return PendingUploadWithItems(
        id=str(upload.id),
        container_id=str(upload.container_id),
        status=upload.status,
        multi_item_mode=upload.multi_item_mode,
        items_created=upload.items_created,
        error_message=upload.error_message,
        created_at=upload.created_at.isoformat(),
        processed_at=upload.processed_at.isoformat() if upload.processed_at else None,
        item_ids=[str(item.id) for item in upload.created_items],
    )
