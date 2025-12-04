"""Authentication service."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import Session, User

settings = get_settings()
ph = PasswordHasher()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def verify_password(self, user: User, password: str) -> bool:
        """Verify a user's password."""
        if not user.password_hash:
            return False
        try:
            ph.verify(user.password_hash, password)
            return True
        except VerifyMismatchError:
            return False

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return ph.hash(password)

    async def create_session(self, user: User) -> Session:
        """Create a new session for a user."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.access_token_expire_days
        )

        session = Session(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_by_token(self, token: str) -> Session | None:
        """Get a session by token."""
        result = await self.db.execute(
            select(Session)
            .where(Session.token == token)
            .where(Session.expires_at > datetime.now(timezone.utc))
        )
        return result.scalar_one_or_none()

    async def delete_session(self, session: Session) -> None:
        """Delete a session."""
        await self.db.delete(session)

    async def login(self, user_id: UUID, password: str | None = None) -> Session | None:
        """Attempt to log in a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        if user.requires_password:
            if not password or not await self.verify_password(user, password):
                return None

        return await self.create_session(user)
