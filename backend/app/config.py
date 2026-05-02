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

    # Security (required — no default; generate with: openssl rand -hex 32)
    secret_key: str
    access_token_expire_days: int = 30

    # CORS — comma-separated list of additional allowed origins beyond
    # frontend_url and the always-allowed localhost variants
    cors_origins: str = ""

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

    # Segmentation Settings
    segmentation_enabled: bool = True
    segmentation_provider: str = "local"  # "local" or "replicate"
    segmentation_confidence_threshold: float = 0.5
    segmentation_min_area_ratio: float = 1.0  # Minimum 1% of image area

    # Local FastSAM (when segmentation_provider = "local")
    fastsam_url: str = "http://fastsam:8001"

    # Replicate (when segmentation_provider = "replicate")
    replicate_api_token: str = ""
    replicate_sam_model: str = "meta/sam-2-base"  # or "adirik/grounded-sam", etc.

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
