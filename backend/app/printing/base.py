"""Base classes for printer drivers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class LabelContent:
    """Data for a label."""

    container_name: str
    container_qr_code: str
    location_name: str
    contents_summary: str | None = None


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

    def _mm_to_dots(self, mm: float, dpi: int = 203) -> int:
        """Convert millimeters to printer dots."""
        return int(mm * dpi / 25.4)
