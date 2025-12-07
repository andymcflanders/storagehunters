"""Unified segmentation service that supports multiple providers."""

from typing import Protocol, Optional
import logging

from app.config import get_settings
from app.services.fastsam_client import (
    FastSAMClient,
    SegmentResult,
    MultiSegmentResult,
)
from app.services.replicate_client import ReplicateClient

settings = get_settings()
logger = logging.getLogger(__name__)


class SegmentationProvider(Protocol):
    """Protocol for segmentation providers."""

    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...

    async def segment_single(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
    ) -> SegmentResult:
        """Segment the largest object from an image."""
        ...

    async def segment_multi(
        self,
        image_bytes: bytes,
        min_area_ratio: float = 1.0,
        max_objects: int = 10,
        confidence: float = 0.5,
    ) -> MultiSegmentResult:
        """Segment multiple objects from an image."""
        ...


class SegmentationService:
    """Service that manages segmentation using configured provider."""

    def __init__(self):
        """Initialize with configured provider."""
        self._provider: Optional[SegmentationProvider] = None
        self._provider_name: str = ""

    def _get_provider(self) -> SegmentationProvider:
        """Get the configured segmentation provider.

        Returns:
            The provider instance

        Raises:
            ValueError: If no provider is configured or enabled
        """
        if not settings.segmentation_enabled:
            raise ValueError("Segmentation is disabled")

        provider_name = settings.segmentation_provider.lower()

        # Cache the provider if it matches current config
        if self._provider and self._provider_name == provider_name:
            return self._provider

        if provider_name == "local":
            self._provider = FastSAMClient()
            self._provider_name = provider_name
            logger.info("Using local FastSAM for segmentation")
        elif provider_name == "replicate":
            if not settings.replicate_api_token:
                raise ValueError("Replicate API token not configured")
            self._provider = ReplicateClient()
            self._provider_name = provider_name
            logger.info(f"Using Replicate ({settings.replicate_sam_model}) for segmentation")
        else:
            raise ValueError(f"Unknown segmentation provider: {provider_name}")

        return self._provider

    @property
    def provider_name(self) -> str:
        """Get the current provider name."""
        return settings.segmentation_provider.lower()

    @property
    def is_enabled(self) -> bool:
        """Check if segmentation is enabled."""
        return settings.segmentation_enabled

    @property
    def is_cloud(self) -> bool:
        """Check if using a cloud provider."""
        return self.provider_name == "replicate"

    async def health_check(self) -> dict:
        """Check the health of the segmentation service.

        Returns:
            Dict with status information
        """
        if not settings.segmentation_enabled:
            return {
                "enabled": False,
                "provider": None,
                "status": "disabled",
            }

        try:
            provider = self._get_provider()
            healthy = await provider.health_check()
            return {
                "enabled": True,
                "provider": self.provider_name,
                "status": "healthy" if healthy else "unhealthy",
                "model": settings.replicate_sam_model if self.is_cloud else "FastSAM-s",
            }
        except ValueError as e:
            return {
                "enabled": True,
                "provider": self.provider_name,
                "status": "error",
                "error": str(e),
            }
        except Exception as e:
            return {
                "enabled": True,
                "provider": self.provider_name,
                "status": "error",
                "error": str(e),
            }

    async def segment_single(
        self,
        image_bytes: bytes,
        confidence: Optional[float] = None,
    ) -> SegmentResult:
        """Segment the largest object from an image.

        Args:
            image_bytes: Raw image bytes
            confidence: Minimum confidence threshold (uses config default if None)

        Returns:
            SegmentResult with the segmented image
        """
        provider = self._get_provider()
        conf = confidence if confidence is not None else settings.segmentation_confidence_threshold
        return await provider.segment_single(image_bytes, confidence=conf)

    async def segment_multi(
        self,
        image_bytes: bytes,
        min_area_ratio: Optional[float] = None,
        max_objects: int = 10,
        confidence: Optional[float] = None,
    ) -> MultiSegmentResult:
        """Segment multiple objects from an image.

        Args:
            image_bytes: Raw image bytes
            min_area_ratio: Minimum area as percentage of image (uses config default if None)
            max_objects: Maximum number of objects to return
            confidence: Minimum confidence threshold (uses config default if None)

        Returns:
            MultiSegmentResult with all segmented images
        """
        provider = self._get_provider()
        conf = confidence if confidence is not None else settings.segmentation_confidence_threshold
        min_area = min_area_ratio if min_area_ratio is not None else settings.segmentation_min_area_ratio
        return await provider.segment_multi(
            image_bytes,
            min_area_ratio=min_area,
            max_objects=max_objects,
            confidence=conf,
        )


# Singleton instance
_segmentation_service: Optional[SegmentationService] = None


def get_segmentation_service() -> SegmentationService:
    """Get the segmentation service singleton."""
    global _segmentation_service
    if _segmentation_service is None:
        _segmentation_service = SegmentationService()
    return _segmentation_service
