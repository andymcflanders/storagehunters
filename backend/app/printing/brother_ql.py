"""Brother QL printer driver."""

import asyncio
import io
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image, ImageDraw, ImageFont

from app.printing.base import BaseDriver, LabelContent
from app.services.qr_generator import QRGeneratorService


class BrotherQLDriver(BaseDriver):
    """Driver for Brother QL label printers."""

    # Label sizes in mm and their brother_ql identifiers
    LABEL_SIZES = {
        (62, 29): "62x29",
        (62, 100): "62x100",
        (29, 90): "29x90",
        (62, 0): "62",  # Continuous
        (29, 0): "29",  # Continuous
        (12, 0): "12",  # Continuous
    }

    def __init__(
        self,
        address: str,
        label_width_mm: float,
        label_height_mm: float,
        model: str = "QL-570",
    ):
        super().__init__(address, label_width_mm, label_height_mm)
        self.device_path = address  # e.g., "/dev/usb/lp0" or "usb://..."
        self.model = model
        self.label_size = self._get_label_size()

    def _get_label_size(self) -> str:
        """Determine the brother_ql label size identifier."""
        # Find closest matching label size
        width = int(self.label_width_mm)
        height = int(self.label_height_mm)

        # Check for exact match
        if (width, height) in self.LABEL_SIZES:
            return self.LABEL_SIZES[(width, height)]

        # Check for continuous labels
        if height == 0 or height > 200:
            if (width, 0) in self.LABEL_SIZES:
                return self.LABEL_SIZES[(width, 0)]

        # Default to 62x29 for small labels
        return "62x29"

    async def test_connection(self) -> bool:
        """Test connection to the Brother printer."""
        try:
            # Check if device exists
            if self.device_path.startswith("/dev/"):
                return Path(self.device_path).exists()

            # For USB addresses, try to list printers
            result = await asyncio.create_subprocess_exec(
                "brother_ql", "discover",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            return self.device_path in stdout.decode() or result.returncode == 0

        except FileNotFoundError:
            # brother_ql not installed
            return False
        except Exception:
            return False

    async def print_label(self, content: LabelContent) -> bool:
        """Print a label using brother_ql library."""
        # Generate the label image
        image_bytes = await self.generate_preview(content)

        try:
            # Save image to temp file
            with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name

            # Use brother_ql CLI to print
            result = await asyncio.create_subprocess_exec(
                "brother_ql",
                "-b", "pyusb" if "usb:" in self.device_path else "linux_kernel",
                "-m", self.model,
                "-p", self.device_path,
                "print",
                "-l", self.label_size,
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)

            return result.returncode == 0

        except FileNotFoundError:
            # brother_ql not installed
            return False
        except Exception:
            return False

    async def generate_preview(self, content: LabelContent) -> bytes:
        """Generate a label image for Brother QL printer."""
        # Brother QL-570 prints at 300 DPI
        dpi = 300
        width_px = int(self.label_width_mm * dpi / 25.4)
        height_px = int(self.label_height_mm * dpi / 25.4)

        # Create image (Brother uses 1-bit or grayscale)
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)

        # Generate QR code
        qr_service = QRGeneratorService()
        qr_size = min(width_px, height_px) - 40
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        # Position QR code on left
        qr_x = 20
        qr_y = (height_px - qr_size) // 2
        img.paste(qr_img, (qr_x, qr_y))

        # Text on right side
        text_x = qr_x + qr_size + 30
        text_y = 30

        # Fonts (Brother needs good resolution fonts)
        try:
            title_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
            )
            body_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20
            )
            small_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
            )
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Container name
        draw.text((text_x, text_y), content.container_name, fill="black", font=title_font)
        text_y += 40

        # Location
        draw.text((text_x, text_y), content.location_name, fill="black", font=body_font)
        text_y += 30

        # Contents if provided
        if content.contents_summary:
            # Truncate long text
            summary = content.contents_summary[:50]
            if len(content.contents_summary) > 50:
                summary += "..."
            draw.text((text_x, text_y), summary, fill="gray", font=small_font)
            text_y += 25

        # QR code text
        draw.text(
            (text_x, height_px - 40),
            content.container_qr_code,
            fill="gray",
            font=small_font,
        )

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
