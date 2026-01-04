"""Backup creation and restoration service."""

import hashlib
import json
import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_sync_db
from app.models.container import Container
from app.models.item import Item, ItemImage, ItemTag
from app.models.location import Location
from app.models.tag import Tag
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class BackupOptions:
    """Options for backup creation."""

    include_images: bool = False
    include_users: bool = False
    compression_level: int = 6


@dataclass
class BackupProgress:
    """Progress information for backup operation."""

    phase: str  # "preparing", "database", "images", "compressing", "completed"
    current: int = 0
    total: int = 0
    percentage: int = 0
    message: str = ""


@dataclass
class BackupResult:
    """Result of backup creation."""

    success: bool
    filename: str | None = None
    file_path: str | None = None
    size_bytes: int = 0
    checksum: str | None = None
    error_message: str | None = None
    statistics: dict = field(default_factory=dict)


@dataclass
class RestoreResult:
    """Result of backup restoration."""

    success: bool
    error_message: str | None = None
    statistics: dict = field(default_factory=dict)


class BackupService:
    """Service for creating and restoring backups."""

    VERSION = "1.0"

    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)

    def _serialize_uuid(self, value: Any) -> Any:
        """Serialize UUID and other special types to JSON-compatible format."""
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if hasattr(value, "value"):  # Enum
            return value.value
        return value

    def _export_locations(self, db: Session) -> list[dict]:
        """Export all locations."""
        result = db.execute(select(Location).order_by(Location.name))
        locations = result.scalars().all()

        return [
            {
                "id": str(loc.id),
                "name": loc.name,
                "description": loc.description,
                "address": loc.address,
                "sort_order": loc.sort_order,
                "created_at": loc.created_at.isoformat() if loc.created_at else None,
                "updated_at": loc.updated_at.isoformat() if loc.updated_at else None,
            }
            for loc in locations
        ]

    def _export_containers(self, db: Session) -> list[dict]:
        """Export all containers."""
        result = db.execute(select(Container).order_by(Container.name))
        containers = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "name": c.name,
                "location_id": str(c.location_id),
                "parent_container_id": str(c.parent_container_id)
                if c.parent_container_id
                else None,
                "qr_code": c.qr_code,
                "notes": c.notes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in containers
        ]

    def _export_tags(self, db: Session) -> list[dict]:
        """Export all tags."""
        result = db.execute(select(Tag).order_by(Tag.name))
        tags = result.scalars().all()

        return [
            {
                "id": str(t.id),
                "name": t.name,
                "user_created": t.user_created,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tags
        ]

    def _export_items(self, db: Session) -> tuple[list[dict], list[dict]]:
        """Export all items with their tags and images."""
        # Get all items
        items_result = db.execute(select(Item).order_by(Item.name))
        items = items_result.scalars().all()

        # Get all item tags
        item_tags_result = db.execute(select(ItemTag))
        item_tags = item_tags_result.scalars().all()

        # Build tag map
        item_tag_map: dict[str, list[str]] = {}
        for it in item_tags:
            item_id = str(it.item_id)
            if item_id not in item_tag_map:
                item_tag_map[item_id] = []
            item_tag_map[item_id].append(str(it.tag_id))

        # Get all images
        images_result = db.execute(select(ItemImage))
        images = images_result.scalars().all()

        item_image_map: dict[str, list[dict]] = {}
        image_list = []

        for img in images:
            item_id = str(img.item_id)
            if item_id not in item_image_map:
                item_image_map[item_id] = []

            img_data = {
                "id": str(img.id),
                "item_id": str(img.item_id),
                "filename": img.filename,
                "filepath": img.filepath,
                "ai_tags": img.ai_tags,
                "ai_description": img.ai_description,
                "ai_processed": img.ai_processed,
                "is_segmented": img.is_segmented,
                "created_at": img.created_at.isoformat() if img.created_at else None,
            }
            item_image_map[item_id].append(img_data)
            image_list.append(img_data)

        # Build items data
        items_data = []
        for item in items:
            items_data.append(
                {
                    "id": str(item.id),
                    "name": item.name,
                    "description": item.description,
                    "container_id": str(item.container_id),
                    "owner_id": str(item.owner_id) if item.owner_id else None,
                    "size": item.size,
                    "condition": item.condition.value if item.condition else None,
                    "seasonal": item.seasonal.value if item.seasonal else None,
                    "value_estimate": (
                        float(item.value_estimate) if item.value_estimate else None
                    ),
                    "ai_name": item.ai_name,
                    "ai_name_no": item.ai_name_no,
                    "ai_description": item.ai_description,
                    "ai_description_no": item.ai_description_no,
                    "ai_processed": item.ai_processed,
                    "needs_review": item.needs_review,
                    "primary_image_id": (
                        str(item.primary_image_id) if item.primary_image_id else None
                    ),
                    "created_at": (
                        item.created_at.isoformat() if item.created_at else None
                    ),
                    "updated_at": (
                        item.updated_at.isoformat() if item.updated_at else None
                    ),
                    "tag_ids": item_tag_map.get(str(item.id), []),
                    "image_ids": [
                        img["id"] for img in item_image_map.get(str(item.id), [])
                    ],
                }
            )

        return items_data, image_list

    def _export_users(self, db: Session) -> list[dict]:
        """Export users (excluding password hashes)."""
        result = db.execute(select(User).order_by(User.name))
        users = result.scalars().all()

        return [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "role": u.role.value if u.role else None,
                "language": u.language.value if u.language else None,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
            for u in users
        ]

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def create_backup(
        self,
        options: BackupOptions,
        progress_callback: Callable | None = None,
    ) -> BackupResult:
        """
        Create a backup archive.

        Args:
            options: Backup configuration options
            progress_callback: Optional callback for progress updates

        Returns:
            BackupResult with backup details
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"storagehub_backup_{timestamp}.zip"
        temp_dir = Path(tempfile.mkdtemp())

        statistics = {
            "locations_count": 0,
            "containers_count": 0,
            "items_count": 0,
            "tags_count": 0,
            "images_count": 0,
        }

        try:
            # Report progress
            if progress_callback:
                progress_callback(
                    BackupProgress(phase="preparing", message="Preparing backup...")
                )

            # Create database directory
            db_dir = temp_dir / "database"
            db_dir.mkdir()

            with get_sync_db() as db:
                # Phase 1: Export database tables
                if progress_callback:
                    progress_callback(
                        BackupProgress(
                            phase="database", message="Exporting locations..."
                        )
                    )

                # Locations
                locations_data = self._export_locations(db)
                statistics["locations_count"] = len(locations_data)
                with open(db_dir / "locations.json", "w") as f:
                    json.dump(locations_data, f, indent=2)

                # Containers
                if progress_callback:
                    progress_callback(
                        BackupProgress(
                            phase="database", message="Exporting containers..."
                        )
                    )
                containers_data = self._export_containers(db)
                statistics["containers_count"] = len(containers_data)
                with open(db_dir / "containers.json", "w") as f:
                    json.dump(containers_data, f, indent=2)

                # Tags
                if progress_callback:
                    progress_callback(
                        BackupProgress(phase="database", message="Exporting tags...")
                    )
                tags_data = self._export_tags(db)
                statistics["tags_count"] = len(tags_data)
                with open(db_dir / "tags.json", "w") as f:
                    json.dump(tags_data, f, indent=2)

                # Items and images metadata
                if progress_callback:
                    progress_callback(
                        BackupProgress(phase="database", message="Exporting items...")
                    )
                items_data, images_data = self._export_items(db)
                statistics["items_count"] = len(items_data)
                statistics["images_count"] = len(images_data)

                with open(db_dir / "items.json", "w") as f:
                    json.dump(items_data, f, indent=2)

                with open(db_dir / "images.json", "w") as f:
                    json.dump(images_data, f, indent=2)

                # Optional: Users
                if options.include_users:
                    if progress_callback:
                        progress_callback(
                            BackupProgress(
                                phase="database", message="Exporting users..."
                            )
                        )
                    users_data = self._export_users(db)
                    with open(db_dir / "users.json", "w") as f:
                        json.dump(users_data, f, indent=2)

            # Phase 2: Copy images (if requested)
            if options.include_images and images_data:
                images_dir = temp_dir / "images"
                images_dir.mkdir()

                total_images = len(images_data)
                for idx, img in enumerate(images_data):
                    if progress_callback:
                        progress_callback(
                            BackupProgress(
                                phase="images",
                                current=idx + 1,
                                total=total_images,
                                percentage=int((idx + 1) / total_images * 100),
                                message=f"Copying image {idx + 1}/{total_images}",
                            )
                        )

                    src_path = self.upload_dir / img["filepath"]
                    if src_path.exists():
                        dest_path = images_dir / img["filepath"]
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_path, dest_path)

            # Create manifest
            manifest = {
                "version": self.VERSION,
                "created_at": datetime.utcnow().isoformat(),
                "storagehub_version": "1.0.0",
                "contents": {
                    "include_images": options.include_images,
                    "include_users": options.include_users,
                },
                "statistics": statistics,
            }
            with open(temp_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)

            # Phase 3: Create ZIP archive
            if progress_callback:
                progress_callback(
                    BackupProgress(phase="compressing", message="Creating archive...")
                )

            zip_path = temp_dir / filename
            with zipfile.ZipFile(
                zip_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=options.compression_level,
            ) as zf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file() and file_path != zip_path:
                        arcname = file_path.relative_to(temp_dir)
                        zf.write(file_path, arcname)

            # Calculate checksum
            checksum = self._calculate_checksum(zip_path)
            file_size = zip_path.stat().st_size

            # Move to final location (backup directory)
            backup_dir = Path(settings.upload_dir).parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            final_path = backup_dir / filename
            shutil.move(str(zip_path), str(final_path))

            if progress_callback:
                progress_callback(
                    BackupProgress(
                        phase="completed",
                        percentage=100,
                        message="Backup completed successfully",
                    )
                )

            return BackupResult(
                success=True,
                filename=filename,
                file_path=str(final_path),
                size_bytes=file_size,
                checksum=checksum,
                statistics=statistics,
            )

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return BackupResult(success=False, error_message=str(e))

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def verify_backup(self, backup_path: Path) -> tuple[bool, dict | None, str | None]:
        """
        Verify a backup file and return its manifest.

        Returns:
            Tuple of (is_valid, manifest, error_message)
        """
        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                # Check for manifest
                if "manifest.json" not in zf.namelist():
                    return False, None, "Invalid backup: manifest.json not found"

                # Read and parse manifest
                manifest_data = zf.read("manifest.json")
                manifest = json.loads(manifest_data)

                # Verify version compatibility
                version = manifest.get("version", "0.0")
                if version != self.VERSION:
                    return (
                        False,
                        manifest,
                        f"Backup version {version} may not be compatible",
                    )

                # Verify required files exist
                required_files = [
                    "database/locations.json",
                    "database/containers.json",
                    "database/items.json",
                    "database/tags.json",
                ]
                for req_file in required_files:
                    if req_file not in zf.namelist():
                        return False, manifest, f"Missing required file: {req_file}"

                return True, manifest, None

        except zipfile.BadZipFile:
            return False, None, "Invalid or corrupted ZIP file"
        except json.JSONDecodeError:
            return False, None, "Invalid manifest.json format"
        except Exception as e:
            return False, None, str(e)

    def restore_backup(
        self,
        backup_path: Path,
        restore_images: bool = True,
        progress_callback: Callable | None = None,
    ) -> RestoreResult:
        """
        Restore from a backup archive.

        Args:
            backup_path: Path to the backup ZIP file
            restore_images: Whether to restore images
            progress_callback: Optional callback for progress updates

        Returns:
            RestoreResult with restoration details
        """
        # Verify backup first
        is_valid, manifest, error = self.verify_backup(backup_path)
        if not is_valid:
            return RestoreResult(success=False, error_message=error)

        temp_dir = Path(tempfile.mkdtemp())
        statistics = {
            "locations_restored": 0,
            "containers_restored": 0,
            "items_restored": 0,
            "tags_restored": 0,
            "images_restored": 0,
        }

        try:
            if progress_callback:
                progress_callback(
                    BackupProgress(phase="preparing", message="Extracting backup...")
                )

            # Extract backup
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extractall(temp_dir)

            db_dir = temp_dir / "database"

            with get_sync_db() as db:
                # Restore in order of dependencies

                # 1. Tags
                if progress_callback:
                    progress_callback(
                        BackupProgress(phase="database", message="Restoring tags...")
                    )

                with open(db_dir / "tags.json", "r") as f:
                    tags_data = json.load(f)

                tag_id_map: dict[str, UUID] = {}
                for tag_data in tags_data:
                    # Check if tag already exists
                    existing = db.execute(
                        select(Tag).where(Tag.name == tag_data["name"])
                    ).scalar_one_or_none()

                    if existing:
                        tag_id_map[tag_data["id"]] = existing.id
                    else:
                        new_tag = Tag(
                            name=tag_data["name"],
                            user_created=tag_data.get("user_created", False),
                        )
                        db.add(new_tag)
                        db.flush()
                        tag_id_map[tag_data["id"]] = new_tag.id
                        statistics["tags_restored"] += 1

                # 2. Locations
                if progress_callback:
                    progress_callback(
                        BackupProgress(
                            phase="database", message="Restoring locations..."
                        )
                    )

                with open(db_dir / "locations.json", "r") as f:
                    locations_data = json.load(f)

                location_id_map: dict[str, UUID] = {}
                for loc_data in locations_data:
                    # Check if location exists by name
                    existing = db.execute(
                        select(Location).where(Location.name == loc_data["name"])
                    ).scalar_one_or_none()

                    if existing:
                        location_id_map[loc_data["id"]] = existing.id
                    else:
                        new_loc = Location(
                            name=loc_data["name"],
                            description=loc_data.get("description"),
                            address=loc_data.get("address"),
                            sort_order=loc_data.get("sort_order", 0),
                        )
                        db.add(new_loc)
                        db.flush()
                        location_id_map[loc_data["id"]] = new_loc.id
                        statistics["locations_restored"] += 1

                # 3. Containers (first pass - no parents)
                if progress_callback:
                    progress_callback(
                        BackupProgress(
                            phase="database", message="Restoring containers..."
                        )
                    )

                with open(db_dir / "containers.json", "r") as f:
                    containers_data = json.load(f)

                container_id_map: dict[str, UUID] = {}
                containers_with_parents = []

                for cont_data in containers_data:
                    # Check if container exists by qr_code
                    existing = db.execute(
                        select(Container).where(Container.qr_code == cont_data["qr_code"])
                    ).scalar_one_or_none()

                    if existing:
                        container_id_map[cont_data["id"]] = existing.id
                    else:
                        location_id = location_id_map.get(cont_data["location_id"])
                        if not location_id:
                            continue

                        new_cont = Container(
                            name=cont_data["name"],
                            location_id=location_id,
                            qr_code=cont_data["qr_code"],
                            notes=cont_data.get("notes"),
                        )
                        db.add(new_cont)
                        db.flush()
                        container_id_map[cont_data["id"]] = new_cont.id
                        statistics["containers_restored"] += 1

                        if cont_data.get("parent_container_id"):
                            containers_with_parents.append(
                                (new_cont.id, cont_data["parent_container_id"])
                            )

                # Update container parents
                for cont_id, parent_old_id in containers_with_parents:
                    parent_new_id = container_id_map.get(parent_old_id)
                    if parent_new_id:
                        db.execute(
                            Container.__table__.update()
                            .where(Container.id == cont_id)
                            .values(parent_container_id=parent_new_id)
                        )

                # 4. Items
                if progress_callback:
                    progress_callback(
                        BackupProgress(phase="database", message="Restoring items...")
                    )

                with open(db_dir / "items.json", "r") as f:
                    items_data = json.load(f)

                item_id_map: dict[str, UUID] = {}
                for item_data in items_data:
                    container_id = container_id_map.get(item_data["container_id"])
                    if not container_id:
                        continue

                    # Create item
                    new_item = Item(
                        name=item_data["name"],
                        description=item_data.get("description"),
                        container_id=container_id,
                        size=item_data.get("size"),
                        ai_name=item_data.get("ai_name"),
                        ai_name_no=item_data.get("ai_name_no"),
                        ai_description=item_data.get("ai_description"),
                        ai_description_no=item_data.get("ai_description_no"),
                        ai_processed=item_data.get("ai_processed", False),
                        needs_review=item_data.get("needs_review", False),
                    )

                    # Handle condition enum
                    if item_data.get("condition"):
                        from app.models.item import ConditionEnum

                        try:
                            new_item.condition = ConditionEnum(item_data["condition"])
                        except ValueError:
                            pass

                    # Handle seasonal enum
                    if item_data.get("seasonal"):
                        from app.models.item import SeasonalEnum

                        try:
                            new_item.seasonal = SeasonalEnum(item_data["seasonal"])
                        except ValueError:
                            pass

                    db.add(new_item)
                    db.flush()
                    item_id_map[item_data["id"]] = new_item.id
                    statistics["items_restored"] += 1

                    # Restore item tags
                    for old_tag_id in item_data.get("tag_ids", []):
                        new_tag_id = tag_id_map.get(old_tag_id)
                        if new_tag_id:
                            from app.models.item import ItemTag

                            item_tag = ItemTag(item_id=new_item.id, tag_id=new_tag_id)
                            db.add(item_tag)

                # 5. Images (if requested)
                if restore_images:
                    images_dir = temp_dir / "images"
                    if images_dir.exists():
                        with open(db_dir / "images.json", "r") as f:
                            images_data = json.load(f)

                        total_images = len(images_data)
                        for idx, img_data in enumerate(images_data):
                            if progress_callback:
                                progress_callback(
                                    BackupProgress(
                                        phase="images",
                                        current=idx + 1,
                                        total=total_images,
                                        percentage=int((idx + 1) / total_images * 100),
                                        message=f"Restoring image {idx + 1}/{total_images}",
                                    )
                                )

                            item_id = item_id_map.get(img_data["item_id"])
                            if not item_id:
                                continue

                            # Copy image file
                            src_path = images_dir / img_data["filepath"]
                            if src_path.exists():
                                dest_path = self.upload_dir / img_data["filepath"]
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src_path, dest_path)

                                # Create image record
                                new_image = ItemImage(
                                    item_id=item_id,
                                    filename=img_data["filename"],
                                    filepath=img_data["filepath"],
                                    ai_tags=img_data.get("ai_tags"),
                                    ai_description=img_data.get("ai_description"),
                                    ai_processed=img_data.get("ai_processed", False),
                                    is_segmented=img_data.get("is_segmented", False),
                                )
                                db.add(new_image)
                                statistics["images_restored"] += 1

                db.commit()

            if progress_callback:
                progress_callback(
                    BackupProgress(
                        phase="completed",
                        percentage=100,
                        message="Restore completed successfully",
                    )
                )

            return RestoreResult(success=True, statistics=statistics)

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return RestoreResult(success=False, error_message=str(e))

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
