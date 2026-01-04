"""PDF label generator for generic printers."""

import io
import os
from dataclasses import dataclass

from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.printing.base import BaseDriver, LabelContent, LabelTemplate
from app.services.qr_generator import QRGeneratorService


@dataclass
class LabelLayout:
    """Layout configuration for labels on a page."""

    name: str
    page_size: tuple[float, float]
    label_width: float  # mm
    label_height: float  # mm
    columns: int
    rows: int
    margin_left: float  # mm
    margin_top: float  # mm
    spacing_x: float  # mm
    spacing_y: float  # mm


# Common label layouts (Avery-style)
LAYOUTS = {
    "avery_5160": LabelLayout(
        name="Avery 5160 (30 labels)",
        page_size=letter,
        label_width=66.7,
        label_height=25.4,
        columns=3,
        rows=10,
        margin_left=4.8,
        margin_top=12.7,
        spacing_x=3.2,
        spacing_y=0,
    ),
    "avery_5163": LabelLayout(
        name="Avery 5163 (10 labels)",
        page_size=letter,
        label_width=101.6,
        label_height=50.8,
        columns=2,
        rows=5,
        margin_left=4.8,
        margin_top=12.7,
        spacing_x=3.2,
        spacing_y=0,
    ),
    "avery_l7163": LabelLayout(
        name="Avery L7163 (14 labels)",
        page_size=A4,
        label_width=99.1,
        label_height=38.1,
        columns=2,
        rows=7,
        margin_left=4.7,
        margin_top=15.2,
        spacing_x=2.5,
        spacing_y=0,
    ),
    "single": LabelLayout(
        name="Single Label",
        page_size=A4,
        label_width=100,
        label_height=50,
        columns=1,
        rows=1,
        margin_left=55,
        margin_top=120,
        spacing_x=0,
        spacing_y=0,
    ),
}


class PDFLabelDriver(BaseDriver):
    """Driver that generates PDF files with labels."""

    def __init__(
        self,
        address: str,
        label_width_mm: float,
        label_height_mm: float,
        layout: str = "single",
    ):
        super().__init__(address, label_width_mm, label_height_mm)
        # Address is the output path or "download" for in-memory
        self.output_path = address if address != "download" else None
        self.layout = LAYOUTS.get(layout, LAYOUTS["single"])

    async def test_connection(self) -> bool:
        """PDF driver is always available."""
        return True

    async def print_label(self, content: LabelContent) -> bool:
        """Generate a PDF with the label."""
        try:
            pdf_bytes = await self.generate_pdf([content])

            if self.output_path:
                with open(self.output_path, "wb") as f:
                    f.write(pdf_bytes)

            return True
        except Exception:
            return False

    async def generate_preview(self, content: LabelContent) -> bytes:
        """Generate a preview image of a single label based on template."""
        # For A4 Full Details, generate the PDF and convert to PNG
        if content.template == LabelTemplate.A4_FULL_DETAILS:
            return await self._generate_a4_preview(content)

        # Create a label image similar to other drivers
        width_px = int(self.label_width_mm * 96 / 25.4)
        height_px = int(self.label_height_mm * 96 / 25.4)

        from PIL import ImageDraw, ImageFont

        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)

        # Border
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        # Load fonts
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

        qr_service = QRGeneratorService()

        # Render based on template
        if content.template == LabelTemplate.QR_ONLY:
            # QR code larger for QR-only template
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
            else:
                qr_x = (width_px - qr_size) // 2
                qr_y = 10
                img.paste(qr_img, (qr_x, qr_y))
                text_y = qr_y + qr_size + 5
                draw.text((10, text_y), content.container_name, fill="black", font=body_font)

        elif content.template == LabelTemplate.QR_AI_SUMMARY:
            # QR + AI summary
            qr_size = int(min(width_px * 0.4, height_px - 20))
            qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
            qr_img = Image.open(io.BytesIO(qr_bytes))

            qr_x = 10
            qr_y = 10
            img.paste(qr_img, (qr_x, qr_y))

            text_x = qr_x + qr_size + 10
            text_y = 10
            draw.text((text_x, text_y), content.container_name, fill="black", font=title_font)
            text_y += 18
            draw.text((text_x, text_y), content.location_name, fill="gray", font=body_font)
            text_y += 16

            summary_text = content.ai_summary or ""
            if not summary_text and content.item_count > 0:
                summary_text = f"{content.item_count} items"
            if summary_text:
                draw.text((text_x, text_y), summary_text[:40], fill="gray", font=small_font)

            draw.text((text_x, height_px - 15), content.container_qr_code, fill="gray", font=small_font)

        elif content.template == LabelTemplate.QR_FULL_CONTENTS:
            # QR + full contents list
            qr_size = int(min(width_px * 0.35, height_px * 0.4))
            qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
            qr_img = Image.open(io.BytesIO(qr_bytes))

            qr_x = 10
            qr_y = 10
            img.paste(qr_img, (qr_x, qr_y))

            text_x = qr_x + qr_size + 10
            draw.text((text_x, 10), content.container_name, fill="black", font=title_font)
            draw.text((text_x, 28), content.location_name, fill="gray", font=body_font)

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
                    draw.text((qr_x, contents_y), f"• {display_name}", fill="gray", font=tiny_font)
                    contents_y += line_height

                if remaining > 0:
                    draw.text((qr_x, contents_y), f"... +{remaining} more", fill="gray", font=tiny_font)

            elif content.item_count > 0:
                draw.text((qr_x, contents_y), f"{content.item_count} items", fill="gray", font=small_font)

            draw.text((text_x, height_px - 15), content.container_qr_code, fill="gray", font=tiny_font)

        else:
            # Legacy format
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
                draw.text((text_x, text_y), content.contents_summary[:30], fill="gray", font=small_font)

            draw.text((text_x, height_px - 20), content.container_qr_code, fill="gray", font=small_font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    async def generate_pdf(self, labels: list[LabelContent]) -> bytes:
        """Generate a PDF with multiple labels based on template type."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=self.layout.page_size)

        qr_service = QRGeneratorService()
        labels_per_page = self.layout.columns * self.layout.rows
        page_width, page_height = self.layout.page_size

        for i, content in enumerate(labels):
            # Calculate position on page
            page_index = i % labels_per_page
            col = page_index % self.layout.columns
            row = page_index // self.layout.columns

            # Calculate x, y position (PDF coordinates from bottom-left)
            x = (
                self.layout.margin_left
                + col * (self.layout.label_width + self.layout.spacing_x)
            ) * mm
            y = page_height - (
                self.layout.margin_top
                + row * (self.layout.label_height + self.layout.spacing_y)
                + self.layout.label_height
            ) * mm

            label_w = self.layout.label_width * mm
            label_h = self.layout.label_height * mm

            # Render based on template
            if content.template == LabelTemplate.A4_FULL_DETAILS:
                # A4 Full Details gets its own full page
                self._draw_pdf_a4_full_details(c, qr_service, content)
            elif content.template == LabelTemplate.QR_ONLY:
                self._draw_pdf_qr_only(c, qr_service, content, x, y, label_w, label_h)
            elif content.template == LabelTemplate.QR_AI_SUMMARY:
                self._draw_pdf_ai_summary(c, qr_service, content, x, y, label_w, label_h)
            elif content.template == LabelTemplate.QR_FULL_CONTENTS:
                self._draw_pdf_full_contents(c, qr_service, content, x, y, label_w, label_h)
            else:
                self._draw_pdf_legacy(c, qr_service, content, x, y, label_w, label_h)

            # New page if needed
            if (i + 1) % labels_per_page == 0 and i + 1 < len(labels):
                c.showPage()

        c.save()
        return buffer.getvalue()

    async def generate_batch_pdf(
        self, labels: list[LabelContent], layout: str = "avery_5160"
    ) -> bytes:
        """Generate a PDF with labels in a specific layout."""
        self.layout = LAYOUTS.get(layout, self.layout)
        return await self.generate_pdf(labels)

    def _get_qr_buffer(
        self, qr_service: QRGeneratorService, qr_code: str, size: int
    ) -> ImageReader:
        """Generate QR code and return as ImageReader for ReportLab."""
        qr_bytes = qr_service.generate_container_qr(qr_code, size)
        qr_img = Image.open(io.BytesIO(qr_bytes))
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        return ImageReader(qr_buffer)

    def _draw_pdf_qr_only(
        self,
        c: canvas.Canvas,
        qr_service: QRGeneratorService,
        content: LabelContent,
        x: float,
        y: float,
        label_w: float,
        label_h: float,
    ) -> None:
        """Draw QR-only template to PDF."""
        # Larger QR code for this template
        qr_size_mm = min(label_w, label_h) * 0.75 / mm
        qr_buffer = self._get_qr_buffer(qr_service, content.container_qr_code, int(qr_size_mm * 10))

        if label_w > label_h * 1.3:  # Wide label
            qr_x = x + 2 * mm
            qr_y = y + (label_h - qr_size_mm * mm) / 2
            c.drawImage(qr_buffer, qr_x, qr_y, width=qr_size_mm * mm, height=qr_size_mm * mm)

            text_x = qr_x + qr_size_mm * mm + 3 * mm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(text_x, y + label_h - 6 * mm, content.container_name[:20])
            c.setFont("Helvetica", 8)
            c.drawString(text_x, y + label_h - 10 * mm, content.location_name[:25])
        else:  # Square/tall label
            qr_x = x + (label_w - qr_size_mm * mm) / 2
            qr_y = y + label_h - qr_size_mm * mm - 2 * mm
            c.drawImage(qr_buffer, qr_x, qr_y, width=qr_size_mm * mm, height=qr_size_mm * mm)

            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + 2 * mm, y + 3 * mm, content.container_name[:20])

    def _draw_pdf_ai_summary(
        self,
        c: canvas.Canvas,
        qr_service: QRGeneratorService,
        content: LabelContent,
        x: float,
        y: float,
        label_w: float,
        label_h: float,
    ) -> None:
        """Draw QR + AI summary template to PDF."""
        qr_size_mm = min(label_w * 0.4, label_h - 4 * mm) / mm
        qr_buffer = self._get_qr_buffer(qr_service, content.container_qr_code, int(qr_size_mm * 10))

        qr_x = x + 2 * mm
        qr_y = y + (label_h - qr_size_mm * mm) / 2
        c.drawImage(qr_buffer, qr_x, qr_y, width=qr_size_mm * mm, height=qr_size_mm * mm)

        text_x = qr_x + qr_size_mm * mm + 3 * mm

        # Container name
        c.setFont("Helvetica-Bold", 10)
        c.drawString(text_x, y + label_h - 5 * mm, content.container_name[:25])

        # Location
        c.setFont("Helvetica", 8)
        c.drawString(text_x, y + label_h - 9 * mm, content.location_name[:30])

        # AI Summary or item count
        summary_text = content.ai_summary or ""
        if not summary_text and content.item_count > 0:
            summary_text = f"{content.item_count} items"

        if summary_text:
            c.setFont("Helvetica", 7)
            c.drawString(text_x, y + label_h - 13 * mm, summary_text[:40])

        # QR code value
        c.setFont("Helvetica", 6)
        c.setFillGray(0.5)
        c.drawString(text_x, y + 2 * mm, content.container_qr_code)
        c.setFillGray(0)

    def _draw_pdf_full_contents(
        self,
        c: canvas.Canvas,
        qr_service: QRGeneratorService,
        content: LabelContent,
        x: float,
        y: float,
        label_w: float,
        label_h: float,
    ) -> None:
        """Draw QR + full contents template to PDF."""
        qr_size_mm = min(label_w * 0.35, label_h * 0.4) / mm
        qr_buffer = self._get_qr_buffer(qr_service, content.container_qr_code, int(qr_size_mm * 10))

        qr_x = x + 2 * mm
        qr_y = y + label_h - qr_size_mm * mm - 2 * mm
        c.drawImage(qr_buffer, qr_x, qr_y, width=qr_size_mm * mm, height=qr_size_mm * mm)

        # Header text to the right of QR
        text_x = qr_x + qr_size_mm * mm + 3 * mm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(text_x, y + label_h - 5 * mm, content.container_name[:25])
        c.setFont("Helvetica", 7)
        c.drawString(text_x, y + label_h - 9 * mm, content.location_name[:30])

        # Contents list below QR
        contents_y = qr_y - 3 * mm
        line_height = 2.5 * mm

        if content.full_contents:
            c.setFont("Helvetica-Bold", 6)
            c.drawString(qr_x, contents_y, "Contents:")
            contents_y -= line_height

            available_height = contents_y - y - 3 * mm
            max_items = int(available_height / line_height)

            items_to_show = content.full_contents[:max_items]
            remaining = len(content.full_contents) - len(items_to_show)

            c.setFont("Helvetica", 6)
            c.setFillGray(0.3)
            for item in items_to_show:
                display_name = item[:35] if len(item) <= 35 else item[:32] + "..."
                c.drawString(qr_x, contents_y, f"• {display_name}")
                contents_y -= line_height

            if remaining > 0:
                c.drawString(qr_x, contents_y, f"... +{remaining} more")

            c.setFillGray(0)

        elif content.item_count > 0:
            c.setFont("Helvetica", 7)
            c.drawString(qr_x, contents_y, f"{content.item_count} items")

        # QR code value at bottom
        c.setFont("Helvetica", 5)
        c.setFillGray(0.5)
        c.drawString(text_x, y + 2 * mm, content.container_qr_code)
        c.setFillGray(0)

    def _draw_pdf_legacy(
        self,
        c: canvas.Canvas,
        qr_service: QRGeneratorService,
        content: LabelContent,
        x: float,
        y: float,
        label_w: float,
        label_h: float,
    ) -> None:
        """Draw legacy format label to PDF."""
        qr_size_mm = min(label_w, label_h) * 0.7 / mm
        qr_buffer = self._get_qr_buffer(qr_service, content.container_qr_code, int(qr_size_mm * 10))

        qr_x = x + 2 * mm
        qr_y = y + (label_h - qr_size_mm * mm) / 2
        c.drawImage(qr_buffer, qr_x, qr_y, width=qr_size_mm * mm, height=qr_size_mm * mm)

        text_x = qr_x + qr_size_mm * mm + 3 * mm
        text_y = y + label_h - 5 * mm

        c.setFont("Helvetica-Bold", 10)
        c.drawString(text_x, text_y, content.container_name[:25])
        text_y -= 4 * mm

        c.setFont("Helvetica", 8)
        c.drawString(text_x, text_y, content.location_name[:30])
        text_y -= 3.5 * mm

        if content.contents_summary:
            c.setFont("Helvetica", 7)
            c.drawString(text_x, text_y, content.contents_summary[:35])

        c.setFont("Helvetica", 6)
        c.setFillGray(0.5)
        c.drawString(text_x, y + 2 * mm, content.container_qr_code)
        c.setFillGray(0)

    async def _generate_a4_preview(self, content: LabelContent) -> bytes:
        """Generate an A4 preview image by rendering PDF and converting to PNG."""
        from PIL import ImageDraw, ImageFont

        # Generate the PDF first
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        qr_service = QRGeneratorService()
        self._draw_pdf_a4_full_details(c, qr_service, content)
        c.save()
        pdf_bytes = buffer.getvalue()

        # Try to convert PDF to PNG
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=100, first_page=1, last_page=1)
            if images:
                img_buffer = io.BytesIO()
                images[0].save(img_buffer, format="PNG")
                return img_buffer.getvalue()
        except ImportError:
            pass

        # Fallback: Generate a simple preview image
        width_px = int(210 * 96 / 25.4)  # A4 width in pixels at 96 dpi
        height_px = int(297 * 96 / 25.4)  # A4 height in pixels at 96 dpi

        img = Image.new("RGB", (width_px, height_px), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw QR code
        qr_size = 150
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))
        img.paste(qr_img, (20, 20))

        # Header text
        text_x = 190
        draw.text((text_x, 30), content.container_name, fill="black", font=title_font)
        draw.text((text_x, 55), content.location_name, fill="gray", font=body_font)
        draw.text((text_x, 75), f"Items: {content.item_count}", fill="gray", font=small_font)

        # AI Summary preview
        y = 200
        if content.ai_summary:
            draw.text((20, y), "Summary:", fill="black", font=body_font)
            y += 20
            summary = content.ai_summary[:100] + "..." if len(content.ai_summary) > 100 else content.ai_summary
            draw.text((20, y), summary, fill="gray", font=small_font)
            y += 40

        # Items table preview
        draw.text((20, y), "Contents:", fill="black", font=body_font)
        y += 25

        # Table header
        draw.rectangle([(20, y), (width_px - 20, y + 20)], fill="#f0f0f0")
        draw.text((30, y + 3), "Item", fill="black", font=small_font)
        draw.text((200, y + 3), "Description", fill="black", font=small_font)
        draw.text((400, y + 3), "Size", fill="black", font=small_font)
        draw.text((500, y + 3), "Owner", fill="black", font=small_font)
        y += 25

        # Item rows (show first few)
        for i, item in enumerate(content.item_details[:8]):
            name = item.name[:20] + "..." if len(item.name) > 20 else item.name
            desc = (item.description or "")[:15] + "..." if item.description and len(item.description) > 15 else (item.description or "")
            size = (item.size or "")[:10]
            owner = (item.owner_name or "")[:12]

            draw.text((30, y + 3), name, fill="black", font=small_font)
            draw.text((200, y + 3), desc, fill="gray", font=small_font)
            draw.text((400, y + 3), size, fill="gray", font=small_font)
            draw.text((500, y + 3), owner, fill="gray", font=small_font)
            draw.line([(20, y + 20), (width_px - 20, y + 20)], fill="#e0e0e0")
            y += 22

        if len(content.item_details) > 8:
            draw.text((30, y + 3), f"... and {len(content.item_details) - 8} more items", fill="gray", font=small_font)

        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        return img_buffer.getvalue()

    def _draw_pdf_a4_full_details(
        self,
        c: canvas.Canvas,
        qr_service: QRGeneratorService,
        content: LabelContent,
    ) -> None:
        """Draw A4 full details template with item table and thumbnails.

        Supports multiple pages when there are many items.
        """
        page_width, page_height = A4
        margin = 15 * mm
        col_widths = [20 * mm, 55 * mm, 40 * mm, 25 * mm, 35 * mm]  # Image, Name, Description, Size, Owner
        headers = ["", "Item", "Description", "Size", "Owner"]
        row_height = 18 * mm

        # Calculate total pages needed
        items_per_first_page = 8  # Approximate, depends on summary length
        items_per_continuation_page = 12
        total_items = len(content.item_details)

        if total_items <= items_per_first_page:
            total_pages = 1
        else:
            remaining = total_items - items_per_first_page
            total_pages = 1 + (remaining + items_per_continuation_page - 1) // items_per_continuation_page

        current_page = 1
        item_index = 0

        def draw_table_header(table_y: float) -> float:
            """Draw the table header and return new y position."""
            c.setFillColor(HexColor("#f0f0f0"))
            c.rect(margin, table_y - 6 * mm, sum(col_widths), 8 * mm, fill=True, stroke=False)
            c.setFillColor(black)

            c.setFont("Helvetica-Bold", 9)
            x = margin
            for i, header in enumerate(headers):
                c.drawString(x + 2 * mm, table_y - 4 * mm, header)
                x += col_widths[i]

            c.setStrokeGray(0.7)
            c.line(margin, table_y - 6 * mm, margin + sum(col_widths), table_y - 6 * mm)

            return table_y - 8 * mm

        def draw_item_row(item, row_y: float, row_index: int) -> None:
            """Draw a single item row."""
            x = margin

            # Alternating row background
            if row_index % 2 == 1:
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
            c.setFillGray(0)
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

        def draw_footer(page_num: int) -> None:
            """Draw page footer."""
            c.setFont("Helvetica", 8)
            c.setFillGray(0.5)
            c.drawString(margin, margin, f"Generated by StorageHub - {content.container_qr_code}")
            c.drawRightString(page_width - margin, margin, f"Page {page_num} of {total_pages}")
            c.setFillGray(0)

        # ========== First Page: Header + Summary + Items ==========
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
        c.drawImage(ImageReader(qr_buffer), margin, header_y - qr_display_size,
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

        # AI Summary Section
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

            for line in lines[:5]:
                c.drawString(margin, summary_y, line)
                summary_y -= 5 * mm

            c.setFillGray(0)
            summary_y -= 5 * mm

        # Items Table Section
        table_y = summary_y - 5 * mm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, table_y, "Contents")
        table_y -= 8 * mm

        table_y = draw_table_header(table_y)

        # Draw items on first page
        while item_index < total_items:
            if table_y < margin + 25 * mm:
                # Need to start a new page
                break

            draw_item_row(content.item_details[item_index], table_y, item_index)
            table_y -= row_height
            item_index += 1

        draw_footer(current_page)

        # ========== Continuation Pages ==========
        while item_index < total_items:
            c.showPage()
            current_page += 1

            # Start new page with just table
            table_y = page_height - margin - 10 * mm

            # Page title
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin, table_y, f"{content.container_name} - Contents (continued)")
            table_y -= 12 * mm

            table_y = draw_table_header(table_y)

            # Draw items on this page
            while item_index < total_items:
                if table_y < margin + 25 * mm:
                    break

                draw_item_row(content.item_details[item_index], table_y, item_index)
                table_y -= row_height
                item_index += 1

            draw_footer(current_page)
