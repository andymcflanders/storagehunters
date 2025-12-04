"""PDF label generator for generic printers."""

import io
from dataclasses import dataclass

from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.printing.base import BaseDriver, LabelContent
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
        """Generate a preview image of a single label."""
        # Create a label image similar to other drivers
        width_px = int(self.label_width_mm * 96 / 25.4)
        height_px = int(self.label_height_mm * 96 / 25.4)

        img = Image.new("RGB", (width_px, height_px), "white")
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(img)

        # Border
        draw.rectangle([(0, 0), (width_px - 1, height_px - 1)], outline="black")

        # QR code
        qr_service = QRGeneratorService()
        qr_size = min(width_px, height_px) - 20
        qr_bytes = qr_service.generate_container_qr(content.container_qr_code, qr_size)
        qr_img = Image.open(io.BytesIO(qr_bytes))

        qr_x = 10
        qr_y = (height_px - qr_size) // 2
        img.paste(qr_img, (qr_x, qr_y))

        # Text
        text_x = qr_x + qr_size + 15
        text_y = 15

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
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        draw.text((text_x, text_y), content.container_name, fill="black", font=title_font)
        text_y += 20
        draw.text((text_x, text_y), content.location_name, fill="gray", font=body_font)
        text_y += 18

        if content.contents_summary:
            draw.text(
                (text_x, text_y),
                content.contents_summary[:30],
                fill="gray",
                font=small_font,
            )

        draw.text(
            (text_x, height_px - 20),
            content.container_qr_code,
            fill="gray",
            font=small_font,
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    async def generate_pdf(self, labels: list[LabelContent]) -> bytes:
        """Generate a PDF with multiple labels."""
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

            # Draw label border (optional, for debugging)
            # c.rect(x, y, self.layout.label_width * mm, self.layout.label_height * mm)

            # Generate QR code
            qr_size_mm = min(self.layout.label_width, self.layout.label_height) * 0.7
            qr_bytes = qr_service.generate_container_qr(
                content.container_qr_code, int(qr_size_mm * 10)
            )
            qr_img = Image.open(io.BytesIO(qr_bytes))

            # Save QR to temp buffer for ReportLab
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)

            # Draw QR code
            qr_x = x + 2 * mm
            qr_y = y + (self.layout.label_height * mm - qr_size_mm * mm) / 2
            c.drawImage(
                qr_buffer,
                qr_x,
                qr_y,
                width=qr_size_mm * mm,
                height=qr_size_mm * mm,
            )

            # Draw text
            text_x = qr_x + qr_size_mm * mm + 3 * mm
            text_y = y + self.layout.label_height * mm - 5 * mm

            # Container name (bold)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(text_x, text_y, content.container_name[:25])
            text_y -= 4 * mm

            # Location
            c.setFont("Helvetica", 8)
            c.drawString(text_x, text_y, content.location_name[:30])
            text_y -= 3.5 * mm

            # Contents summary
            if content.contents_summary:
                c.setFont("Helvetica", 7)
                c.drawString(text_x, text_y, content.contents_summary[:35])
                text_y -= 3 * mm

            # QR code value
            c.setFont("Helvetica", 6)
            c.setFillGray(0.5)
            c.drawString(text_x, y + 2 * mm, content.container_qr_code)
            c.setFillGray(0)

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
