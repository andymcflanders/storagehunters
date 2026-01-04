"""Google Drive storage provider using Service Account authentication.

IMPORTANT: Service accounts do not have storage quota. This provider requires:
1. A Google Workspace account with a Shared Drive (Team Drive), OR
2. A folder in a Shared Drive that the service account has access to

Regular shared folders will NOT work because files are still owned by the uploader.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from app.backup.providers.base import (
    BaseStorageProvider,
    DownloadResult,
    ListResult,
    RemoteBackupInfo,
    UploadResult,
)

logger = logging.getLogger(__name__)

# Required scopes for Google Drive access
SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveStorageProvider(BaseStorageProvider):
    """Google Drive storage provider using Service Account authentication.

    This provider requires a Shared Drive (Team Drive) for storage because
    service accounts do not have their own storage quota.
    """

    def __init__(self, config: dict):
        """
        Initialize Google Drive storage provider.

        Config keys:
            - service_account_json: Service account credentials JSON (required)
            - folder_id: Specific folder ID within a Shared Drive (optional)
            - shared_drive_id: Shared Drive ID to use (optional, auto-detected if not provided)
            - folder_name: Name for backup folder (default: "StorageHub Backups")
        """
        super().__init__(config)
        self._service = None
        self._folder_id = config.get("folder_id")
        self._shared_drive_id = config.get("shared_drive_id")
        self._folder_name = config.get("folder_name", "StorageHub Backups")
        self._credentials_json = config.get("service_account_json")

    def _get_service(self):
        """Get or create Google Drive service instance."""
        if self._service is None:
            if not self._credentials_json:
                raise ValueError("Service account credentials not configured")

            # Parse credentials JSON
            if isinstance(self._credentials_json, str):
                creds_dict = json.loads(self._credentials_json)
            else:
                creds_dict = self._credentials_json

            credentials = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES
            )
            self._service = build("drive", "v3", credentials=credentials)

        return self._service

    async def _find_shared_drive(self) -> dict | None:
        """Find a Shared Drive that the service account has access to."""
        service = self._get_service()

        try:
            # List all Shared Drives the service account can access
            results = service.drives().list(
                pageSize=10,
                fields="drives(id, name)"
            ).execute()

            drives = results.get("drives", [])
            if drives:
                logger.info(f"Found {len(drives)} Shared Drive(s)")
                return drives[0]  # Return first accessible shared drive

            return None
        except Exception as e:
            logger.debug(f"Error listing Shared Drives: {e}")
            return None

    async def _ensure_folder(self) -> tuple[str, str | None]:
        """
        Find or create a backup folder in a Shared Drive.

        Returns:
            tuple: (folder_id, shared_drive_id) - shared_drive_id may be None for regular Drive
        """
        if self._folder_id:
            return self._folder_id, self._shared_drive_id

        service = self._get_service()

        # First, try to find a Shared Drive
        shared_drive = await self._find_shared_drive()

        if shared_drive:
            self._shared_drive_id = shared_drive["id"]
            logger.info(f"Using Shared Drive: {shared_drive['name']} ({self._shared_drive_id})")

            # Look for existing backup folder in the Shared Drive
            query = f"name='{self._folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = (
                service.files()
                .list(
                    q=query,
                    corpora="drive",
                    driveId=self._shared_drive_id,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields="files(id, name)",
                )
                .execute()
            )
            files = results.get("files", [])

            if files:
                self._folder_id = files[0]["id"]
                logger.info(f"Found existing backup folder: {self._folder_id}")
                return self._folder_id, self._shared_drive_id

            # Create backup folder in the Shared Drive root
            file_metadata = {
                "name": self._folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self._shared_drive_id],
            }
            folder = (
                service.files()
                .create(
                    body=file_metadata,
                    fields="id",
                    supportsAllDrives=True,
                )
                .execute()
            )
            self._folder_id = folder.get("id")
            logger.info(f"Created backup folder in Shared Drive: {self._folder_id}")
            return self._folder_id, self._shared_drive_id

        # No Shared Drive found - this won't work for uploads
        raise ValueError(
            "No Shared Drive found. Service accounts cannot upload to regular Google Drive "
            "because they have no storage quota. You need:\n\n"
            "1. A Google Workspace account (not personal Gmail)\n"
            "2. A Shared Drive (Team Drive) created in that account\n"
            "3. The service account added as a Content Manager to that Shared Drive\n\n"
            "Personal Gmail accounts cannot use Shared Drives. Consider using a different "
            "backup provider or contact your IT admin to set up a Shared Drive."
        )

    async def test_connection(self) -> tuple[bool, str, str | None, list[dict] | None]:
        """
        Test Google Drive access and check for Shared Drives.

        Returns:
            tuple: (success, email, message, shared_drives)
        """
        try:
            service = self._get_service()

            # Get service account info
            about = service.about().get(fields="user").execute()
            email = about.get("user", {}).get("emailAddress", "unknown")
            logger.info(f"Google Drive connected as: {email}")

            # Check for Shared Drives
            try:
                results = service.drives().list(
                    pageSize=10,
                    fields="drives(id, name)"
                ).execute()
                shared_drives = results.get("drives", [])
            except Exception as e:
                logger.debug(f"Could not list Shared Drives: {e}")
                shared_drives = []

            return True, email, shared_drives

        except Exception as e:
            logger.error(f"Google Drive connection test failed: {e}")
            raise

    async def upload(
        self,
        file_path: Path,
        filename: str,
        progress_callback: Callable | None = None,
    ) -> UploadResult:
        """Upload backup to Google Drive (Shared Drive)."""
        try:
            service = self._get_service()
            folder_id, shared_drive_id = await self._ensure_folder()

            # Calculate checksum while preparing upload
            total_size = file_path.stat().st_size
            md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5.update(chunk)
            checksum = md5.hexdigest()

            # Prepare file metadata
            file_metadata = {
                "name": filename,
                "parents": [folder_id],
                "description": f"StorageHub backup created at {datetime.now().isoformat()}",
            }

            # Upload file with resumable upload for large files
            media = MediaFileUpload(
                str(file_path),
                mimetype="application/zip",
                resumable=True,
                chunksize=1024 * 1024,  # 1MB chunks
            )

            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id,name,size,webViewLink",
                supportsAllDrives=True,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and progress_callback:
                    progress_callback(int(status.progress() * 100))

            if progress_callback:
                progress_callback(100)

            logger.info(f"Uploaded backup to Google Drive: {response.get('id')}")

            return UploadResult(
                success=True,
                remote_id=response.get("id"),
                remote_path=response.get("webViewLink", ""),
                size_bytes=total_size,
                checksum=checksum,
            )

        except Exception as e:
            logger.error(f"Google Drive upload failed: {e}")
            return UploadResult(success=False, error_message=str(e))

    async def download(
        self,
        remote_id: str,
        local_path: Path,
        progress_callback: Callable | None = None,
    ) -> DownloadResult:
        """Download backup from Google Drive."""
        try:
            service = self._get_service()

            # Get file metadata first
            file_metadata = (
                service.files()
                .get(fileId=remote_id, fields="size,name", supportsAllDrives=True)
                .execute()
            )
            total_size = int(file_metadata.get("size", 0))

            # Download file
            request = service.files().get_media(fileId=remote_id)

            with open(local_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request, chunksize=1024 * 1024)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status and progress_callback:
                        progress_callback(int(status.progress() * 100))

            if progress_callback:
                progress_callback(100)

            logger.info(f"Downloaded backup from Google Drive: {remote_id}")

            return DownloadResult(
                success=True,
                local_path=str(local_path),
                size_bytes=total_size,
            )

        except Exception as e:
            logger.error(f"Google Drive download failed: {e}")
            return DownloadResult(success=False, error_message=str(e))

    async def delete(self, remote_id: str) -> bool:
        """Delete backup from Google Drive."""
        try:
            service = self._get_service()
            service.files().delete(fileId=remote_id, supportsAllDrives=True).execute()
            logger.info(f"Deleted backup from Google Drive: {remote_id}")
            return True
        except Exception as e:
            logger.error(f"Google Drive delete failed: {e}")
            return False

    async def list_backups(self) -> ListResult:
        """List backups in Google Drive folder."""
        try:
            service = self._get_service()
            folder_id, shared_drive_id = await self._ensure_folder()

            # Query for backup files in the folder
            query = f"'{folder_id}' in parents and trashed=false and (name contains '.zip')"

            list_params = {
                "q": query,
                "fields": "files(id, name, size, createdTime, md5Checksum, webViewLink)",
                "orderBy": "createdTime desc",
                "pageSize": 100,
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
            }

            # If using a Shared Drive, specify the corpora
            if shared_drive_id:
                list_params["corpora"] = "drive"
                list_params["driveId"] = shared_drive_id

            results = service.files().list(**list_params).execute()

            backups = []
            for f in results.get("files", []):
                try:
                    created_at = datetime.fromisoformat(
                        f.get("createdTime", "").replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    created_at = datetime.now()

                backups.append(
                    RemoteBackupInfo(
                        remote_id=f.get("id"),
                        filename=f.get("name"),
                        remote_path=f.get("webViewLink", ""),
                        size_bytes=int(f.get("size", 0)),
                        created_at=created_at,
                        checksum=f.get("md5Checksum"),
                    )
                )

            return ListResult(success=True, backups=backups)

        except Exception as e:
            logger.error(f"Google Drive list failed: {e}")
            return ListResult(success=False, error_message=str(e))
