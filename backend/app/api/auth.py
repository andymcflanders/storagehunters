"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, get_current_session
from app.models.user import Session
from app.schemas.user import LoginRequest, SessionResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=SessionResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: DbSession,
) -> SessionResponse:
    """Log in a user."""
    auth_service = AuthService(db)
    session = await auth_service.login(request.user_id, request.password)

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
