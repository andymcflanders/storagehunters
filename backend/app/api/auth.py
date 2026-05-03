"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, get_current_session
from app.models.user import Session, User
from app.schemas.user import LoginRequest, SessionResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=SessionResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: DbSession,
) -> SessionResponse:
    """Log in a user via card-tap (user_id) or email + password (admins)."""
    auth_service = AuthService(db)

    # Resolve email → user_id for the admin sign-in flow. Stops short of
    # confirming the email exists, so a typo'd email returns the same
    # 401 as a wrong password (no account-enumeration leak).
    user_id = request.user_id
    if user_id is None and request.email:
        result = await db.execute(
            select(User).where(func.lower(User.email) == request.email.strip().lower())
        )
        user = result.scalar_one_or_none()
        if user:
            user_id = user.id

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    session = await auth_service.login(user_id, request.password)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Set session cookie
    response.set_cookie(
        key="session_token",
        value=session.token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
    )

    user = await auth_service.get_user_by_id(session.user_id)
    return SessionResponse(
        token=session.token,
        expires_at=session.expires_at,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    response: Response,
    db: DbSession,
    session: Session = Depends(get_current_session),
) -> dict[str, str]:
    """Log out the current user."""
    auth_service = AuthService(db)
    await auth_service.delete_session(session)

    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """Get the current authenticated user."""
    return UserResponse.model_validate(current_user)
