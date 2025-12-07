"""User API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth import AuthService
from app.services.image_storage import ImageStorageService

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users(db: DbSession) -> list[UserResponse]:
    """List all users."""
    result = await db.execute(select(User).order_by(User.name))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    """Create a new user."""
    # Check for duplicate email
    if user_data.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    from app.models.user import Language, UserRole

    auth_service = AuthService(db)

    # Convert role string to enum
    role = UserRole.ADMIN if user_data.role.value == "admin" else UserRole.USER
    # Convert language string to enum
    language = Language.NO if user_data.language.value == "no" else Language.EN

    user = User(
        name=user_data.name,
        email=user_data.email,
        requires_password=user_data.requires_password,
        role=role,
        language=language,
    )

    if user_data.password and user_data.requires_password:
        user.password_hash = auth_service.hash_password(user_data.password)

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: DbSession) -> UserResponse:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Update a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    auth_service = AuthService(db)

    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        # Check for duplicate email
        if user_data.email != user.email:
            result = await db.execute(select(User).where(User.email == user_data.email))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
        user.email = user_data.email
    if user_data.requires_password is not None:
        user.requires_password = user_data.requires_password
    if user_data.password is not None:
        user.password_hash = auth_service.hash_password(user_data.password)
    if user_data.language is not None:
        from app.models.user import Language
        user.language = Language.NO if user_data.language.value == "no" else Language.EN

    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)


@router.post("/{user_id}/avatar", response_model=UserResponse)
async def upload_avatar(
    user_id: UUID,
    file: UploadFile,
    db: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """Upload a user avatar."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type",
        )

    storage = ImageStorageService()
    content = await file.read()
    filename, filepath = await storage.save_image(user_id, file.filename or "avatar.jpg", content)

    user.avatar_url = storage.get_url(filepath)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)
