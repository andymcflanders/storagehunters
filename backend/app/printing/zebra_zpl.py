"""Zebra ZPL printer driver."""

import asyncio
import io
import socket
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.printing.base import BaseDriver, DetectedMedia, LabelContent, LabelTemplate, MediaType
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

    @property
    def supports_media_detection(self) -> bool:
        """Zebra ZPL printers support media detection via ~HS command."""
        return True

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

    async def detect_media(self) -> DetectedMedia:
        """Detect currently loaded media using Zebra ~HS command.

        The ~HS (Host Status) command returns printer status including:
        - Print width in dots
        - Label length in dots (0 for continuous media)
        - Paper out status
        """
        try:
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            await loop.run_in_executor(
                None, lambda: sock.connect((self.host, self.port))
            )

            # Send Host Status request
            sock.send(b"~HS")

            # Read response
            sock.settimeout(3)
            response = b""
            try:
                while True:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response += chunk
                    # Response ends with ETX (0x03) characters
                    if response.count(b"\x03") >= 3:
                        break
            except socket.timeout:
                pass

            sock.close()

            if not response:
                return DetectedMedia(
                    supported=True,
                    error_message="No response from printer",
                    printer_status="error",
                )

            return self._parse_host_status(response)

        except (socket.error, socket.timeout, OSError) as e:
            return DetectedMedia(
                supported=True,
                error_message=f"Connection failed: {e!s}",
                printer_status="error",
            )

    def _parse_host_status(self, response: bytes) -> DetectedMedia:
        """Parse the ~HS response from Zebra printer.

        Response format (3 strings separated by ETX 0x03):
        String 1: Communication diagnostics
        String 2: Paper status info
        String 3: Contains print width, label length, etc.

        Example response fields in String 3:
        - Field 1: Print width in dots
        - Field 2: Media type (0=continuous, 1=die-cut)
        - Field 6: Label length in dots
        - Field 20: Paper out flag
        """
        try:
            # Split by ETX character
            parts = response.split(b"\x03")

            # We need at least 3 parts
            if len(parts) < 3:
                return DetectedMedia(
                    supported=True,
                    error_message="Invalid response format",
                    printer_status="unknown",
                )

            # Parse String 2 for paper status (starts with STX 0x02)
            string2 = parts[1].lstrip(b"\x02").decode("ascii", errors="ignore").strip()
            fields2 = string2.split(",")

            # Parse String 3 for dimensions
            string3 = parts[2].lstrip(b"\x02").decode("ascii", errors="ignore").strip()
            fields3 = string3.split(",")

            # Extract values from response
            width_dots = 0
            length_dots = 0
            media_type = MediaType.UNKNOWN
            paper_out = False

            # String 2 field 1 is paper out (0=no, 1=yes)
            if len(fields2) > 0:
                try:
                    paper_out = int(fields2[0]) == 1
                except ValueError:
                    pass

            # String 3 field 1 is print width in dots
            if len(fields3) > 0:
                try:
                    width_dots = int(fields3[0])
                except ValueError:
                    pass

            # String 3 field 2 is media type (0=continuous, 1=die-cut gap, 2=die-cut mark)
            if len(fields3) > 1:
                try:
                    mt = int(fields3[1])
                    if mt == 0:
                        media_type = MediaType.CONTINUOUS
                    elif mt in (1, 2):
                        media_type = MediaType.DIE_CUT
                except ValueError:
                    pass

            # String 3 field 6 is label length in dots (0 for continuous)
            if len(fields3) > 5:
                try:
                    length_dots = int(fields3[5])
                except ValueError:
                    pass

            # Convert dots to mm
            width_mm = self._dots_to_mm(width_dots, self.dpi) if width_dots > 0 else None
            height_mm = self._dots_to_mm(length_dots, self.dpi) if length_dots > 0 else None

            # Determine printer status
            if paper_out:
                printer_status = "out_of_media"
            else:
                printer_status = "ready"

            return DetectedMedia(
                supported=True,
                width_mm=width_mm,
                height_mm=height_mm,
                media_type=media_type,
                printer_status=printer_status,
            )

        except Exception as e:
            return DetectedMedia(
                supported=True,
                error_message=f"Failed to parse response: {e!s}",
                printer_status="unknown",
            )

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
        """Generate a preview image of the label based on template type."""
        # Convert mm to pixels (assuming 96 DPI for screen)
        width_px = int(self.label_width_mm * 96 / 25.4)
        height_px = int(self.label_height_mm * 96 / 25.4)

        # Route to appropriate template renderer
        if content.template == LabelTemplate.QR_ONLY:
            return self._preview_qr_only(content, width_px, height_px)
        elif content.template == LabelTemplate.QR_AI_SUMMARY:
            return self._preview_ai_summary(content, width_px, height_px)
        elif content.template == LabelTemplate.QR_FULL_CONTENTS:
            return self._preview_full_contents(content, width_px, height_px)
        else:
            return self._preview_legacy(content, width_px, height_px)

    def _get_fonts(self) -> tuple:
        """Load fonts for preview rendering."""
        try:
            title_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14
            )
            body_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
            )
            small_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9
            )
            tiny_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8
            )
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            tiny_font = ImageFont.load_default()
        return title_font, body_font, small_font, tiny_font

    def _preview_qr_only(
        self, content: LabelContent, width_px: int, height_px: int
    ) -> bytes:
        """Generate preview for QR-only template."""
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        title_font, body_font, small_font, _ = self._get_fonts()

        # QR code - larger for QR-only template
        qr_service = QRGeneratorService()
        qr_size = int(min(width_px, height_px) * 0.7)
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        if width_px > height_px * 1.3:  # Wide label
            qr_x = 10
            qr_y = (height_px - qr_size) // 2
            img.paste(qr_img, (qr_x, qr_y))

            text_x = qr_x + qr_size + 10
            draw.text((text_x, 15), content.container_name, fill="black", font=title_font)
            draw.text((text_x, 35), content.location_name, fill="gray", font=body_font)
        else:  # Square/tall label
            qr_x = (width_px - qr_size) // 2
            qr_y = 10
            img.paste(qr_img, (qr_x, qr_y))

            text_y = qr_y + qr_size + 5
            draw.text((10, text_y), content.container_name, fill="black", font=body_font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _preview_ai_summary(
        self, content: LabelContent, width_px: int, height_px: int
    ) -> bytes:
        """Generate preview for QR + AI summary template."""
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        title_font, body_font, small_font, _ = self._get_fonts()

        # QR code on left
        qr_service = QRGeneratorService()
        qr_size = int(min(width_px * 0.4, height_px - 20))
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        qr_x = 10
        qr_y = 10
        img.paste(qr_img, (qr_x, qr_y))

        # Text on right
        text_x = qr_x + qr_size + 10
        text_y = 10

        draw.text((text_x, text_y), content.container_name, fill="black", font=title_font)
        text_y += 18

        draw.text((text_x, text_y), content.location_name, fill="gray", font=body_font)
        text_y += 16

        # AI Summary
        summary_text = content.ai_summary or ""
        if not summary_text and content.item_count > 0:
            summary_text = f"{content.item_count} items"

        if summary_text:
            max_width = width_px - text_x - 10
            wrapped = self._wrap_text(summary_text, small_font, max_width, draw)
            for line in wrapped[:3]:
                draw.text((text_x, text_y), line, fill="gray", font=small_font)
                text_y += 12

        # QR code at bottom
        draw.text(
            (text_x, height_px - 15),
            content.container_qr_code,
            fill="gray",
            font=small_font,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _preview_full_contents(
        self, content: LabelContent, width_px: int, height_px: int
    ) -> bytes:
        """Generate preview for QR + full contents template."""
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        title_font, body_font, small_font, tiny_font = self._get_fonts()

        # QR code - smaller to leave room for contents
        qr_service = QRGeneratorService()
        qr_size = int(min(width_px * 0.35, height_px * 0.4))
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        qr_x = 10
        qr_y = 10
        img.paste(qr_img, (qr_x, qr_y))

        # Header text to the right of QR
        text_x = qr_x + qr_size + 10
        draw.text((text_x, 10), content.container_name, fill="black", font=title_font)
        draw.text((text_x, 28), content.location_name, fill="gray", font=body_font)

        # Contents list below QR
        contents_y = qr_y + qr_size + 10
        line_height = 11

        if content.full_contents:
            draw.text((qr_x, contents_y), "Contents:", fill="black", font=small_font)
            contents_y += line_height + 2

            available_height = height_px - contents_y - 20
            max_items = available_height // line_height

            items_to_show = content.full_contents[:max_items]
            remaining = len(content.full_contents) - len(items_to_show)

            for item in items_to_show:
                display_name = item[:30] + "..." if len(item) > 30 else item
                draw.text(
                    (qr_x, contents_y), f"• {display_name}", fill="gray", font=tiny_font
                )
                contents_y += line_height

            if remaining > 0:
                draw.text(
                    (qr_x, contents_y),
                    f"... +{remaining} more",
                    fill="gray",
                    font=tiny_font,
                )

        elif content.item_count > 0:
            draw.text(
                (qr_x, contents_y),
                f"{content.item_count} items",
                fill="gray",
                font=small_font,
            )

        # QR code value at bottom
        draw.text(
            (text_x, height_px - 15),
            content.container_qr_code,
            fill="gray",
            font=tiny_font,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _preview_legacy(
        self, content: LabelContent, width_px: int, height_px: int
    ) -> bytes:
        """Generate preview using legacy format."""
        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        title_font, body_font, small_font, _ = self._get_fonts()

        # QR code
        qr_service = QRGeneratorService()
        qr_size = min(width_px, height_px) - 20
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        qr_x = 10
        qr_y = (height_px - qr_size) // 2
        img.paste(qr_img, (qr_x, qr_y))

        text_x = qr_x + qr_size + 15
        text_y = 15

        draw.text((text_x, text_y), content.container_name, fill="black", font=title_font)
        text_y += 20

        draw.text((text_x, text_y), content.location_name, fill="gray", font=body_font)
        text_y += 18

        if content.contents_summary:
            max_width = width_px - text_x - 10
            wrapped = self._wrap_text(content.contents_summary, small_font, max_width, draw)
            for line in wrapped[:2]:
                draw.text((text_x, text_y), line, fill="gray", font=small_font)
                text_y += 12

        draw.text(
            (text_x, height_px - 20),
            content.container_qr_code,
            fill="gray",
            font=small_font,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def _generate_zpl(self, content: LabelContent) -> str:
        """Generate ZPL commands for the label based on template type."""
        width_dots = self._mm_to_dots(self.label_width_mm, self.dpi)
        height_dots = self._mm_to_dots(self.label_height_mm, self.dpi)

        # Route to appropriate template renderer
        if content.template == LabelTemplate.QR_ONLY:
            return self._generate_zpl_qr_only(content, width_dots, height_dots)
        elif content.template == LabelTemplate.QR_AI_SUMMARY:
            return self._generate_zpl_ai_summary(content, width_dots, height_dots)
        elif content.template == LabelTemplate.QR_FULL_CONTENTS:
            return self._generate_zpl_full_contents(content, width_dots, height_dots)
        else:
            # Legacy fallback
            return self._generate_zpl_legacy(content, width_dots, height_dots)

    def _generate_zpl_qr_only(
        self, content: LabelContent, width_dots: int, height_dots: int
    ) -> str:
        """Generate ZPL for QR-only template (compact label)."""
        # QR code takes up most of the space
        qr_mag = max(3, min(6, height_dots // 50))  # Scale QR based on label size

        zpl_lines = [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            "^PON",
            "^LH0,0",
        ]

        # QR Code centered or left-aligned depending on label shape
        qr_url = f"http://storagehub/c/{content.container_qr_code}"
        qr_x = 15
        qr_y = 15

        zpl_lines.extend([
            f"^FO{qr_x},{qr_y}",
            f"^BQN,2,{qr_mag}",
            f"^FDMA,{qr_url}^FS",
        ])

        # Container name - position depends on label orientation
        # For wide labels: text to the right of QR
        # For tall labels: text below QR
        qr_size_approx = qr_mag * 25  # Approximate QR size

        if width_dots > height_dots * 1.3:  # Wide label
            text_x = qr_x + qr_size_approx + 20
            zpl_lines.extend([
                f"^FO{text_x},20",
                "^A0N,28,28",
                f"^FD{content.container_name}^FS",
                f"^FO{text_x},52",
                "^A0N,20,20",
                f"^FD{content.location_name}^FS",
            ])
        else:  # Square or tall label
            text_y = qr_y + qr_size_approx + 10
            zpl_lines.extend([
                f"^FO{qr_x},{text_y}",
                "^A0N,22,22",
                f"^FD{content.container_name}^FS",
            ])

        zpl_lines.append("^XZ")
        return "\n".join(zpl_lines)

    def _generate_zpl_ai_summary(
        self, content: LabelContent, width_dots: int, height_dots: int
    ) -> str:
        """Generate ZPL for QR + AI summary template (medium label)."""
        qr_mag = max(3, min(5, height_dots // 60))
        qr_size_approx = qr_mag * 25

        zpl_lines = [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            "^PON",
            "^LH0,0",
        ]

        # QR Code on left
        qr_url = f"http://storagehub/c/{content.container_qr_code}"
        qr_x = 15
        qr_y = 15

        zpl_lines.extend([
            f"^FO{qr_x},{qr_y}",
            f"^BQN,2,{qr_mag}",
            f"^FDMA,{qr_url}^FS",
        ])

        # Text area to the right of QR
        text_x = qr_x + qr_size_approx + 25
        text_width = width_dots - text_x - 10

        # Container name
        zpl_lines.extend([
            f"^FO{text_x},15",
            "^A0N,28,28",
            f"^FD{content.container_name}^FS",
        ])

        # Location
        zpl_lines.extend([
            f"^FO{text_x},48",
            "^A0N,20,20",
            f"^FD{content.location_name}^FS",
        ])

        # AI Summary or item count
        summary_text = content.ai_summary or ""
        if not summary_text and content.item_count > 0:
            summary_text = f"{content.item_count} items"

        if summary_text:
            # Truncate to fit available width (roughly)
            max_chars = max(20, text_width // 10)
            if len(summary_text) > max_chars:
                summary_text = summary_text[:max_chars - 3] + "..."

            zpl_lines.extend([
                f"^FO{text_x},75",
                "^A0N,18,18",
                f"^FD{summary_text}^FS",
            ])

        # QR code value at bottom
        zpl_lines.extend([
            f"^FO{text_x},{height_dots - 25}",
            "^A0N,14,14",
            f"^FD{content.container_qr_code}^FS",
        ])

        zpl_lines.append("^XZ")
        return "\n".join(zpl_lines)

    def _generate_zpl_full_contents(
        self, content: LabelContent, width_dots: int, height_dots: int
    ) -> str:
        """Generate ZPL for QR + full contents template (large label)."""
        qr_mag = max(3, min(4, height_dots // 80))
        qr_size_approx = qr_mag * 25

        zpl_lines = [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            "^PON",
            "^LH0,0",
        ]

        # QR Code on left
        qr_url = f"http://storagehub/c/{content.container_qr_code}"
        qr_x = 15
        qr_y = 15

        zpl_lines.extend([
            f"^FO{qr_x},{qr_y}",
            f"^BQN,2,{qr_mag}",
            f"^FDMA,{qr_url}^FS",
        ])

        # Header area to the right of QR
        text_x = qr_x + qr_size_approx + 25

        # Container name
        zpl_lines.extend([
            f"^FO{text_x},15",
            "^A0N,26,26",
            f"^FD{content.container_name}^FS",
        ])

        # Location
        zpl_lines.extend([
            f"^FO{text_x},45",
            "^A0N,18,18",
            f"^FD{content.location_name}^FS",
        ])

        # Contents list below the QR code
        contents_y = max(qr_y + qr_size_approx + 15, 75)
        line_height = 18

        if content.full_contents:
            zpl_lines.extend([
                f"^FO{qr_x},{contents_y}",
                "^A0N,16,16",
                "^FDContents:^FS",
            ])
            contents_y += line_height

            # Calculate how many items we can fit
            available_height = height_dots - contents_y - 30
            max_items = available_height // line_height

            items_to_show = content.full_contents[:max_items]
            remaining = len(content.full_contents) - len(items_to_show)

            for item in items_to_show:
                # Truncate long item names
                display_name = item[:35] if len(item) > 35 else item
                zpl_lines.extend([
                    f"^FO{qr_x},{contents_y}",
                    "^A0N,14,14",
                    f"^FD- {display_name}^FS",
                ])
                contents_y += line_height - 2

            if remaining > 0:
                zpl_lines.extend([
                    f"^FO{qr_x},{contents_y}",
                    "^A0N,14,14",
                    f"^FD... +{remaining} more^FS",
                ])

        elif content.item_count > 0:
            zpl_lines.extend([
                f"^FO{qr_x},{contents_y}",
                "^A0N,16,16",
                f"^FD{content.item_count} items^FS",
            ])

        # QR code value at bottom right
        zpl_lines.extend([
            f"^FO{text_x},{height_dots - 25}",
            "^A0N,12,12",
            f"^FD{content.container_qr_code}^FS",
        ])

        zpl_lines.append("^XZ")
        return "\n".join(zpl_lines)

    def _generate_zpl_legacy(
        self, content: LabelContent, width_dots: int, height_dots: int
    ) -> str:
        """Generate ZPL using legacy format (backward compatibility)."""
        # QR code size (about 40% of label height)
        qr_size = int(height_dots * 0.4)

        # Calculate positions
        qr_x = 20
        qr_y = (height_dots - qr_size) // 2
        text_x = qr_x + qr_size + 30

        zpl_lines = [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            "^PON",
            "^LH0,0",
        ]

        # QR Code
        qr_url = f"http://storagehub/c/{content.container_qr_code}"
        zpl_lines.extend([
            f"^FO{qr_x},{qr_y}",
            "^BQN,2,4",
            f"^FDMA,{qr_url}^FS",
        ])

        # Container name
        zpl_lines.extend([
            f"^FO{text_x},20",
            "^A0N,30,30",
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

        zpl_lines.append("^XZ")
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
