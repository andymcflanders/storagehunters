"""Dropbox storage provider using Access Token authentication.

Dropbox works with both personal and business accounts using a simple access token.
No complicated service account setup required - just generate an access token from
the Dropbox App Console.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import WriteMode

from app.backup.providers.base import (
    BaseStorageProvider,
    DownloadResult,
    ListResult,
    RemoteBackupInfo,
    UploadResult,
)

logger = logging.getLogger(__name__)

# Chunk size for uploading large files (150 MB)
CHUNK_SIZE = 150 * 1024 * 1024


class DropboxStorageProvider(BaseStorageProvider):
    """Dropbox storage provider using Access Token authentication.

    Works with both personal Dropbox and Dropbox Business accounts.
    """

    def __init__(self, config: dict):
        """
        Initialize Dropbox storage provider.

        Config keys:
            - access_token: Dropbox access token (required)
            - folder_path: Path within Dropbox for backups (default: "/StorageHub Backups")
        """
        super().__init__(config)
        self._client = None
        self._access_token = config.get("access_token")
        self._folder_path = config.get("folder_path", "/StorageHub Backups")
        # Ensure folder path starts with /
        if not self._folder_path.startswith("/"):
            self._folder_path = "/" + self._folder_path

    def _get_client(self) -> dropbox.Dropbox:
        """Get or create Dropbox client instance."""
        if self._client is None:
            if not self._access_token:
                raise ValueError("Dropbox access token not configured")
            self._client = dropbox.Dropbox(self._access_token)
        return self._client

    async def _ensure_folder(self) -> str:
        """Ensure the backup folder exists."""
        client = self._get_client()

        try:
            # Check if folder exists
            client.files_get_metadata(self._folder_path)
            logger.debug(f"Dropbox folder exists: {self._folder_path}")
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                # Create the folder
                try:
                    client.files_create_folder_v2(self._folder_path)
                    logger.info(f"Created Dropbox folder: {self._folder_path}")
                except ApiError as create_error:
                    # Folder might have been created by another process
                    if not (
                        create_error.error.is_path()
                        and create_error.error.get_path().is_conflict()
                    ):
                        raise
            else:
                raise

        return self._folder_path

    async def test_connection(self) -> tuple[bool, str, dict]:
        """
        Test Dropbox access and return account info.

        Returns:
            tuple: (success, account_email, account_info)
        """
        try:
            client = self._get_client()
            account = client.users_get_current_account()

            account_info = {
                "name": account.name.display_name,
                "email": account.email,
                "account_type": str(account.account_type),
            }

            logger.info(f"Dropbox connected as: {account.email}")
            return True, account.email, account_info

        except AuthError as e:
            logger.error(f"Dropbox authentication failed: {e}")
            raise ValueError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"Dropbox connection test failed: {e}")
            raise

    async def upload(
        self,
        file_path: Path,
        filename: str,
        progress_callback: Callable | None = None,
    ) -> UploadResult:
        """Upload backup to Dropbox."""
        try:
            client = self._get_client()
            folder_path = await self._ensure_folder()
            remote_path = f"{folder_path}/{filename}"

            # Calculate file size and checksum
            total_size = file_path.stat().st_size
            md5 = hashlib.md5()

            with open(file_path, "rb") as f:
                # Calculate checksum first
                for chunk in iter(lambda: f.read(8192), b""):
                    md5.update(chunk)
                checksum = md5.hexdigest()

                # Reset file position for upload
                f.seek(0)

                if total_size <= CHUNK_SIZE:
                    # Simple upload for smaller files
                    data = f.read()
                    result = client.files_upload(
                        data,
                        remote_path,
                        mode=WriteMode.overwrite,
                    )
                    if progress_callback:
                        progress_callback(100)
                else:
                    # Chunked upload for large files
                    upload_session_start_result = client.files_upload_session_start(
                        f.read(CHUNK_SIZE)
                    )
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=upload_session_start_result.session_id,
                        offset=f.tell(),
                    )
                    commit = dropbox.files.CommitInfo(
                        path=remote_path, mode=WriteMode.overwrite
                    )

                    uploaded = CHUNK_SIZE
                    if progress_callback:
                        progress_callback(int((uploaded / total_size) * 100))

                    while f.tell() < total_size:
                        remaining = total_size - f.tell()
                        if remaining <= CHUNK_SIZE:
                            # Final chunk
                            result = client.files_upload_session_finish(
                                f.read(remaining), cursor, commit
                            )
                        else:
                            client.files_upload_session_append_v2(
                                f.read(CHUNK_SIZE), cursor
                            )
                            cursor.offset = f.tell()

                        uploaded = f.tell()
                        if progress_callback:
                            progress_callback(int((uploaded / total_size) * 100))

            if progress_callback:
                progress_callback(100)

            logger.info(f"Uploaded backup to Dropbox: {remote_path}")

            return UploadResult(
                success=True,
                remote_id=result.id,
                remote_path=remote_path,
                size_bytes=total_size,
                checksum=checksum,
            )

        except Exception as e:
            logger.error(f"Dropbox upload failed: {e}")
            return UploadResult(success=False, error_message=str(e))

    async def download(
        self,
        remote_id: str,
        local_path: Path,
        progress_callback: Callable | None = None,
    ) -> DownloadResult:
        """Download backup from Dropbox."""
        try:
            client = self._get_client()

            # Get metadata first to know the size
            # remote_id in Dropbox is the file path or ID
            # Try to get by ID first, then by path
            try:
                metadata = client.files_get_metadata(remote_id)
            except ApiError:
                # If not found by ID, it might be a path
                metadata = client.files_get_metadata(remote_id)

            total_size = metadata.size if hasattr(metadata, "size") else 0
            file_path = metadata.path_display

            # Download file
            _, response = client.files_download(file_path)

            with open(local_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(int((downloaded / total_size) * 100))

            if progress_callback:
                progress_callback(100)

            logger.info(f"Downloaded backup from Dropbox: {file_path}")

            return DownloadResult(
                success=True,
                local_path=str(local_path),
                size_bytes=total_size,
            )

        except Exception as e:
            logger.error(f"Dropbox download failed: {e}")
            return DownloadResult(success=False, error_message=str(e))

    async def delete(self, remote_id: str) -> bool:
        """Delete backup from Dropbox."""
        try:
            client = self._get_client()

            # Try to delete by path (remote_id might be path or id)
            try:
                # First try to get metadata to find the actual path
                metadata = client.files_get_metadata(remote_id)
                path_to_delete = metadata.path_display
            except ApiError:
                # Assume it's already a path
                path_to_delete = remote_id

            client.files_delete_v2(path_to_delete)
            logger.info(f"Deleted backup from Dropbox: {path_to_delete}")
            return True

        except Exception as e:
            logger.error(f"Dropbox delete failed: {e}")
            return False

    async def list_backups(self) -> ListResult:
        """List backups in Dropbox folder."""
        try:
            client = self._get_client()
            folder_path = await self._ensure_folder()

            # List files in the backup folder
            result = client.files_list_folder(folder_path)
            backups = []

            while True:
                for entry in result.entries:
                    # Only include .zip files
                    if hasattr(entry, "name") and entry.name.endswith(".zip"):
                        # Get file metadata
                        if hasattr(entry, "size"):
                            size = entry.size
                        else:
                            size = 0

                        if hasattr(entry, "client_modified"):
                            created_at = entry.client_modified
                        elif hasattr(entry, "server_modified"):
                            created_at = entry.server_modified
                        else:
                            created_at = datetime.now()

                        # Get content hash if available
                        content_hash = None
                        if hasattr(entry, "content_hash"):
                            content_hash = entry.content_hash

                        backups.append(
                            RemoteBackupInfo(
                                remote_id=entry.path_display,
                                filename=entry.name,
                                remote_path=entry.path_display,
                                size_bytes=size,
                                created_at=created_at,
                                checksum=content_hash,
                            )
                        )

                if not result.has_more:
                    break

                result = client.files_list_folder_continue(result.cursor)

            # Sort by created_at descending
            backups.sort(key=lambda x: x.created_at, reverse=True)

            return ListResult(success=True, backups=backups)

        except Exception as e:
            logger.error(f"Dropbox list failed: {e}")
            return ListResult(success=False, error_message=str(e))
