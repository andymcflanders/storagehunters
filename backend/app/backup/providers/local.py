"""Local filesystem storage provider."""

import hashlib
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.backup.providers.base import (
    BaseStorageProvider,
    DownloadResult,
    ListResult,
    RemoteBackupInfo,
    UploadResult,
)

logger = logging.getLogger(__name__)


class LocalStorageProvider(BaseStorageProvider):
    """Local filesystem storage provider for backups."""

    def __init__(self, config: dict):
        """
        Initialize local storage provider.

        Config keys:
            - backup_dir: Directory to store backups (required)
        """
        super().__init__(config)
        self._backup_dir = Path(config.get("backup_dir", "./backups"))
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    async def test_connection(self) -> bool:
        """Test local storage access."""
        try:
            return self._backup_dir.exists() and os.access(self._backup_dir, os.W_OK)
        except Exception as e:
            logger.error(f"Local storage test failed: {e}")
            return False

    async def upload(
        self,
        file_path: Path,
        filename: str,
        progress_callback: Callable | None = None,
    ) -> UploadResult:
        """Copy backup to local directory."""
        try:
            dest_path = self._backup_dir / filename

            # Copy file with progress tracking
            total_size = file_path.stat().st_size
            copied = 0
            md5 = hashlib.md5()

            with open(file_path, "rb") as src:
                with open(dest_path, "wb") as dst:
                    while chunk := src.read(8192):
                        dst.write(chunk)
                        md5.update(chunk)
                        copied += len(chunk)
                        if progress_callback:
                            progress_callback(int(copied / total_size * 100))

            return UploadResult(
                success=True,
                remote_id=str(dest_path),
                remote_path=str(dest_path),
                size_bytes=total_size,
                checksum=md5.hexdigest(),
            )

        except Exception as e:
            logger.error(f"Local storage upload failed: {e}")
            return UploadResult(success=False, error_message=str(e))

    async def download(
        self,
        remote_id: str,
        local_path: Path,
        progress_callback: Callable | None = None,
    ) -> DownloadResult:
        """Copy backup from local directory."""
        try:
            src_path = Path(remote_id)
            if not src_path.exists():
                return DownloadResult(
                    success=False, error_message="Backup file not found"
                )

            total_size = src_path.stat().st_size
            copied = 0

            with open(src_path, "rb") as src:
                with open(local_path, "wb") as dst:
                    while chunk := src.read(8192):
                        dst.write(chunk)
                        copied += len(chunk)
                        if progress_callback:
                            progress_callback(int(copied / total_size * 100))

            return DownloadResult(
                success=True,
                local_path=str(local_path),
                size_bytes=total_size,
            )

        except Exception as e:
            logger.error(f"Local storage download failed: {e}")
            return DownloadResult(success=False, error_message=str(e))

    async def delete(self, remote_id: str) -> bool:
        """Delete backup from local directory."""
        try:
            path = Path(remote_id)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted local backup: {path}")
            return True
        except Exception as e:
            logger.error(f"Local storage delete failed: {e}")
            return False

    async def list_backups(self) -> ListResult:
        """List backups in local directory."""
        try:
            backups = []
            for f in self._backup_dir.glob("*.zip"):
                stat = f.stat()
                backups.append(
                    RemoteBackupInfo(
                        remote_id=str(f),
                        filename=f.name,
                        remote_path=str(f),
                        size_bytes=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                    )
                )

            # Also include encrypted backups
            for f in self._backup_dir.glob("*.zip.enc"):
                stat = f.stat()
                backups.append(
                    RemoteBackupInfo(
                        remote_id=str(f),
                        filename=f.name,
                        remote_path=str(f),
                        size_bytes=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                    )
                )

            # Sort by creation date, newest first
            backups.sort(key=lambda x: x.created_at, reverse=True)
            return ListResult(success=True, backups=backups)

        except Exception as e:
            logger.error(f"Local storage list failed: {e}")
            return ListResult(success=False, error_message=str(e))
