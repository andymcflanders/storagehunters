"""Backup storage providers."""

from app.backup.providers.base import (
    BaseStorageProvider,
    DownloadResult,
    ListResult,
    RemoteBackupInfo,
    StorageProvider,
    UploadResult,
)
from app.backup.providers.local import LocalStorageProvider
from app.models.backup import BackupProviderType

# Google Drive is optional - may not have dependencies installed
try:
    from app.backup.providers.google_drive import GoogleDriveStorageProvider

    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GoogleDriveStorageProvider = None
    GOOGLE_DRIVE_AVAILABLE = False

# Dropbox is optional - may not have dependencies installed
try:
    from app.backup.providers.dropbox import DropboxStorageProvider

    DROPBOX_AVAILABLE = True
except ImportError:
    DropboxStorageProvider = None
    DROPBOX_AVAILABLE = False

__all__ = [
    "BaseStorageProvider",
    "StorageProvider",
    "UploadResult",
    "DownloadResult",
    "ListResult",
    "RemoteBackupInfo",
    "LocalStorageProvider",
    "GoogleDriveStorageProvider",
    "GOOGLE_DRIVE_AVAILABLE",
    "DropboxStorageProvider",
    "DROPBOX_AVAILABLE",
    "get_storage_provider",
]


def get_storage_provider(
    provider_type: BackupProviderType | str, config: dict
) -> BaseStorageProvider:
    """
    Factory function to get a storage provider instance.

    Args:
        provider_type: The type of provider to create
        config: Provider-specific configuration

    Returns:
        A storage provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    if isinstance(provider_type, str):
        provider_type = BackupProviderType(provider_type)

    if provider_type == BackupProviderType.LOCAL:
        return LocalStorageProvider(config)
    elif provider_type == BackupProviderType.GOOGLE_DRIVE:
        if not GOOGLE_DRIVE_AVAILABLE:
            raise ValueError(
                "Google Drive provider not available. "
                "Install google-auth and google-api-python-client."
            )
        return GoogleDriveStorageProvider(config)
    elif provider_type == BackupProviderType.DROPBOX:
        if not DROPBOX_AVAILABLE:
            raise ValueError(
                "Dropbox provider not available. "
                "Install dropbox package."
            )
        return DropboxStorageProvider(config)
    else:
        raise ValueError(f"Unsupported storage provider: {provider_type}")
