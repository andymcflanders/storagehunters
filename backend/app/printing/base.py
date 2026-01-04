"""Base classes for printer drivers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class LabelTemplate(str, Enum):
    """Label template types."""

    QR_ONLY = "qr_only"  # QR code + container name only
    QR_AI_SUMMARY = "qr_ai_summary"  # QR + OpenAI-generated summary
    QR_FULL_CONTENTS = "qr_full_contents"  # QR + complete item list
    A4_FULL_DETAILS = "a4_full_details"  # A4 page with QR, AI summary, and item table with thumbnails


class MediaType(str, Enum):
    """Type of label media."""

    CONTINUOUS = "continuous"
    DIE_CUT = "die_cut"
    UNKNOWN = "unknown"


@dataclass
class DetectedMedia:
    """Information about detected printer media."""

    supported: bool  # Whether detection is supported
    width_mm: float | None = None  # Detected width in mm
    height_mm: float | None = None  # Detected height in mm (None for continuous)
    media_type: MediaType = MediaType.UNKNOWN
    printer_status: str = "unknown"  # "ready", "error", "out_of_media"
    error_message: str | None = None


@dataclass
class ItemDetail:
    """Detailed item information for A4 template."""

    name: str
    description: str | None = None
    owner_name: str | None = None
    size: str | None = None
    thumbnail_path: str | None = None  # Path to thumbnail image


@dataclass
class LabelContent:
    """Data for a label."""

    container_name: str
    container_qr_code: str
    location_name: str
    template: LabelTemplate = LabelTemplate.QR_ONLY

    # Legacy field for backward compatibility
    contents_summary: str | None = None

    # Template-specific fields (populated based on template)
    ai_summary: str | None = None  # For QR_AI_SUMMARY
    full_contents: list[str] = field(default_factory=list)  # For QR_FULL_CONTENTS
    item_count: int = 0

    # For A4_FULL_DETAILS template
    item_details: list[ItemDetail] = field(default_factory=list)


@runtime_checkable
class PrinterDriver(Protocol):
    """Protocol for printer drivers."""

    async def test_connection(self) -> bool:
        """Test if the printer is reachable."""
        ...

    async def print_label(self, content: LabelContent) -> bool:
        """Print a label with the given content."""
        ...

    async def generate_preview(self, content: LabelContent) -> bytes:
        """Generate a preview image of the label."""
        ...


class BaseDriver(ABC):
    """Abstract base class for printer drivers."""

    def __init__(
        self,
        address: str,
        label_width_mm: float,
        label_height_mm: float,
    ):
        self.address = address
        self.label_width_mm = label_width_mm
        self.label_height_mm = label_height_mm

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the printer is reachable."""
        pass

    @abstractmethod
    async def print_label(self, content: LabelContent) -> bool:
        """Print a label with the given content."""
        pass

    @abstractmethod
    async def generate_preview(self, content: LabelContent) -> bytes:
        """Generate a preview image of the label."""
        pass

    async def detect_media(self) -> DetectedMedia:
        """Detect currently loaded media.

        Default implementation returns "not supported".
        Override in subclasses that support media detection.
        """
        return DetectedMedia(
            supported=False,
            error_message="Media detection not supported for this printer type",
        )

    @property
    def supports_media_detection(self) -> bool:
        """Whether this driver supports media detection."""
        return False

    def _mm_to_dots(self, mm: float, dpi: int = 203) -> int:
        """Convert millimeters to printer dots."""
        return int(mm * dpi / 25.4)

    def _dots_to_mm(self, dots: int, dpi: int = 203) -> float:
        """Convert printer dots to millimeters."""
        return dots * 25.4 / dpi
