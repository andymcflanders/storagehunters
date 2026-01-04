"""Base classes for backup storage providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Callable, Protocol, runtime_checkable


@dataclass
class UploadResult:
    """Result of an upload operation."""

    success: bool
    remote_id: str | None = None
    remote_path: str | None = None
    size_bytes: int = 0
    checksum: str | None = None
    error_message: str | None = None


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success: bool
    local_path: str | None = None
    size_bytes: int = 0
    error_message: str | None = None


@dataclass
class RemoteBackupInfo:
    """Information about a backup stored remotely."""

    remote_id: str
    filename: str
    remote_path: str
    size_bytes: int
    created_at: datetime
    checksum: str | None = None


@dataclass
class ListResult:
    """Result of listing backups."""

    success: bool
    backups: list[RemoteBackupInfo] = field(default_factory=list)
    error_message: str | None = None


@runtime_checkable
class StorageProvider(Protocol):
    """Protocol for backup storage providers."""

    async def test_connection(self) -> bool:
        """Test if the provider is accessible and authenticated."""
        ...

    async def upload(
        self,
        file_path: Path,
        filename: str,
        progress_callback: Callable | None = None,
    ) -> UploadResult:
        """Upload a backup file to the storage provider."""
        ...

    async def download(
        self,
        remote_id: str,
        local_path: Path,
        progress_callback: Callable | None = None,
    ) -> DownloadResult:
        """Download a backup file from the storage provider."""
        ...

    async def delete(self, remote_id: str) -> bool:
        """Delete a backup from the storage provider."""
        ...

    async def list_backups(self) -> ListResult:
        """List available backups in the storage provider."""
        ...


class BaseStorageProvider(ABC):
    """Abstract base class for storage providers."""

    def __init__(self, config: dict):
        """Initialize with provider-specific configuration."""
        self.config = config

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the provider is accessible and authenticated."""
        pass

    @abstractmethod
    async def upload(
        self,
        file_path: Path,
        filename: str,
        progress_callback: Callable | None = None,
    ) -> UploadResult:
        """Upload a backup file."""
        pass

    @abstractmethod
    async def download(
        self,
        remote_id: str,
        local_path: Path,
        progress_callback: Callable | None = None,
    ) -> DownloadResult:
        """Download a backup file."""
        pass

    @abstractmethod
    async def delete(self, remote_id: str) -> bool:
        """Delete a backup."""
        pass

    @abstractmethod
    async def list_backups(self) -> ListResult:
        """List available backups."""
        pass
