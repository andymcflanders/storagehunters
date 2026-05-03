"""Background tasks for StorageHub."""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.database import get_sync_db
from app.models.item import Item, ItemImage, ItemTag, SeasonalEnum
from app.models.tag import Tag
from app.models.user import User, UserRole
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_ai_classifier():
    """Get the configured AI classifier."""
    from app.ai import get_classifier
    return get_classifier()


def _load_candidate_owners(db) -> list:
    """Build the candidate-owner list passed to the vision classifier.

    Includes every non-admin user (full members + profile users), since
    "size 42 wool socks" should suggest the parent and "size 98 dinosaur
    tee" should suggest the toddler. Admins are excluded — they're not
    typical item owners in a household setup.

    Returns an empty list when the AI settings toggle is off, so the
    classifier prompt skips the owner section entirely.
    """
    from app.ai import _load_ai_settings_sync
    from app.ai.base import CandidateOwner
    from datetime import date as _date

    if not _load_ai_settings_sync().owner_suggestion_enabled:
        return []

    result = db.execute(
        select(User).where(User.role != UserRole.ADMIN, User.is_active == True)  # noqa: E712
    )
    users = result.scalars().all()

    today = _date.today()
    candidates = []
    for u in users:
        age: int | None = None
        if u.birthdate:
            age = today.year - u.birthdate.year - (
                (today.month, today.day) < (u.birthdate.month, u.birthdate.day)
            )
        candidates.append(
            CandidateOwner(
                id=str(u.id),
                name=u.name,
                gender=u.gender.value if u.gender else None,
                age=age,
            )
        )
    return candidates


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

        # Classify all images together (async call wrapped in asyncio.run).
        # Candidates are non-admin household members; the classifier may
        # return a suggested_owner_id matching one of them.
        candidates = _load_candidate_owners(db)
        classifier = get_ai_classifier()
        try:
            classification = asyncio.run(
                classifier.classify(image_bytes_list, candidate_owners=candidates)
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

        # Record actual usage (token counts come from OpenAI's `usage`
        # block; mock classifier leaves these zero so the row is a
        # no-op insert from a cost perspective). uploaded_by gives us
        # the human user who triggered this — pulls from the first
        # unprocessed image since they all belong to the same item.
        if classification.prompt_tokens or classification.completion_tokens:
            from app.services.ai_usage import log_ai_call

            uploader_id = next(
                (img.uploaded_by for img in unprocessed_images if img.uploaded_by),
                None,
            )
            log_ai_call(
                kind="vision",
                model=classifier.model if hasattr(classifier, "model") else "unknown",
                input_tokens=classification.prompt_tokens,
                output_tokens=classification.completion_tokens,
                has_images=True,
                user_id=uploader_id,
                item_id=item.id,
                latency_ms=classification.latency_ms or None,
                db=db,
            )

        # Update item with AI results
        item.ai_names = dict(classification.names)
        item.ai_descriptions = dict(classification.descriptions)
        item.ai_processed = True

        # Persist AI owner suggestion. Only set when the user hasn't
        # already picked an owner — once owner_id is set, we don't want
        # the classifier overwriting that on a re-run.
        if classification.suggested_owner_id and item.owner_id is None:
            from uuid import UUID as _UUID
            try:
                item.suggested_owner_id = _UUID(classification.suggested_owner_id)
                item.owner_suggestion_reason = classification.owner_reason
            except (ValueError, TypeError):
                pass

        # Update size if extracted and not already set
        if classification.size and not item.size:
            item.size = classification.size

        # Always update size age range when the classifier produced
        # one. These fields are derived (not user-edited) so it's safe
        # to overwrite — and a re-run after the user fixes a wrong
        # size string should refresh the range.
        if classification.size_age_min_months is not None:
            item.size_age_min_months = classification.size_age_min_months
        if classification.size_age_max_months is not None:
            item.size_age_max_months = classification.size_age_max_months

        # Seed manual description from default-language AI description.
        if not item.description:
            from app.services.localized import localized
            from app.ai import _load_ai_settings_sync

            default_desc = localized(
                classification.descriptions,
                _load_ai_settings_sync().default_language,
            )
            if default_desc:
                item.description = default_desc

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

        # Mark all images as processed and store per-image data.
        # Per-image AI description uses the default language only — it's
        # an internal scratch field, not user-facing for selection.
        from app.services.localized import localized as _localized
        from app.ai import _load_ai_settings_sync as _load_ai
        per_image_desc = _localized(
            classification.descriptions, _load_ai().default_language
        )
        for img in unprocessed_images:
            img.ai_tags = classification.tags
            img.ai_description = per_image_desc
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
            "names": classification.names,
            "descriptions": classification.descriptions,
            "tags": classification.tags,
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
def backfill_size_age_ranges() -> dict:
    """Populate size_age_min/max_months on items that have a size but
    no age range yet.

    Hits the cheap text model with just the size string per item, so
    it's much cheaper than re-running the full vision classifier.
    Idempotent — safe to run repeatedly; only touches rows where
    size_age_max_months IS NULL.
    """
    from app.ai import _load_ai_settings_sync
    from app.ai.size_age import infer_size_age_range, SizeAgeResult
    from app.config import get_settings
    from app.services.ai_usage import log_ai_call

    ai_settings = _load_ai_settings_sync()
    config = get_settings()
    api_key = ai_settings.openai_api_key or config.openai_api_key
    if not api_key:
        return {"status": "skipped", "reason": "no_api_key", "updated": 0}

    model = ai_settings.summary_model

    with get_sync_db() as db:
        result = db.execute(
            select(Item).where(
                Item.size.is_not(None),
                Item.size != "",
                Item.size_age_max_months.is_(None),
            )
        )
        items = result.scalars().all()

        updated = 0
        skipped = 0
        for item in items:
            try:
                res: SizeAgeResult = asyncio.run(
                    infer_size_age_range(item.size, api_key=api_key, model=model)
                )
            except Exception:
                res = SizeAgeResult(min_months=None, max_months=None)

            # Log every call that actually hit OpenAI, even when the
            # AI declined to map the size — they all cost money.
            if res.prompt_tokens or res.completion_tokens:
                log_ai_call(
                    kind="size_age",
                    model=model,
                    input_tokens=res.prompt_tokens,
                    output_tokens=res.completion_tokens,
                    has_images=False,
                    item_id=item.id,
                    latency_ms=res.latency_ms or None,
                    db=db,
                )

            if res.min_months is None or res.max_months is None:
                skipped += 1
                continue

            item.size_age_min_months = res.min_months
            item.size_age_max_months = res.max_months
            updated += 1

            # Commit periodically so a mid-run failure doesn't lose
            # everything.
            if updated % 25 == 0:
                db.commit()

        db.commit()

    return {
        "status": "success",
        "considered": len(items),
        "updated": updated,
        "skipped": skipped,
    }


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


# ============== Backup Tasks ==============


def _calculate_next_run(schedule) -> datetime:
    """Calculate the next run time for a schedule."""
    from app.models.backup import ScheduleFrequency

    now = datetime.utcnow()
    schedule_time = schedule.time_of_day

    # Create a datetime with today's date and the schedule time
    next_run = now.replace(
        hour=schedule_time.hour,
        minute=schedule_time.minute,
        second=0,
        microsecond=0,
    )

    if schedule.frequency == ScheduleFrequency.DAILY:
        # If time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)

    elif schedule.frequency == ScheduleFrequency.WEEKLY:
        # Find the next occurrence of the specified day
        target_day = schedule.day_of_week or 0  # 0 = Monday
        days_ahead = target_day - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and next_run <= now):
            days_ahead += 7
        next_run += timedelta(days=days_ahead)

    elif schedule.frequency == ScheduleFrequency.MONTHLY:
        # Schedule for the specified day of month
        target_day = schedule.day_of_month or 1
        try:
            next_run = next_run.replace(day=target_day)
        except ValueError:
            # Day doesn't exist in this month, use last day
            import calendar
            last_day = calendar.monthrange(next_run.year, next_run.month)[1]
            next_run = next_run.replace(day=min(target_day, last_day))

        if next_run <= now:
            # Move to next month
            if next_run.month == 12:
                next_run = next_run.replace(year=next_run.year + 1, month=1)
            else:
                next_run = next_run.replace(month=next_run.month + 1)
            try:
                next_run = next_run.replace(day=target_day)
            except ValueError:
                import calendar
                last_day = calendar.monthrange(next_run.year, next_run.month)[1]
                next_run = next_run.replace(day=min(target_day, last_day))

    return next_run


@celery_app.task
def check_scheduled_backups() -> dict:
    """
    Periodic task to check for scheduled backups that need to run.

    This task runs every minute and checks if any schedules are due.
    """
    from app.models.backup import BackupSchedule

    now = datetime.utcnow()
    triggered = []

    with get_sync_db() as db:
        # Find active schedules that are due
        result = db.execute(
            select(BackupSchedule)
            .where(
                and_(
                    BackupSchedule.is_active == True,
                    BackupSchedule.next_run_at <= now,
                )
            )
        )
        schedules = result.scalars().all()

        for schedule in schedules:
            # Trigger the backup
            run_scheduled_backup.delay(str(schedule.id))
            triggered.append(str(schedule.id))

            # Update next_run_at
            schedule.next_run_at = _calculate_next_run(schedule)
            logger.info(
                f"Triggered backup for schedule {schedule.id}, "
                f"next run at {schedule.next_run_at}"
            )

        db.commit()

    return {"checked_at": now.isoformat(), "triggered": triggered}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def run_scheduled_backup(self, schedule_id: str) -> dict:
    """
    Run a scheduled backup.

    This task creates a backup based on the schedule's configuration.
    """
    from app.backup.backup_service import BackupOptions, BackupService
    from app.models.backup import (
        BackupConfig,
        BackupHistory,
        BackupSchedule,
        BackupStatus,
    )

    try:
        with get_sync_db() as db:
            # Get the schedule with its config
            result = db.execute(
                select(BackupSchedule)
                .where(BackupSchedule.id == UUID(schedule_id))
                .options(selectinload(BackupSchedule.config))
            )
            schedule = result.scalar_one_or_none()

            if not schedule:
                return {"status": "error", "message": "Schedule not found"}

            if not schedule.is_active:
                return {"status": "skipped", "message": "Schedule is not active"}

            config = schedule.config
            if not config or not config.is_active:
                return {"status": "skipped", "message": "Config is not active"}

            # Create history record
            history = BackupHistory(
                config_id=config.id,
                schedule_id=schedule.id,
                filename="",
                status=BackupStatus.IN_PROGRESS,
                include_images=config.include_images,
                is_encrypted=config.encryption_enabled,
                is_scheduled=True,
                started_at=datetime.utcnow(),
            )
            db.add(history)
            db.commit()
            db.refresh(history)
            history_id = history.id

        # Run the backup (outside transaction for long-running operation)
        service = BackupService()
        options = BackupOptions(
            include_images=config.include_images,
            include_users=False,
            compression_level=config.compression_level,
        )

        result = service.create_backup(options)

        # Update history with results
        with get_sync_db() as db:
            history = db.get(BackupHistory, history_id)
            schedule = db.get(BackupSchedule, UUID(schedule_id))

            if history:
                if result.success:
                    history.status = BackupStatus.COMPLETED
                    history.filename = result.filename or ""
                    history.file_path = result.file_path
                    history.size_bytes = result.size_bytes
                    history.checksum = result.checksum
                    history.statistics = result.statistics
                else:
                    history.status = BackupStatus.FAILED
                    history.error_message = result.error_message
                history.completed_at = datetime.utcnow()

            if schedule:
                schedule.last_run_at = datetime.utcnow()

            db.commit()

        if result.success:
            logger.info(f"Scheduled backup completed: {result.filename}")
            return {
                "status": "success",
                "filename": result.filename,
                "size_bytes": result.size_bytes,
            }
        else:
            logger.error(f"Scheduled backup failed: {result.error_message}")
            return {"status": "failed", "error": result.error_message}

    except Exception as exc:
        logger.error(f"Scheduled backup error: {exc}")
        # Update history as failed
        try:
            with get_sync_db() as db:
                result = db.execute(
                    select(BackupHistory)
                    .where(
                        and_(
                            BackupHistory.schedule_id == UUID(schedule_id),
                            BackupHistory.status == BackupStatus.IN_PROGRESS,
                        )
                    )
                    .order_by(BackupHistory.created_at.desc())
                    .limit(1)
                )
                history = result.scalar_one_or_none()
                if history:
                    history.status = BackupStatus.FAILED
                    history.error_message = str(exc)
                    history.completed_at = datetime.utcnow()
                    db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
