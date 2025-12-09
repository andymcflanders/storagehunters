"""Authentication service."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.api_key import APIKey
from app.models.user import Session, User

settings = get_settings()
ph = PasswordHasher()


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


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

    # API Key methods

    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        scopes: list[str],
        description: str | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns the key object and the raw key (only available once)."""
        raw_key = APIKey.generate_key()
        key_hash = hash_api_key(raw_key)
        key_prefix = APIKey.get_prefix(raw_key)

        api_key = APIKey(
            user_id=user_id,
            name=name,
            description=description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes,
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key, raw_key

    async def get_api_key_by_key(self, raw_key: str) -> APIKey | None:
        """Get an API key by its raw key value."""
        key_hash = hash_api_key(raw_key)
        result = await self.db.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()

    async def get_api_key_by_id(self, key_id: UUID) -> APIKey | None:
        """Get an API key by its ID."""
        result = await self.db.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def list_api_keys(self, user_id: UUID) -> list[APIKey]:
        """List all API keys for a user."""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_api_key(self, api_key: APIKey) -> None:
        """Delete an API key."""
        await self.db.delete(api_key)
