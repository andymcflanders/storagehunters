"""FastSAM service client for image segmentation."""

import base64
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class SegmentResult:
    """Result of a segmentation operation."""

    success: bool
    image_bytes: bytes = b""  # PNG with transparency
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, width, height
    confidence: float = 0.0
    area_ratio: float = 0.0
    error: Optional[str] = None


@dataclass
class MultiSegmentResult:
    """Result of a multi-object segmentation."""

    success: bool
    segments: list[SegmentResult] = field(default_factory=list)
    processing_time_ms: int = 0
    error: Optional[str] = None


class FastSAMClient:
    """Client for communicating with FastSAM segmentation service."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0):
        """Initialize the client.

        Args:
            base_url: FastSAM service URL, defaults to config value
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.fastsam_url
        self.timeout = timeout

    async def health_check(self) -> bool:
        """Check if the FastSAM service is available and healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("model_loaded", False)
                return False
        except Exception:
            return False

    async def segment_single(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
    ) -> SegmentResult:
        """Segment the largest object from an image.

        Args:
            image_bytes: Raw image bytes
            confidence: Minimum confidence threshold

        Returns:
            SegmentResult with the segmented image
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                data = {"confidence": str(confidence)}

                response = await client.post(
                    f"{self.base_url}/segment",
                    files=files,
                    data=data,
                )

                if response.status_code != 200:
                    return SegmentResult(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                result = response.json()

                if not result.get("success") or not result.get("segments"):
                    return SegmentResult(
                        success=False,
                        error=result.get("error", "No segments found"),
                    )

                # Get the first (and only) segment
                segment = result["segments"][0]
                image_b64 = segment.get("image", "")
                image_data = base64.b64decode(image_b64) if image_b64 else b""

                return SegmentResult(
                    success=True,
                    image_bytes=image_data,
                    bbox=tuple(segment.get("bbox", [0, 0, 0, 0])),
                    confidence=segment.get("confidence", 0.0),
                    area_ratio=segment.get("area_ratio", 0.0),
                )

        except httpx.TimeoutException:
            return SegmentResult(
                success=False,
                error="Segmentation request timed out",
            )
        except Exception as e:
            return SegmentResult(
                success=False,
                error=str(e),
            )

    async def segment_multi(
        self,
        image_bytes: bytes,
        min_area_ratio: float = 1.0,
        max_objects: int = 10,
        confidence: float = 0.5,
    ) -> MultiSegmentResult:
        """Segment multiple objects from an image.

        Args:
            image_bytes: Raw image bytes
            min_area_ratio: Minimum area as percentage of image (1.0 = 1%)
            max_objects: Maximum number of objects to return
            confidence: Minimum confidence threshold

        Returns:
            MultiSegmentResult with all segmented images
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                data = {
                    "min_area_ratio": str(min_area_ratio),
                    "max_objects": str(max_objects),
                    "confidence": str(confidence),
                }

                response = await client.post(
                    f"{self.base_url}/segment/multi",
                    files=files,
                    data=data,
                )

                if response.status_code != 200:
                    return MultiSegmentResult(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                result = response.json()

                if not result.get("success"):
                    return MultiSegmentResult(
                        success=False,
                        error=result.get("error", "Segmentation failed"),
                        processing_time_ms=result.get("processing_time_ms", 0),
                    )

                segments = []
                for seg_data in result.get("segments", []):
                    image_b64 = seg_data.get("image", "")
                    image_data = base64.b64decode(image_b64) if image_b64 else b""

                    segments.append(
                        SegmentResult(
                            success=True,
                            image_bytes=image_data,
                            bbox=tuple(seg_data.get("bbox", [0, 0, 0, 0])),
                            confidence=seg_data.get("confidence", 0.0),
                            area_ratio=seg_data.get("area_ratio", 0.0),
                        )
                    )

                return MultiSegmentResult(
                    success=True,
                    segments=segments,
                    processing_time_ms=result.get("processing_time_ms", 0),
                )

        except httpx.TimeoutException:
            return MultiSegmentResult(
                success=False,
                error="Segmentation request timed out",
            )
        except Exception as e:
            return MultiSegmentResult(
                success=False,
                error=str(e),
            )


def get_fastsam_client() -> FastSAMClient:
    """Get a FastSAM client instance."""
    return FastSAMClient()
