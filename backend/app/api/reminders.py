"""Reminder API endpoints."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models import Container, Item, Reminder, ReminderType

router = APIRouter()


# Schemas
class ReminderCreate(BaseModel):
    """Schema for creating a reminder."""

    title: str
    description: str | None = None
    reminder_type: ReminderType = ReminderType.CUSTOM
    due_date: datetime
    item_id: uuid.UUID | None = None
    container_id: uuid.UUID | None = None
    is_recurring: bool = False
    recurrence_days: int | None = None


class ReminderUpdate(BaseModel):
    """Schema for updating a reminder."""

    title: str | None = None
    description: str | None = None
    reminder_type: ReminderType | None = None
    due_date: datetime | None = None
    is_recurring: bool | None = None
    recurrence_days: int | None = None


class ReminderResponse(BaseModel):
    """Schema for reminder response."""

    id: uuid.UUID
    title: str
    description: str | None
    reminder_type: ReminderType
    due_date: datetime
    is_completed: bool
    is_recurring: bool
    recurrence_days: int | None
    completed_at: datetime | None
    created_at: datetime
    item_id: uuid.UUID | None
    item_name: str | None
    container_id: uuid.UUID | None
    container_name: str | None
    is_overdue: bool

    class Config:
        from_attributes = True


class ReminderListResponse(BaseModel):
    """Schema for list of reminders."""

    items: list[ReminderResponse]
    total: int
    overdue_count: int
    upcoming_count: int


# Helper function
def reminder_to_response(reminder: Reminder) -> ReminderResponse:
    """Convert reminder model to response."""
    now = datetime.now(timezone.utc)
    is_overdue = not reminder.is_completed and reminder.due_date < now

    return ReminderResponse(
        id=reminder.id,
        title=reminder.title,
        description=reminder.description,
        reminder_type=reminder.reminder_type,
        due_date=reminder.due_date,
        is_completed=reminder.is_completed,
        is_recurring=reminder.is_recurring,
        recurrence_days=reminder.recurrence_days,
        completed_at=reminder.completed_at,
        created_at=reminder.created_at,
        item_id=reminder.item_id,
        item_name=reminder.item.name if reminder.item else None,
        container_id=reminder.container_id,
        container_name=reminder.container.name if reminder.container else None,
        is_overdue=is_overdue,
    )


# Endpoints
@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ReminderResponse:
    """Create a new reminder."""
    # Verify item exists if provided
    if data.item_id:
        result = await db.execute(select(Item).where(Item.id == data.item_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

    # Verify container exists if provided
    if data.container_id:
        result = await db.execute(select(Container).where(Container.id == data.container_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Container not found",
            )

    reminder = Reminder(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        reminder_type=data.reminder_type,
        due_date=data.due_date,
        item_id=data.item_id,
        container_id=data.container_id,
        is_recurring=data.is_recurring,
        recurrence_days=data.recurrence_days,
    )
    db.add(reminder)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Reminder)
        .options(selectinload(Reminder.item), selectinload(Reminder.container))
        .where(Reminder.id == reminder.id)
    )
    reminder = result.scalar_one()

    return reminder_to_response(reminder)


@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    db: DbSession,
    current_user: CurrentUser,
    include_completed: Annotated[bool, Query()] = False,
    item_id: Annotated[uuid.UUID | None, Query()] = None,
    container_id: Annotated[uuid.UUID | None, Query()] = None,
    upcoming_days: Annotated[int | None, Query()] = None,
) -> ReminderListResponse:
    """List reminders for the current user."""
    query = (
        select(Reminder)
        .options(selectinload(Reminder.item), selectinload(Reminder.container))
        .where(Reminder.user_id == current_user.id)
    )

    if not include_completed:
        query = query.where(Reminder.is_completed == False)  # noqa: E712

    if item_id:
        query = query.where(Reminder.item_id == item_id)

    if container_id:
        query = query.where(Reminder.container_id == container_id)

    if upcoming_days:
        future_date = datetime.now(timezone.utc) + timedelta(days=upcoming_days)
        query = query.where(Reminder.due_date <= future_date)

    query = query.order_by(Reminder.due_date.asc())
    result = await db.execute(query)
    reminders = result.scalars().all()

    now = datetime.now(timezone.utc)
    items = [reminder_to_response(r) for r in reminders]
    overdue_count = sum(1 for r in items if r.is_overdue)
    upcoming_count = sum(1 for r in items if not r.is_overdue and not r.is_completed)

    return ReminderListResponse(
        items=items,
        total=len(items),
        overdue_count=overdue_count,
        upcoming_count=upcoming_count,
    )


@router.get("/upcoming", response_model=ReminderListResponse)
async def get_upcoming_reminders(
    db: DbSession,
    current_user: CurrentUser,
    days: Annotated[int, Query(ge=1, le=30)] = 7,
) -> ReminderListResponse:
    """Get upcoming reminders for the next N days."""
    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days)

    result = await db.execute(
        select(Reminder)
        .options(selectinload(Reminder.item), selectinload(Reminder.container))
        .where(
            and_(
                Reminder.user_id == current_user.id,
                Reminder.is_completed == False,  # noqa: E712
                Reminder.due_date <= future_date,
            )
        )
        .order_by(Reminder.due_date.asc())
    )
    reminders = result.scalars().all()

    items = [reminder_to_response(r) for r in reminders]
    overdue_count = sum(1 for r in items if r.is_overdue)
    upcoming_count = sum(1 for r in items if not r.is_overdue)

    return ReminderListResponse(
        items=items,
        total=len(items),
        overdue_count=overdue_count,
        upcoming_count=upcoming_count,
    )


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ReminderResponse:
    """Get a specific reminder."""
    result = await db.execute(
        select(Reminder)
        .options(selectinload(Reminder.item), selectinload(Reminder.container))
        .where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    return reminder_to_response(reminder)


@router.patch("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: uuid.UUID,
    data: ReminderUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ReminderResponse:
    """Update a reminder."""
    result = await db.execute(
        select(Reminder)
        .options(selectinload(Reminder.item), selectinload(Reminder.container))
        .where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    await db.flush()

    return reminder_to_response(reminder)


@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
async def complete_reminder(
    reminder_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ReminderResponse:
    """Mark a reminder as completed."""
    result = await db.execute(
        select(Reminder)
        .options(selectinload(Reminder.item), selectinload(Reminder.container))
        .where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    now = datetime.now(timezone.utc)
    reminder.is_completed = True
    reminder.completed_at = now

    # If recurring, create the next reminder
    if reminder.is_recurring and reminder.recurrence_days:
        next_reminder = Reminder(
            user_id=current_user.id,
            title=reminder.title,
            description=reminder.description,
            reminder_type=reminder.reminder_type,
            due_date=reminder.due_date + timedelta(days=reminder.recurrence_days),
            item_id=reminder.item_id,
            container_id=reminder.container_id,
            is_recurring=True,
            recurrence_days=reminder.recurrence_days,
        )
        db.add(next_reminder)

    await db.flush()

    return reminder_to_response(reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a reminder."""
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    await db.delete(reminder)
