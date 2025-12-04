"""QR code generation service."""

import io
from uuid import UUID

import qrcode
from qrcode.image.pil import PilImage

from app.config import get_settings

settings = get_settings()


class QRGeneratorService:
    """Service for generating QR codes."""

    def generate_container_url(self, qr_code: str) -> str:
        """Generate the URL for a container QR code."""
        return f"{settings.frontend_url}/c/{qr_code}"

    def generate_qr_image(
        self,
        data: str,
        size: int = 200,
        border: int = 2,
    ) -> bytes:
        """
        Generate a QR code image.

        Args:
            data: The data to encode in the QR code
            size: The size of the image in pixels
            border: The border size in boxes

        Returns:
            PNG image bytes
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img: PilImage = qr.make_image(fill_color="black", back_color="white")

        # Resize to requested size
        img = img.resize((size, size))

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def generate_container_qr(
        self,
        qr_code: str,
        size: int = 200,
    ) -> bytes:
        """Generate a QR code for a container."""
        url = self.generate_container_url(qr_code)
        return self.generate_qr_image(url, size)
