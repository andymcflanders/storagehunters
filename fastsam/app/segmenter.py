"""FastSAM model wrapper for image segmentation."""

import io
import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
from ultralytics import FastSAM


@dataclass
class SegmentInfo:
    """Information about a single segmented object."""

    image_base64: str  # PNG with transparency, base64 encoded
    bbox: tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    area_ratio: float  # Percentage of image area


@dataclass
class SegmentationResult:
    """Result of image segmentation."""

    success: bool
    segments: list[SegmentInfo] = field(default_factory=list)
    error: Optional[str] = None
    processing_time_ms: int = 0


class FastSAMSegmenter:
    """FastSAM model wrapper for segmentation tasks."""

    def __init__(self, model_path: str = "FastSAM-s.pt", device: str = "cpu"):
        """Initialize the FastSAM model.

        Args:
            model_path: Path to FastSAM model weights
            device: Device to run inference on ('cpu' or 'cuda')
        """
        self.model = FastSAM(model_path)
        self.device = device
        self._model_loaded = True

    def _image_to_pil(self, image_bytes: bytes) -> Image.Image:
        """Convert bytes to PIL Image."""
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")

    def _mask_to_rgba(
        self,
        image: Image.Image,
        mask: np.ndarray,
        crop_to_bbox: bool = True
    ) -> tuple[bytes, tuple[int, int, int, int]]:
        """Apply mask to image and return PNG with transparency.

        Args:
            image: Original PIL image
            mask: Binary mask (H, W) where True = object
            crop_to_bbox: Whether to crop result to bounding box

        Returns:
            Tuple of (PNG bytes, bbox as x,y,w,h)
        """
        # Convert image to RGBA
        img_array = np.array(image)
        rgba = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)
        rgba[:, :, :3] = img_array

        # Apply mask to alpha channel
        rgba[:, :, 3] = (mask * 255).astype(np.uint8)

        # Find bounding box
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not rows.any() or not cols.any():
            # Empty mask
            return b"", (0, 0, 0, 0)

        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]

        bbox = (int(x_min), int(y_min), int(x_max - x_min + 1), int(y_max - y_min + 1))

        if crop_to_bbox:
            # Crop to bounding box
            rgba = rgba[y_min:y_max+1, x_min:x_max+1]

        # Convert to PNG
        result_image = Image.fromarray(rgba, mode="RGBA")
        buffer = io.BytesIO()
        result_image.save(buffer, format="PNG", optimize=True)

        return buffer.getvalue(), bbox

    def _get_masks_from_results(self, results) -> list[tuple[np.ndarray, float]]:
        """Extract masks and confidences from FastSAM results."""
        masks_with_conf = []

        if results and len(results) > 0 and results[0].masks is not None:
            masks = results[0].masks.data.cpu().numpy()

            # Get confidence scores if available
            if results[0].boxes is not None and results[0].boxes.conf is not None:
                confs = results[0].boxes.conf.cpu().numpy()
            else:
                confs = np.ones(len(masks))

            for i, mask in enumerate(masks):
                conf = float(confs[i]) if i < len(confs) else 1.0
                masks_with_conf.append((mask.astype(bool), conf))

        return masks_with_conf

    def segment_single(
        self,
        image_bytes: bytes,
        confidence_threshold: float = 0.5
    ) -> SegmentationResult:
        """Segment the single largest object from the image.

        Args:
            image_bytes: Raw image bytes
            confidence_threshold: Minimum confidence threshold

        Returns:
            SegmentationResult with single segment (largest object)
        """
        import time
        start_time = time.time()

        try:
            image = self._image_to_pil(image_bytes)
            img_area = image.width * image.height

            # Run FastSAM inference
            results = self.model(
                image,
                device=self.device,
                retina_masks=True,
                conf=confidence_threshold,
                iou=0.7,
            )

            masks_with_conf = self._get_masks_from_results(results)

            if not masks_with_conf:
                return SegmentationResult(
                    success=False,
                    error="No objects detected in image",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Find largest mask by area
            largest_mask = None
            largest_area = 0
            largest_conf = 0.0

            for mask, conf in masks_with_conf:
                area = np.sum(mask)
                if area > largest_area:
                    largest_area = area
                    largest_mask = mask
                    largest_conf = conf

            if largest_mask is None:
                return SegmentationResult(
                    success=False,
                    error="No valid masks found",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Convert mask to RGBA image
            png_bytes, bbox = self._mask_to_rgba(image, largest_mask)

            if not png_bytes:
                return SegmentationResult(
                    success=False,
                    error="Failed to create segmented image",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            segment = SegmentInfo(
                image_base64=base64.b64encode(png_bytes).decode("utf-8"),
                bbox=bbox,
                confidence=largest_conf,
                area_ratio=float(largest_area / img_area) * 100
            )

            return SegmentationResult(
                success=True,
                segments=[segment],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            return SegmentationResult(
                success=False,
                error=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

    def segment_multi(
        self,
        image_bytes: bytes,
        min_area_ratio: float = 1.0,
        max_objects: int = 10,
        confidence_threshold: float = 0.5
    ) -> SegmentationResult:
        """Segment multiple non-overlapping objects from the image.

        Args:
            image_bytes: Raw image bytes
            min_area_ratio: Minimum area as percentage of image (1.0 = 1%)
            max_objects: Maximum number of objects to return
            confidence_threshold: Minimum confidence threshold

        Returns:
            SegmentationResult with multiple segments
        """
        import time
        start_time = time.time()

        try:
            image = self._image_to_pil(image_bytes)
            img_area = image.width * image.height
            min_area = img_area * (min_area_ratio / 100)

            # Run FastSAM inference
            results = self.model(
                image,
                device=self.device,
                retina_masks=True,
                conf=confidence_threshold,
                iou=0.7,
            )

            masks_with_conf = self._get_masks_from_results(results)

            if not masks_with_conf:
                return SegmentationResult(
                    success=False,
                    error="No objects detected in image",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Filter by minimum area and sort by size (largest first)
            valid_masks = []
            for mask, conf in masks_with_conf:
                area = np.sum(mask)
                if area >= min_area:
                    valid_masks.append((mask, conf, area))

            valid_masks.sort(key=lambda x: x[2], reverse=True)

            # Select non-overlapping masks
            selected_masks = []
            combined_mask = np.zeros_like(valid_masks[0][0]) if valid_masks else None

            for mask, conf, area in valid_masks:
                if len(selected_masks) >= max_objects:
                    break

                # Check overlap with already selected masks
                if combined_mask is not None:
                    overlap = np.sum(mask & combined_mask)
                    overlap_ratio = overlap / area if area > 0 else 0

                    # Skip if more than 30% overlaps with existing selections
                    if overlap_ratio > 0.3:
                        continue

                selected_masks.append((mask, conf, area))
                if combined_mask is not None:
                    combined_mask = combined_mask | mask

            if not selected_masks:
                return SegmentationResult(
                    success=False,
                    error="No objects meet the minimum size requirement",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Convert each mask to segment
            segments = []
            for mask, conf, area in selected_masks:
                png_bytes, bbox = self._mask_to_rgba(image, mask)

                if png_bytes:
                    segment = SegmentInfo(
                        image_base64=base64.b64encode(png_bytes).decode("utf-8"),
                        bbox=bbox,
                        confidence=conf,
                        area_ratio=float(area / img_area) * 100
                    )
                    segments.append(segment)

            return SegmentationResult(
                success=True,
                segments=segments,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            return SegmentationResult(
                success=False,
                error=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

    def is_ready(self) -> bool:
        """Check if the model is loaded and ready."""
        return self._model_loaded


# Global segmenter instance (loaded once on startup)
_segmenter: Optional[FastSAMSegmenter] = None


def get_segmenter() -> FastSAMSegmenter:
    """Get or create the global segmenter instance."""
    global _segmenter
    if _segmenter is None:
        import os
        device = os.environ.get("DEVICE", "cpu")
        model_path = os.environ.get("MODEL_PATH", "FastSAM-s.pt")
        _segmenter = FastSAMSegmenter(model_path=model_path, device=device)
    return _segmenter
