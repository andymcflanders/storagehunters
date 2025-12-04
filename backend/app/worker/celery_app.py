"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "storagehub",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit at 4 minutes
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Results expire after 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    "app.worker.tasks.process_image_ai": {"queue": "ai"},
    "app.worker.tasks.*": {"queue": "default"},
}
