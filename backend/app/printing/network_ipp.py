"""Network printer driver using IPP (Internet Printing Protocol).

Supports most modern network printers including Epson, HP, Canon, Brother, etc.
Uses the pycups library for CUPS integration on Linux.
"""

import asyncio
import io
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, gray
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from app.printing.base import BaseDriver, ItemDetail, LabelContent, LabelTemplate
from app.services.qr_generator import QRGeneratorService


class NetworkIPPDriver(BaseDriver):
    """Driver for network printers using IPP/CUPS.

    Supports printing via:
    1. Direct IPP (ipp://printer-ip/ipp/print)
    2. CUPS queue name
    3. Network hostname/IP

    Compatible with most network printers including Epson ET-2750, HP, Canon, etc.
    """

    def __init__(
        self,
        address: str,
        label_width_mm: float = 210,  # A4 width
        label_height_mm: float = 297,  # A4 height
    ):
        super().__init__(address, label_width_mm, label_height_mm)
        self.printer_address = address
        # Check if address is IPP URL, CUPS queue, or IP
        self.is_ipp_url = address.startswith("ipp://") or address.startswith("ipps://")
        self.is_cups_queue = not self.is_ipp_url and not self._looks_like_ip(address)

    def _looks_like_ip(self, addr: str) -> bool:
        """Check if address looks like an IP or hostname."""
        # Remove port if present
        addr = addr.split(":")[0]
        parts = addr.split(".")
        if len(parts) == 4:
            try:
                return all(0 <= int(p) <= 255 for p in parts)
            except ValueError:
                pass
        return False

    async def test_connection(self) -> bool:
        """Test connection to the network printer."""
        try:
            if self.is_cups_queue:
                # Check if CUPS queue exists
                result = await asyncio.create_subprocess_exec(
                    "lpstat", "-p", self.printer_address,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, _ = await result.communicate()
                return result.returncode == 0
            elif self.is_ipp_url:
                # Try to query printer status via ipptool if available
                result = await asyncio.create_subprocess_exec(
                    "ipptool", "-t", self.printer_address, "-d", "get-printer-attributes",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, _ = await result.communicate()
                return result.returncode == 0
            else:
                # Try ping for IP/hostname
                result = await asyncio.create_subprocess_exec(
                    "ping", "-c", "1", "-W", "2", self.printer_address.split(":")[0],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, _ = await result.communicate()
                return result.returncode == 0
        except FileNotFoundError:
            # Command not found, assume printer is available
            return True
        except Exception:
            return False

    async def print_label(self, content: LabelContent) -> bool:
        """Print a label/document to the network printer."""
        try:
            # Generate PDF based on template
            if content.template == LabelTemplate.A4_FULL_DETAILS:
                pdf_bytes = await self._generate_a4_full_details_pdf(content)
            else:
                pdf_bytes = await self._generate_standard_pdf(content)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            try:
                # Print using lp command (works with CUPS)
                cmd = ["lp"]

                if self.is_cups_queue:
                    cmd.extend(["-d", self.printer_address])
                elif self.is_ipp_url:
                    cmd.extend(["-h", self.printer_address.replace("ipp://", "").replace("ipps://", "")])
                else:
                    # Assume CUPS can route via IP
                    cmd.extend(["-h", self.printer_address])

                cmd.append(tmp_path)

                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                return result.returncode == 0
            finally:
                # Cleanup
                Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            print(f"Print error: {e}")
            return False

    async def generate_preview(self, content: LabelContent) -> bytes:
        """Generate a preview image of the document."""
        if content.template == LabelTemplate.A4_FULL_DETAILS:
            pdf_bytes = await self._generate_a4_full_details_pdf(content)
        else:
            pdf_bytes = await self._generate_standard_pdf(content)

        # Convert PDF to PNG for preview
        return await self._pdf_to_png(pdf_bytes)

    async def _pdf_to_png(self, pdf_bytes: bytes) -> bytes:
        """Convert PDF to PNG image for preview."""
        try:
            # Try using pdf2image if available
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=150, first_page=1, last_page=1)
            if images:
                buffer = io.BytesIO()
                images[0].save(buffer, format="PNG")
                return buffer.getvalue()
        except ImportError:
            pass

        # Fallback: Generate a simple preview image
        width_px = int(self.label_width_mm * 96 / 25.4)
        height_px = int(self.label_height_mm * 96 / 25.4)

        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except OSError:
            font = ImageFont.load_default()

        draw.text((20, 20), "PDF Preview", fill="black", font=font)
        draw.text((20, 50), f"Container: {content.container_name}", fill="black", font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    async def _generate_standard_pdf(self, content: LabelContent) -> bytes:
        """Generate a standard label PDF."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        page_width, page_height = A4
        qr_service = QRGeneratorService()

        # Generate QR code
        qr_size = 150
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Position QR code at top left
        c.drawImage(qr_buffer, 30 * mm, page_height - 60 * mm, width=50 * mm, height=50 * mm)

        # Text next to QR
        text_x = 90 * mm
        text_y = page_height - 25 * mm

        c.setFont("Helvetica-Bold", 18)
        c.drawString(text_x, text_y, content.container_name)

        c.setFont("Helvetica", 14)
        c.drawString(text_x, text_y - 8 * mm, content.location_name)

        c.setFont("Helvetica", 10)
        c.setFillGray(0.4)
        c.drawString(text_x, text_y - 16 * mm, content.container_qr_code)
        c.setFillGray(0)

        # AI Summary if available
        if content.ai_summary:
            c.setFont("Helvetica", 11)
            text_y = page_height - 70 * mm
            # Word wrap the summary
            words = content.ai_summary.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if c.stringWidth(test_line, "Helvetica", 11) < page_width - 60 * mm:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            for line in lines[:4]:  # Max 4 lines
                c.drawString(30 * mm, text_y, line)
                text_y -= 5 * mm

        c.save()
        return buffer.getvalue()

    async def _generate_a4_full_details_pdf(self, content: LabelContent) -> bytes:
        """Generate a full A4 page with QR, summary, and item table with thumbnails."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        page_width, page_height = A4
        margin = 15 * mm
        qr_service = QRGeneratorService()

        # Load fonts
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            # Use system fonts if available
        except:
            pass

        # ========== Header Section ==========
        header_y = page_height - margin

        # Generate QR code
        qr_size = 200
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Draw QR code at top left
        qr_display_size = 45 * mm
        c.drawImage(qr_buffer, margin, header_y - qr_display_size,
                   width=qr_display_size, height=qr_display_size)

        # Container name and location
        text_x = margin + qr_display_size + 10 * mm
        text_y = header_y - 10 * mm

        c.setFont("Helvetica-Bold", 24)
        c.drawString(text_x, text_y, content.container_name)

        c.setFont("Helvetica", 16)
        c.setFillGray(0.3)
        c.drawString(text_x, text_y - 10 * mm, content.location_name)

        c.setFont("Helvetica", 11)
        c.setFillGray(0.5)
        c.drawString(text_x, text_y - 20 * mm, f"QR: {content.container_qr_code}")
        c.drawString(text_x, text_y - 27 * mm, f"Items: {content.item_count}")
        c.setFillGray(0)

        # ========== AI Summary Section ==========
        summary_y = header_y - qr_display_size - 10 * mm

        if content.ai_summary:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, summary_y, "Summary")
            summary_y -= 6 * mm

            c.setFont("Helvetica", 11)
            c.setFillGray(0.2)

            # Word wrap the summary
            words = content.ai_summary.split()
            lines = []
            current_line = ""
            max_width = page_width - 2 * margin

            for word in words:
                test_line = f"{current_line} {word}".strip()
                if c.stringWidth(test_line, "Helvetica", 11) < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            for line in lines[:5]:  # Max 5 lines
                c.drawString(margin, summary_y, line)
                summary_y -= 5 * mm

            c.setFillGray(0)
            summary_y -= 5 * mm

        # ========== Items Table Section ==========
        table_y = summary_y - 5 * mm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, table_y, "Contents")
        table_y -= 8 * mm

        # Draw table header
        col_widths = [20 * mm, 55 * mm, 40 * mm, 25 * mm, 35 * mm]  # Image, Name, Description, Size, Owner
        headers = ["", "Item", "Description", "Size", "Owner"]

        # Header background
        c.setFillColor(HexColor("#f0f0f0"))
        c.rect(margin, table_y - 6 * mm, sum(col_widths), 8 * mm, fill=True, stroke=False)
        c.setFillColor(black)

        # Header text
        c.setFont("Helvetica-Bold", 9)
        x = margin
        for i, header in enumerate(headers):
            c.drawString(x + 2 * mm, table_y - 4 * mm, header)
            x += col_widths[i]

        # Header line
        c.setStrokeGray(0.7)
        c.line(margin, table_y - 6 * mm, margin + sum(col_widths), table_y - 6 * mm)

        table_y -= 8 * mm
        row_height = 18 * mm  # Height for each row (to accommodate thumbnails)

        # Draw item rows
        c.setFont("Helvetica", 9)

        for i, item in enumerate(content.item_details):
            if table_y < margin + 20 * mm:
                # Start new page if running out of space
                remaining = len(content.item_details) - i
                c.setFont("Helvetica-Oblique", 9)
                c.setFillGray(0.5)
                c.drawString(margin, table_y, f"... and {remaining} more items")
                break

            x = margin
            row_y = table_y

            # Alternating row background
            if i % 2 == 1:
                c.setFillColor(HexColor("#fafafa"))
                c.rect(margin, row_y - row_height + 2 * mm, sum(col_widths), row_height, fill=True, stroke=False)
                c.setFillColor(black)

            # Thumbnail
            if item.thumbnail_path and os.path.exists(item.thumbnail_path):
                try:
                    thumb_size = 15 * mm
                    # Load image and convert to ImageReader for ReportLab
                    thumb_img = Image.open(item.thumbnail_path)
                    thumb_buffer = io.BytesIO()
                    thumb_img.save(thumb_buffer, format="PNG")
                    thumb_buffer.seek(0)
                    c.drawImage(ImageReader(thumb_buffer), x + 2 * mm, row_y - thumb_size,
                               width=thumb_size, height=thumb_size, preserveAspectRatio=True)
                except Exception:
                    pass
            x += col_widths[0]

            # Item name
            c.setFont("Helvetica-Bold", 9)
            name = item.name[:30] + "..." if len(item.name) > 30 else item.name
            c.drawString(x + 2 * mm, row_y - 5 * mm, name)
            x += col_widths[1]

            # Description
            c.setFont("Helvetica", 8)
            c.setFillGray(0.3)
            if item.description:
                desc = item.description[:25] + "..." if len(item.description) > 25 else item.description
                c.drawString(x + 2 * mm, row_y - 5 * mm, desc)
            x += col_widths[2]

            # Size
            if item.size:
                c.drawString(x + 2 * mm, row_y - 5 * mm, item.size[:15])
            x += col_widths[3]

            # Owner
            c.setFillGray(0.2)
            if item.owner_name:
                owner = item.owner_name[:20] + "..." if len(item.owner_name) > 20 else item.owner_name
                c.drawString(x + 2 * mm, row_y - 5 * mm, owner)
            c.setFillGray(0)

            # Row separator line
            c.setStrokeGray(0.85)
            c.line(margin, row_y - row_height + 2 * mm, margin + sum(col_widths), row_y - row_height + 2 * mm)

            table_y -= row_height

        # ========== Footer ==========
        c.setFont("Helvetica", 8)
        c.setFillGray(0.5)
        c.drawString(margin, margin, f"Generated by StorageHub - {content.container_qr_code}")
        c.drawRightString(page_width - margin, margin, f"Page 1 of 1")

        c.save()
        return buffer.getvalue()
