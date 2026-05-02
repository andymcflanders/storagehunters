"""Image storage service."""

import shutil
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

import aiofiles

from app.config import get_settings

settings = get_settings()


class ImageStorageService:
    """Service for managing image storage."""

    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _get_storage_path(self, item_id: UUID) -> Path:
        """Get the storage path for an item's images."""
        date_prefix = datetime.now().strftime("%Y/%m")
        path = self.upload_dir / date_prefix / str(item_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename preserving the extension."""
        ext = Path(original_filename).suffix.lower()
        return f"{uuid4()}{ext}"

    async def save_image(
        self, item_id: UUID, filename: str, content: bytes
    ) -> tuple[str, str]:
        """
        Save an image for an item.

        Returns:
            Tuple of (filename, relative_filepath)
        """
        storage_path = self._get_storage_path(item_id)
        safe_filename = self._generate_filename(filename)
        file_path = storage_path / safe_filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Return relative path from upload_dir
        relative_path = str(file_path.relative_to(self.upload_dir))
        return safe_filename, relative_path

    async def delete_image(self, filepath: str) -> bool:
        """Delete an image file."""
        full_path = self.upload_dir / filepath
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def get_full_path(self, filepath: str) -> Path:
        """Get the full filesystem path for a relative filepath."""
        return self.upload_dir / filepath

    def get_url(self, filepath: str) -> str:
        """Get the URL for accessing an image."""
        return f"/uploads/{filepath}"
