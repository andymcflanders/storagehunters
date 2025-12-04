"""Celery worker module."""

from app.worker.celery_app import celery_app
from app.worker.tasks import (
    batch_process_item_images,
    cleanup_orphan_tags,
    process_image_ai,
)

__all__ = [
    "celery_app",
    "process_image_ai",
    "batch_process_item_images",
    "cleanup_orphan_tags",
]
