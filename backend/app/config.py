"""Application configuration from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/storagehub"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production-min-32-chars"
    access_token_expire_days: int = 30

    # AI Provider
    ai_provider: str = "openai"
    openai_api_key: str = ""
    google_application_credentials: str = ""

    # File Storage
    upload_dir: Path = Path("./uploads")
    max_upload_size_mb: int = 10

    # Frontend URL
    frontend_url: str = "http://localhost:5173"

    # Printer Defaults
    default_label_width_mm: float = 51.0
    default_label_height_mm: float = 25.0

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
