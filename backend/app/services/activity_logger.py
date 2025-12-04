"""Activity logging service."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActionEnum, ActivityLog


class ActivityLogger:
    """Service for logging activity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        user_id: UUID | None,
        action: ActionEnum,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        details: dict[str, Any] | None = None,
    ) -> ActivityLog:
        """Log an activity."""
        log_entry = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def log_created(
        self,
        user_id: UUID | None,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
    ) -> ActivityLog:
        """Log a creation event."""
        return await self.log(
            user_id=user_id,
            action=ActionEnum.CREATED,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
        )

    async def log_updated(
        self,
        user_id: UUID | None,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        old_values: dict[str, Any],
        new_values: dict[str, Any],
    ) -> ActivityLog:
        """Log an update event."""
        return await self.log(
            user_id=user_id,
            action=ActionEnum.UPDATED,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details={"old": old_values, "new": new_values},
        )

    async def log_moved(
        self,
        user_id: UUID | None,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        from_location: str,
        to_location: str,
    ) -> ActivityLog:
        """Log a move event."""
        return await self.log(
            user_id=user_id,
            action=ActionEnum.MOVED,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details={"from": from_location, "to": to_location},
        )

    async def log_deleted(
        self,
        user_id: UUID | None,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
    ) -> ActivityLog:
        """Log a deletion event."""
        return await self.log(
            user_id=user_id,
            action=ActionEnum.DELETED,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
        )
