"""Zebra ZPL printer driver."""

import asyncio
import io
import socket
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.printing.base import BaseDriver, LabelContent
from app.services.qr_generator import QRGeneratorService


class ZebraZPLDriver(BaseDriver):
    """Driver for Zebra printers using ZPL II protocol."""

    def __init__(
        self,
        address: str,
        label_width_mm: float,
        label_height_mm: float,
        port: int = 9100,
        dpi: int = 203,
    ):
        super().__init__(address, label_width_mm, label_height_mm)
        # Parse address - could be "ip:port" or just "ip"
        if ":" in address:
            parts = address.split(":")
            self.host = parts[0]
            self.port = int(parts[1])
        else:
            self.host = address
            self.port = port
        self.dpi = dpi

    async def test_connection(self) -> bool:
        """Test connection to the Zebra printer."""
        try:
            # Try to open a socket connection
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            await loop.run_in_executor(
                None, lambda: sock.connect((self.host, self.port))
            )

            # Send a simple status query
            sock.send(b"~HS")  # Host status query

            # Try to receive response
            sock.settimeout(2)
            try:
                response = sock.recv(1024)
                sock.close()
                return len(response) > 0
            except socket.timeout:
                sock.close()
                # No response but connection succeeded
                return True

        except (socket.error, socket.timeout, OSError):
            return False

    async def print_label(self, content: LabelContent) -> bool:
        """Print a label using ZPL commands."""
        zpl = self._generate_zpl(content)

        try:
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)

            await loop.run_in_executor(
                None, lambda: sock.connect((self.host, self.port))
            )
            await loop.run_in_executor(None, lambda: sock.send(zpl.encode("utf-8")))
            sock.close()
            return True

        except (socket.error, socket.timeout, OSError):
            return False

    async def generate_preview(self, content: LabelContent) -> bytes:
        """Generate a preview image of the label."""
        # Convert mm to pixels (assuming 96 DPI for screen)
        width_px = int(self.label_width_mm * 96 / 25.4)
        height_px = int(self.label_height_mm * 96 / 25.4)

        # Create image
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)

        # Draw border
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        # Generate QR code
        qr_service = QRGeneratorService()
        qr_size = min(width_px, height_px) - 20
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        # Position QR code on left side
        qr_x = 10
        qr_y = (height_px - qr_size) // 2
        img.paste(qr_img, (qr_x, qr_y))

        # Draw text on right side
        text_x = qr_x + qr_size + 15
        text_y = 15

        # Try to use a better font, fall back to default
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Container name
        draw.text((text_x, text_y), content.container_name, fill="black", font=title_font)
        text_y += 20

        # Location
        draw.text((text_x, text_y), content.location_name, fill="gray", font=body_font)
        text_y += 18

        # Contents summary if provided
        if content.contents_summary:
            # Wrap text if needed
            max_width = width_px - text_x - 10
            wrapped = self._wrap_text(content.contents_summary, small_font, max_width, draw)
            for line in wrapped[:2]:  # Max 2 lines
                draw.text((text_x, text_y), line, fill="gray", font=small_font)
                text_y += 12

        # QR code value at bottom
        draw.text((text_x, height_px - 20), content.container_qr_code, fill="gray", font=small_font)

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _generate_zpl(self, content: LabelContent) -> str:
        """Generate ZPL commands for the label."""
        width_dots = self._mm_to_dots(self.label_width_mm, self.dpi)
        height_dots = self._mm_to_dots(self.label_height_mm, self.dpi)

        # QR code size (about 40% of label height)
        qr_size = int(height_dots * 0.4)

        # Calculate positions
        qr_x = 20
        qr_y = (height_dots - qr_size) // 2
        text_x = qr_x + qr_size + 30

        zpl_lines = [
            "^XA",  # Start format
            f"^PW{width_dots}",  # Print width
            f"^LL{height_dots}",  # Label length
            "^PON",  # Print orientation normal
            "^LH0,0",  # Label home position
        ]

        # QR Code
        # ^BQ = QR code, N = normal, 2 = model 2, magnification 4
        qr_url = f"http://storagehub/c/{content.container_qr_code}"
        zpl_lines.extend([
            f"^FO{qr_x},{qr_y}",
            "^BQN,2,4",
            f"^FDMA,{qr_url}^FS",
        ])

        # Container name (larger font)
        zpl_lines.extend([
            f"^FO{text_x},20",
            "^A0N,30,30",  # Font A, 30 dots high
            f"^FD{content.container_name}^FS",
        ])

        # Location
        zpl_lines.extend([
            f"^FO{text_x},55",
            "^A0N,22,22",
            f"^FD{content.location_name}^FS",
        ])

        # Contents summary if provided
        if content.contents_summary:
            # Truncate if too long
            summary = content.contents_summary[:40]
            if len(content.contents_summary) > 40:
                summary += "..."
            zpl_lines.extend([
                f"^FO{text_x},85",
                "^A0N,18,18",
                f"^FD{summary}^FS",
            ])

        # QR code value at bottom
        zpl_lines.extend([
            f"^FO{text_x},{height_dots - 30}",
            "^A0N,16,16",
            f"^FD{content.container_qr_code}^FS",
        ])

        zpl_lines.append("^XZ")  # End format

        return "\n".join(zpl_lines)

    def _wrap_text(
        self, text: str, font: Any, max_width: int, draw: ImageDraw.ImageDraw
    ) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines
