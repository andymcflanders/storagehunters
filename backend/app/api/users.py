"""User API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.user import User, UserRole
from app.schemas.user import PublicUserResponse, UserCreate, UserResponse, UserUpdate
from app.services.auth import AuthService
from app.services.image_storage import ImageStorageService

router = APIRouter()


@router.get("", response_model=list[PublicUserResponse])
async def list_users(
    db: DbSession,
    include_admins: bool = Query(
        True,
        description=(
            "If false, omit admin accounts. The login screen uses "
            "include_admins=false so admins don't appear in the household "
            "user-card grid — they sign in via email + password instead."
        ),
    ),
    include_profiles: bool = Query(
        True,
        description=(
            "If false, omit profile users (household members who own items "
            "but don't log in — typically small kids). The login screen "
            "passes include_profiles=false so they don't appear on the "
            "card grid; owner pickers leave it at the default true."
        ),
    ),
) -> list[PublicUserResponse]:
    """List users; optionally hide admins and/or profile users.

    Deliberately public: the pre-login card grid needs it. The response
    is stripped to the minimal fields a login card needs — no email,
    birthdate, gender, or role.
    """
    query = select(User).order_by(User.name)
    if not include_admins:
        query = query.where(User.role != UserRole.ADMIN)
    if not include_profiles:
        query = query.where(User.is_profile == False)  # noqa: E712
    result = await db.execute(query)
    users = result.scalars().all()
    return [PublicUserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: DbSession,
    admin: AdminUser,
) -> UserResponse:
    """Create a new user. Admin only.

    First-boot bootstrap goes through the public one-shot
    POST /api/setup/complete, which refuses once any user exists.
    """
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
        is_profile=user_data.is_profile,
        birthdate=user_data.birthdate,
        gender=user_data.gender,
    )

    if user_data.password and user_data.requires_password:
        user.password_hash = auth_service.hash_password(user_data.password)

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: DbSession, current_user: CurrentUser) -> UserResponse:
    """Get a user by ID. Requires authentication."""
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
    """Update a user. Users may update themselves; admins may update anyone."""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own account",
        )

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
    if user_data.is_profile is not None:
        user.is_profile = user_data.is_profile
    if user_data.birthdate is not None:
        user.birthdate = user_data.birthdate
    if user_data.gender is not None:
        from app.models.user import Gender
        user.gender = Gender(user_data.gender.value)

    # Guard the same invariant we enforce on create: an admin can't be
    # marked as a profile (a profile-flagged admin couldn't actually log
    # in via either path).
    if user.is_profile and user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot be marked as profile users",
        )

    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: DbSession,
    admin: AdminUser,
) -> None:
    """Delete a user. Admin only."""
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
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
    """Upload a user avatar. Users may set their own; admins may set anyone's."""
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own avatar",
        )
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
