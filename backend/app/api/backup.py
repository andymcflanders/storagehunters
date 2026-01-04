"""Backup API endpoints."""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select, func

from app.api.deps import AdminUser, DbSession
from app.backup.backup_service import BackupOptions, BackupService
from app.backup.providers import GOOGLE_DRIVE_AVAILABLE, DROPBOX_AVAILABLE, get_storage_provider
from app.config import get_settings
from app.models.backup import (
    BackupConfig,
    BackupHistory,
    BackupProviderType,
    BackupSchedule,
    BackupStatus,
    ScheduleFrequency,
)

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/backup", tags=["backup"])


# ============== Schemas ==============


class BackupConfigCreate(BaseModel):
    """Schema for creating a backup configuration."""

    name: str
    description: str | None = None
    provider_type: str = "local"
    provider_config: dict = {}
    include_images: bool = False
    encryption_enabled: bool = False
    encryption_password: str | None = None
    compression_level: int = 6
    retention_count: int = 10
    is_default: bool = False


class BackupConfigUpdate(BaseModel):
    """Schema for updating a backup configuration."""

    name: str | None = None
    description: str | None = None
    provider_config: dict | None = None
    include_images: bool | None = None
    encryption_enabled: bool | None = None
    encryption_password: str | None = None
    compression_level: int | None = None
    retention_count: int | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class BackupConfigResponse(BaseModel):
    """Response schema for backup configuration."""

    id: UUID
    name: str
    description: str | None
    provider_type: str
    include_images: bool
    encryption_enabled: bool
    compression_level: int
    retention_count: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BackupHistoryResponse(BaseModel):
    """Response schema for backup history."""

    id: UUID
    config_id: UUID | None
    filename: str
    file_path: str | None
    remote_id: str | None
    size_bytes: int
    checksum: str | None
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    statistics: dict | None

    model_config = {"from_attributes": True}


class BackupHistoryListResponse(BaseModel):
    """Paginated backup history response."""

    items: list[BackupHistoryResponse]
    total: int
    page: int
    page_size: int


class BackupTriggerRequest(BaseModel):
    """Request to trigger a backup."""

    include_images: bool = False
    include_users: bool = False
    compression_level: int = 6


class BackupTriggerResponse(BaseModel):
    """Response after triggering a backup."""

    backup_id: UUID
    status: str
    message: str


class BackupPreviewResponse(BaseModel):
    """Response with backup preview information."""

    valid: bool
    version: str | None
    created_at: str | None
    statistics: dict | None
    error_message: str | None


class RestoreRequest(BaseModel):
    """Request to restore from a backup."""

    restore_images: bool = True


class RestoreResponse(BaseModel):
    """Response after restore operation."""

    success: bool
    message: str
    statistics: dict | None = None


class GoogleDriveTestRequest(BaseModel):
    """Request to test Google Drive credentials."""

    service_account_json: str


class GoogleDriveTestResponse(BaseModel):
    """Response from Google Drive test."""

    success: bool
    message: str
    email: str | None = None


class RemoteBackupResponse(BaseModel):
    """Remote backup info."""

    remote_id: str
    filename: str
    remote_path: str
    size_bytes: int
    created_at: datetime
    checksum: str | None = None


class RemoteBackupListResponse(BaseModel):
    """List of remote backups."""

    success: bool
    backups: list[RemoteBackupResponse] = []
    error_message: str | None = None


class ProviderStatusResponse(BaseModel):
    """Response with provider status info."""

    google_drive_available: bool
    dropbox_available: bool
    local_available: bool = True


class UploadToProviderRequest(BaseModel):
    """Request to upload a backup to a storage provider."""

    backup_id: UUID
    provider_type: str = "google_drive"
    provider_config: dict = {}


class UploadToProviderResponse(BaseModel):
    """Response after uploading to provider."""

    success: bool
    message: str
    remote_id: str | None = None
    remote_path: str | None = None


# Schedule schemas
class ScheduleCreate(BaseModel):
    """Schema for creating a backup schedule."""

    config_id: UUID
    name: str
    frequency: str  # daily, weekly, monthly
    time_of_day: str  # HH:MM format
    day_of_week: int | None = None  # 0-6 for weekly
    day_of_month: int | None = None  # 1-28 for monthly
    is_active: bool = True


class ScheduleUpdate(BaseModel):
    """Schema for updating a backup schedule."""

    name: str | None = None
    frequency: str | None = None
    time_of_day: str | None = None
    day_of_week: int | None = None
    day_of_month: int | None = None
    is_active: bool | None = None


class ScheduleResponse(BaseModel):
    """Response schema for backup schedule."""

    id: UUID
    config_id: UUID
    name: str
    frequency: str
    time_of_day: str
    day_of_week: int | None
    day_of_month: int | None
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============== Helper Functions ==============


def _get_backup_dir() -> Path:
    """Get the backup directory path."""
    backup_dir = Path(settings.upload_dir).parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _calculate_next_run(schedule: BackupSchedule) -> datetime:
    """Calculate the next run time for a schedule."""
    from datetime import timedelta

    now = datetime.utcnow()
    schedule_time = schedule.time_of_day

    next_run = now.replace(
        hour=schedule_time.hour,
        minute=schedule_time.minute,
        second=0,
        microsecond=0,
    )

    if schedule.frequency == ScheduleFrequency.DAILY:
        if next_run <= now:
            next_run += timedelta(days=1)

    elif schedule.frequency == ScheduleFrequency.WEEKLY:
        target_day = schedule.day_of_week or 0
        days_ahead = target_day - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and next_run <= now):
            days_ahead += 7
        next_run += timedelta(days=days_ahead)

    elif schedule.frequency == ScheduleFrequency.MONTHLY:
        import calendar
        target_day = schedule.day_of_month or 1
        try:
            next_run = next_run.replace(day=target_day)
        except ValueError:
            last_day = calendar.monthrange(next_run.year, next_run.month)[1]
            next_run = next_run.replace(day=min(target_day, last_day))

        if next_run <= now:
            if next_run.month == 12:
                next_run = next_run.replace(year=next_run.year + 1, month=1)
            else:
                next_run = next_run.replace(month=next_run.month + 1)
            try:
                next_run = next_run.replace(day=target_day)
            except ValueError:
                last_day = calendar.monthrange(next_run.year, next_run.month)[1]
                next_run = next_run.replace(day=min(target_day, last_day))

    return next_run


def _schedule_to_response(schedule: BackupSchedule) -> ScheduleResponse:
    """Convert a BackupSchedule to ScheduleResponse."""
    return ScheduleResponse(
        id=schedule.id,
        config_id=schedule.config_id,
        name=schedule.name,
        frequency=schedule.frequency.value,
        time_of_day=schedule.time_of_day.strftime("%H:%M"),
        day_of_week=schedule.day_of_week,
        day_of_month=schedule.day_of_month,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_at=schedule.created_at,
    )


async def _run_backup(
    db_session_factory,
    backup_id: UUID,
    options: BackupOptions,
) -> None:
    """Run backup in background task."""
    from app.database import get_sync_db

    # Update status to in_progress
    with get_sync_db() as db:
        history = db.get(BackupHistory, backup_id)
        if history:
            history.status = BackupStatus.IN_PROGRESS
            history.started_at = datetime.utcnow()
            db.commit()

    try:
        # Create backup
        service = BackupService()
        result = service.create_backup(options)

        # Update history record
        with get_sync_db() as db:
            history = db.get(BackupHistory, backup_id)
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
                db.commit()

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        with get_sync_db() as db:
            history = db.get(BackupHistory, backup_id)
            if history:
                history.status = BackupStatus.FAILED
                history.error_message = str(e)
                history.completed_at = datetime.utcnow()
                db.commit()


# ============== Endpoints ==============


# --- Backup Configurations ---


@router.get("/configs", response_model=list[BackupConfigResponse])
async def list_backup_configs(
    db: DbSession,
    admin: AdminUser,
) -> list[BackupConfigResponse]:
    """List all backup configurations (admin only)."""
    result = await db.execute(
        select(BackupConfig).order_by(BackupConfig.created_at.desc())
    )
    configs = result.scalars().all()

    return [
        BackupConfigResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            provider_type=c.provider_type.value if hasattr(c.provider_type, "value") else str(c.provider_type),
            include_images=c.include_images,
            encryption_enabled=c.encryption_enabled,
            compression_level=c.compression_level,
            retention_count=c.retention_count,
            is_active=c.is_active,
            is_default=c.is_default,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


@router.post("/configs", response_model=BackupConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_config(
    db: DbSession,
    admin: AdminUser,
    data: BackupConfigCreate,
) -> BackupConfigResponse:
    """Create a backup configuration (admin only)."""
    # Validate provider type
    try:
        provider_type = BackupProviderType(data.provider_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider type: {data.provider_type}",
        )

    # If this is set as default, unset other defaults
    if data.is_default:
        await db.execute(
            BackupConfig.__table__.update().values(is_default=False)
        )

    config = BackupConfig(
        name=data.name,
        description=data.description,
        provider_type=provider_type,
        provider_config=data.provider_config,
        include_images=data.include_images,
        encryption_enabled=data.encryption_enabled,
        compression_level=data.compression_level,
        retention_count=data.retention_count,
        is_default=data.is_default,
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return BackupConfigResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        provider_type=config.provider_type.value,
        include_images=config.include_images,
        encryption_enabled=config.encryption_enabled,
        compression_level=config.compression_level,
        retention_count=config.retention_count,
        is_active=config.is_active,
        is_default=config.is_default,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.patch("/configs/{config_id}", response_model=BackupConfigResponse)
async def update_backup_config(
    db: DbSession,
    admin: AdminUser,
    config_id: UUID,
    data: BackupConfigUpdate,
) -> BackupConfigResponse:
    """Update a backup configuration (admin only)."""
    config = await db.get(BackupConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup configuration not found",
        )

    # Update fields
    if data.name is not None:
        config.name = data.name
    if data.description is not None:
        config.description = data.description
    if data.provider_config is not None:
        config.provider_config = data.provider_config
    if data.include_images is not None:
        config.include_images = data.include_images
    if data.encryption_enabled is not None:
        config.encryption_enabled = data.encryption_enabled
    if data.compression_level is not None:
        config.compression_level = data.compression_level
    if data.retention_count is not None:
        config.retention_count = data.retention_count
    if data.is_active is not None:
        config.is_active = data.is_active
    if data.is_default is not None:
        if data.is_default:
            # Unset other defaults
            await db.execute(
                BackupConfig.__table__.update()
                .where(BackupConfig.id != config_id)
                .values(is_default=False)
            )
        config.is_default = data.is_default

    await db.commit()
    await db.refresh(config)

    return BackupConfigResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        provider_type=config.provider_type.value,
        include_images=config.include_images,
        encryption_enabled=config.encryption_enabled,
        compression_level=config.compression_level,
        retention_count=config.retention_count,
        is_active=config.is_active,
        is_default=config.is_default,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_config(
    db: DbSession,
    admin: AdminUser,
    config_id: UUID,
) -> None:
    """Delete a backup configuration (admin only)."""
    config = await db.get(BackupConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup configuration not found",
        )

    await db.delete(config)
    await db.commit()


# --- Backup Schedules ---


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_backup_schedules(
    db: DbSession,
    admin: AdminUser,
) -> list[ScheduleResponse]:
    """List all backup schedules (admin only)."""
    result = await db.execute(
        select(BackupSchedule).order_by(BackupSchedule.created_at.desc())
    )
    schedules = result.scalars().all()
    return [_schedule_to_response(s) for s in schedules]


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_schedule(
    db: DbSession,
    admin: AdminUser,
    data: ScheduleCreate,
) -> ScheduleResponse:
    """Create a backup schedule (admin only)."""
    from datetime import time as time_type

    # Validate config exists
    config = await db.get(BackupConfig, data.config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup configuration not found",
        )

    # Validate frequency
    try:
        frequency = ScheduleFrequency(data.frequency)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid frequency: {data.frequency}. Use daily, weekly, or monthly.",
        )

    # Parse time
    try:
        parts = data.time_of_day.split(":")
        schedule_time = time_type(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM (e.g., 02:30)",
        )

    # Validate day_of_week for weekly
    if frequency == ScheduleFrequency.WEEKLY:
        if data.day_of_week is None or not (0 <= data.day_of_week <= 6):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weekly schedules require day_of_week (0-6, Monday=0)",
            )

    # Validate day_of_month for monthly
    if frequency == ScheduleFrequency.MONTHLY:
        if data.day_of_month is None or not (1 <= data.day_of_month <= 28):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monthly schedules require day_of_month (1-28)",
            )

    schedule = BackupSchedule(
        config_id=data.config_id,
        name=data.name,
        frequency=frequency,
        time_of_day=schedule_time,
        day_of_week=data.day_of_week,
        day_of_month=data.day_of_month,
        is_active=data.is_active,
    )

    # Calculate next run time
    schedule.next_run_at = _calculate_next_run(schedule)

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    return _schedule_to_response(schedule)


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_backup_schedule(
    db: DbSession,
    admin: AdminUser,
    schedule_id: UUID,
) -> ScheduleResponse:
    """Get a specific backup schedule (admin only)."""
    schedule = await db.get(BackupSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )
    return _schedule_to_response(schedule)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_backup_schedule(
    db: DbSession,
    admin: AdminUser,
    schedule_id: UUID,
    data: ScheduleUpdate,
) -> ScheduleResponse:
    """Update a backup schedule (admin only)."""
    from datetime import time as time_type

    schedule = await db.get(BackupSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    recalculate_next = False

    if data.name is not None:
        schedule.name = data.name

    if data.frequency is not None:
        try:
            schedule.frequency = ScheduleFrequency(data.frequency)
            recalculate_next = True
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid frequency: {data.frequency}",
            )

    if data.time_of_day is not None:
        try:
            parts = data.time_of_day.split(":")
            schedule.time_of_day = time_type(int(parts[0]), int(parts[1]))
            recalculate_next = True
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time format. Use HH:MM",
            )

    if data.day_of_week is not None:
        schedule.day_of_week = data.day_of_week
        recalculate_next = True

    if data.day_of_month is not None:
        schedule.day_of_month = data.day_of_month
        recalculate_next = True

    if data.is_active is not None:
        schedule.is_active = data.is_active
        if data.is_active:
            recalculate_next = True

    if recalculate_next and schedule.is_active:
        schedule.next_run_at = _calculate_next_run(schedule)

    await db.commit()
    await db.refresh(schedule)

    return _schedule_to_response(schedule)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_schedule(
    db: DbSession,
    admin: AdminUser,
    schedule_id: UUID,
) -> None:
    """Delete a backup schedule (admin only)."""
    schedule = await db.get(BackupSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    await db.delete(schedule)
    await db.commit()


@router.post("/schedules/{schedule_id}/run", response_model=BackupTriggerResponse)
async def trigger_scheduled_backup(
    db: DbSession,
    admin: AdminUser,
    schedule_id: UUID,
) -> BackupTriggerResponse:
    """Manually trigger a scheduled backup (admin only)."""
    schedule = await db.get(BackupSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    # Queue the backup task
    from app.worker.tasks import run_scheduled_backup
    run_scheduled_backup.delay(str(schedule_id))

    return BackupTriggerResponse(
        backup_id=schedule.id,
        status="pending",
        message="Scheduled backup triggered",
    )


# --- Backup Operations ---


@router.post("/create", response_model=BackupTriggerResponse)
async def trigger_backup(
    db: DbSession,
    admin: AdminUser,
    background_tasks: BackgroundTasks,
    data: BackupTriggerRequest,
) -> BackupTriggerResponse:
    """Trigger a new backup (admin only)."""
    # Create history record
    history = BackupHistory(
        filename="",  # Will be updated when backup completes
        status=BackupStatus.PENDING,
        statistics={
            "include_images": data.include_images,
            "include_users": data.include_users,
        },
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    # Create backup options
    options = BackupOptions(
        include_images=data.include_images,
        include_users=data.include_users,
        compression_level=data.compression_level,
    )

    # Run backup in background
    background_tasks.add_task(
        _run_backup,
        None,  # db_session_factory not needed with get_sync_db
        history.id,
        options,
    )

    return BackupTriggerResponse(
        backup_id=history.id,
        status="pending",
        message="Backup started in background",
    )


@router.get("/history", response_model=BackupHistoryListResponse)
async def list_backup_history(
    db: DbSession,
    admin: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = None,
) -> BackupHistoryListResponse:
    """List backup history (admin only)."""
    # Base query
    query = select(BackupHistory)

    # Apply filters
    if status_filter:
        try:
            status_enum = BackupStatus(status_filter)
            query = query.where(BackupHistory.status == status_enum)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.order_by(BackupHistory.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    histories = result.scalars().all()

    items = [
        BackupHistoryResponse(
            id=h.id,
            config_id=h.config_id,
            filename=h.filename,
            file_path=h.file_path,
            remote_id=h.remote_id,
            size_bytes=h.size_bytes,
            checksum=h.checksum,
            status=h.status.value if hasattr(h.status, "value") else str(h.status),
            error_message=h.error_message,
            started_at=h.started_at,
            completed_at=h.completed_at,
            statistics=h.statistics,
        )
        for h in histories
    ]

    return BackupHistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/history/{backup_id}", response_model=BackupHistoryResponse)
async def get_backup_history(
    db: DbSession,
    admin: AdminUser,
    backup_id: UUID,
) -> BackupHistoryResponse:
    """Get a specific backup history entry (admin only)."""
    history = await db.get(BackupHistory, backup_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup history not found",
        )

    return BackupHistoryResponse(
        id=history.id,
        config_id=history.config_id,
        filename=history.filename,
        file_path=history.file_path,
        remote_id=history.remote_id,
        size_bytes=history.size_bytes,
        checksum=history.checksum,
        status=history.status.value if hasattr(history.status, "value") else str(history.status),
        error_message=history.error_message,
        started_at=history.started_at,
        completed_at=history.completed_at,
        statistics=history.statistics,
    )


@router.get("/history/{backup_id}/download")
async def download_backup(
    db: DbSession,
    admin: AdminUser,
    backup_id: UUID,
) -> FileResponse:
    """Download a backup file (admin only)."""
    history = await db.get(BackupHistory, backup_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup history not found",
        )

    if history.status != BackupStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup is not completed",
        )

    if not history.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found",
        )

    file_path = Path(history.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found on disk",
        )

    return FileResponse(
        path=file_path,
        filename=history.filename,
        media_type="application/zip",
    )


@router.delete("/history/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    db: DbSession,
    admin: AdminUser,
    backup_id: UUID,
) -> None:
    """Delete a backup and its file (admin only)."""
    history = await db.get(BackupHistory, backup_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup history not found",
        )

    # Delete file if it exists
    if history.file_path:
        file_path = Path(history.file_path)
        if file_path.exists():
            file_path.unlink()

    await db.delete(history)
    await db.commit()


# --- Restore Operations ---


# Store uploaded files temporarily for restore preview/execute
_pending_restores: dict[str, Path] = {}


@router.post("/restore/upload", response_model=BackupPreviewResponse)
async def upload_backup_for_restore(
    db: DbSession,
    admin: AdminUser,
    file: UploadFile = File(...),
) -> BackupPreviewResponse:
    """Upload a backup file for restoration (admin only)."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a .zip backup file.",
        )

    # Save to temporary location
    temp_dir = Path(tempfile.mkdtemp())
    temp_path = temp_dir / file.filename

    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Verify and get preview
        service = BackupService()
        is_valid, manifest, error = service.verify_backup(temp_path)

        if not is_valid:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            return BackupPreviewResponse(
                valid=False,
                version=None,
                created_at=None,
                statistics=None,
                error_message=error,
            )

        # Store for later restore
        restore_key = f"{admin.id}_{datetime.utcnow().timestamp()}"
        _pending_restores[restore_key] = temp_path

        return BackupPreviewResponse(
            valid=True,
            version=manifest.get("version"),
            created_at=manifest.get("created_at"),
            statistics=manifest.get("statistics"),
            error_message=None,
        )

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process backup file: {str(e)}",
        )


@router.post("/restore/execute", response_model=RestoreResponse)
async def execute_restore(
    db: DbSession,
    admin: AdminUser,
    data: RestoreRequest,
) -> RestoreResponse:
    """Execute restoration from uploaded backup (admin only)."""
    # Find the most recent pending restore for this admin
    admin_prefix = f"{admin.id}_"
    matching_keys = [k for k in _pending_restores.keys() if k.startswith(admin_prefix)]

    if not matching_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending restore found. Please upload a backup file first.",
        )

    # Get the most recent one
    restore_key = max(matching_keys, key=lambda k: float(k.split("_")[1]))
    backup_path = _pending_restores.pop(restore_key)

    try:
        if not backup_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file no longer available. Please upload again.",
            )

        service = BackupService()
        result = service.restore_backup(
            backup_path=backup_path,
            restore_images=data.restore_images,
        )

        if result.success:
            return RestoreResponse(
                success=True,
                message="Restore completed successfully",
                statistics=result.statistics,
            )
        else:
            return RestoreResponse(
                success=False,
                message=result.error_message or "Restore failed",
                statistics=None,
            )

    finally:
        # Cleanup temp directory
        if backup_path.parent.exists():
            shutil.rmtree(backup_path.parent, ignore_errors=True)


@router.post("/restore/from-history/{backup_id}", response_model=RestoreResponse)
async def restore_from_history(
    db: DbSession,
    admin: AdminUser,
    backup_id: UUID,
    data: RestoreRequest,
) -> RestoreResponse:
    """Restore from an existing backup in history (admin only)."""
    history = await db.get(BackupHistory, backup_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup history not found",
        )

    if history.status != BackupStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup is not completed",
        )

    if not history.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found",
        )

    backup_path = Path(history.file_path)
    if not backup_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found on disk",
        )

    service = BackupService()
    result = service.restore_backup(
        backup_path=backup_path,
        restore_images=data.restore_images,
    )

    if result.success:
        return RestoreResponse(
            success=True,
            message="Restore completed successfully",
            statistics=result.statistics,
        )
    else:
        return RestoreResponse(
            success=False,
            message=result.error_message or "Restore failed",
            statistics=None,
        )


# --- Quick Backup (no config needed) ---


@router.get("/quick-download")
async def quick_backup_download(
    db: DbSession,
    admin: AdminUser,
    include_images: bool = False,
) -> FileResponse:
    """Create and download a backup immediately (admin only)."""
    options = BackupOptions(
        include_images=include_images,
        include_users=False,
        compression_level=6,
    )

    service = BackupService()
    result = service.create_backup(options)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "Backup creation failed",
        )

    if not result.file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup file not created",
        )

    # Create history record for tracking
    history = BackupHistory(
        filename=result.filename or "",
        file_path=result.file_path,
        size_bytes=result.size_bytes,
        checksum=result.checksum,
        status=BackupStatus.COMPLETED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        statistics=result.statistics,
    )
    db.add(history)
    await db.commit()

    return FileResponse(
        path=result.file_path,
        filename=result.filename,
        media_type="application/zip",
    )


# --- Storage Provider Operations ---


@router.get("/providers/status", response_model=ProviderStatusResponse)
async def get_provider_status(
    admin: AdminUser,
) -> ProviderStatusResponse:
    """Get status of available storage providers (admin only)."""
    return ProviderStatusResponse(
        google_drive_available=GOOGLE_DRIVE_AVAILABLE,
        dropbox_available=DROPBOX_AVAILABLE,
        local_available=True,
    )


class SharedDriveInfo(BaseModel):
    """Info about a Shared Drive."""

    id: str
    name: str


class GoogleDriveTestResponseExtended(BaseModel):
    """Extended response from Google Drive test."""

    success: bool
    message: str
    email: str | None = None
    shared_drives: list[SharedDriveInfo] = []
    has_shared_drives: bool = False


@router.post("/providers/google-drive/test", response_model=GoogleDriveTestResponseExtended)
async def test_google_drive_credentials(
    admin: AdminUser,
    data: GoogleDriveTestRequest,
) -> GoogleDriveTestResponseExtended:
    """Test Google Drive credentials (admin only).

    Service accounts require a Shared Drive (Team Drive) to upload files.
    Regular shared folders will NOT work due to storage quota limitations.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        return GoogleDriveTestResponseExtended(
            success=False,
            message="Google Drive provider not available. Dependencies not installed.",
        )

    try:
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # Parse and validate credentials
        creds_dict = json.loads(data.service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/drive"],
        )

        # Test connection
        service = build("drive", "v3", credentials=credentials)
        about = service.about().get(fields="user").execute()
        email = about.get("user", {}).get("emailAddress", "unknown")

        # Check for Shared Drives (Team Drives) - this is what actually works
        shared_drives = []
        try:
            results = service.drives().list(
                pageSize=10,
                fields="drives(id, name)"
            ).execute()
            shared_drives = [
                SharedDriveInfo(id=d["id"], name=d["name"])
                for d in results.get("drives", [])
            ]
        except Exception as e:
            logger.debug(f"Could not list Shared Drives: {e}")

        if shared_drives:
            return GoogleDriveTestResponseExtended(
                success=True,
                message=f"Connected! Found {len(shared_drives)} Shared Drive(s). Ready to upload backups.",
                email=email,
                shared_drives=shared_drives,
                has_shared_drives=True,
            )
        else:
            return GoogleDriveTestResponseExtended(
                success=True,
                message=(
                    f"Connected as {email}, but no Shared Drives found. "
                    "Service accounts cannot upload to regular Google Drive due to storage quota limitations. "
                    "You need a Google Workspace account with a Shared Drive (Team Drive) where the service account is added as a member."
                ),
                email=email,
                shared_drives=[],
                has_shared_drives=False,
            )

    except json.JSONDecodeError:
        return GoogleDriveTestResponseExtended(
            success=False,
            message="Invalid JSON format for service account credentials",
        )
    except Exception as e:
        logger.error(f"Google Drive test failed: {e}")
        return GoogleDriveTestResponseExtended(
            success=False,
            message=f"Connection failed: {str(e)}",
        )


@router.post("/providers/google-drive/list", response_model=RemoteBackupListResponse)
async def list_google_drive_backups(
    admin: AdminUser,
    data: GoogleDriveTestRequest,
) -> RemoteBackupListResponse:
    """List backups stored in Google Drive (admin only)."""
    if not GOOGLE_DRIVE_AVAILABLE:
        return RemoteBackupListResponse(
            success=False,
            error_message="Google Drive provider not available",
        )

    try:
        provider = get_storage_provider(
            "google_drive",
            {"service_account_json": data.service_account_json},
        )
        result = await provider.list_backups()

        if not result.success:
            return RemoteBackupListResponse(
                success=False,
                error_message=result.error_message,
            )

        return RemoteBackupListResponse(
            success=True,
            backups=[
                RemoteBackupResponse(
                    remote_id=b.remote_id,
                    filename=b.filename,
                    remote_path=b.remote_path,
                    size_bytes=b.size_bytes,
                    created_at=b.created_at,
                    checksum=b.checksum,
                )
                for b in result.backups
            ],
        )

    except Exception as e:
        logger.error(f"Google Drive list failed: {e}")
        return RemoteBackupListResponse(
            success=False,
            error_message=str(e),
        )


@router.post("/providers/upload", response_model=UploadToProviderResponse)
async def upload_backup_to_provider(
    db: DbSession,
    admin: AdminUser,
    data: UploadToProviderRequest,
) -> UploadToProviderResponse:
    """Upload a local backup to a storage provider (admin only)."""
    # Get backup from history
    history = await db.get(BackupHistory, data.backup_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found",
        )

    if history.status != BackupStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup is not completed",
        )

    if not history.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found",
        )

    file_path = Path(history.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found on disk",
        )

    try:
        provider = get_storage_provider(data.provider_type, data.provider_config)
        result = await provider.upload(file_path, history.filename)

        if result.success:
            # Update history with remote info
            history.remote_id = result.remote_id
            await db.commit()

            return UploadToProviderResponse(
                success=True,
                message=f"Backup uploaded to {data.provider_type}",
                remote_id=result.remote_id,
                remote_path=result.remote_path,
            )
        else:
            return UploadToProviderResponse(
                success=False,
                message=result.error_message or "Upload failed",
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Upload to provider failed: {e}")
        return UploadToProviderResponse(
            success=False,
            message=str(e),
        )


@router.post("/providers/google-drive/download/{remote_id}")
async def download_from_google_drive(
    admin: AdminUser,
    remote_id: str,
    data: GoogleDriveTestRequest,
) -> FileResponse:
    """Download a backup from Google Drive (admin only)."""
    if not GOOGLE_DRIVE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Drive provider not available",
        )

    try:
        provider = get_storage_provider(
            "google_drive",
            {"service_account_json": data.service_account_json},
        )

        # Create temp file for download
        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / "backup_download.zip"

        result = await provider.download(remote_id, temp_path)

        if not result.success:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error_message or "Download failed",
            )

        # Get filename from Google Drive
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_dict = json.loads(data.service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        service = build("drive", "v3", credentials=credentials)
        file_metadata = service.files().get(fileId=remote_id, fields="name").execute()
        filename = file_metadata.get("name", "backup.zip")

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/zip",
            background=BackgroundTasks().add_task(
                lambda: shutil.rmtree(temp_dir, ignore_errors=True)
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Drive download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/providers/google-drive/{remote_id}")
async def delete_from_google_drive(
    admin: AdminUser,
    remote_id: str,
    data: GoogleDriveTestRequest,
) -> dict:
    """Delete a backup from Google Drive (admin only)."""
    if not GOOGLE_DRIVE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Drive provider not available",
        )

    try:
        provider = get_storage_provider(
            "google_drive",
            {"service_account_json": data.service_account_json},
        )

        success = await provider.delete(remote_id)

        if success:
            return {"success": True, "message": "Backup deleted from Google Drive"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete backup",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Drive delete failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# --- Dropbox Provider Operations ---


class DropboxTestRequest(BaseModel):
    """Request to test Dropbox credentials."""

    access_token: str


class DropboxTestResponse(BaseModel):
    """Response from Dropbox test."""

    success: bool
    message: str
    email: str | None = None
    account_name: str | None = None


@router.post("/providers/dropbox/test", response_model=DropboxTestResponse)
async def test_dropbox_credentials(
    admin: AdminUser,
    data: DropboxTestRequest,
) -> DropboxTestResponse:
    """Test Dropbox credentials (admin only).

    Dropbox works with both personal and business accounts using a simple access token.
    """
    if not DROPBOX_AVAILABLE:
        return DropboxTestResponse(
            success=False,
            message="Dropbox provider not available. Dependencies not installed.",
        )

    try:
        import dropbox
        from dropbox.exceptions import AuthError

        client = dropbox.Dropbox(data.access_token)
        account = client.users_get_current_account()

        return DropboxTestResponse(
            success=True,
            message=f"Connected to Dropbox as {account.name.display_name}",
            email=account.email,
            account_name=account.name.display_name,
        )

    except AuthError as e:
        return DropboxTestResponse(
            success=False,
            message=f"Authentication failed: Invalid or expired access token",
        )
    except Exception as e:
        logger.error(f"Dropbox test failed: {e}")
        return DropboxTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
        )


@router.post("/providers/dropbox/list", response_model=RemoteBackupListResponse)
async def list_dropbox_backups(
    admin: AdminUser,
    data: DropboxTestRequest,
) -> RemoteBackupListResponse:
    """List backups stored in Dropbox (admin only)."""
    if not DROPBOX_AVAILABLE:
        return RemoteBackupListResponse(
            success=False,
            error_message="Dropbox provider not available",
        )

    try:
        provider = get_storage_provider(
            "dropbox",
            {"access_token": data.access_token},
        )
        result = await provider.list_backups()

        if not result.success:
            return RemoteBackupListResponse(
                success=False,
                error_message=result.error_message,
            )

        return RemoteBackupListResponse(
            success=True,
            backups=[
                RemoteBackupResponse(
                    remote_id=b.remote_id,
                    filename=b.filename,
                    remote_path=b.remote_path,
                    size_bytes=b.size_bytes,
                    created_at=b.created_at,
                    checksum=b.checksum,
                )
                for b in result.backups
            ],
        )

    except Exception as e:
        logger.error(f"Dropbox list failed: {e}")
        return RemoteBackupListResponse(
            success=False,
            error_message=str(e),
        )


@router.delete("/providers/dropbox/{remote_id:path}")
async def delete_from_dropbox(
    admin: AdminUser,
    remote_id: str,
    data: DropboxTestRequest,
) -> dict:
    """Delete a backup from Dropbox (admin only).

    Note: remote_id is the file path in Dropbox.
    """
    if not DROPBOX_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dropbox provider not available",
        )

    try:
        provider = get_storage_provider(
            "dropbox",
            {"access_token": data.access_token},
        )

        success = await provider.delete(remote_id)

        if success:
            return {"success": True, "message": "Backup deleted from Dropbox"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete backup",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dropbox delete failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
