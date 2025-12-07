"""Replicate API client for cloud-based SAM segmentation."""

import asyncio
import base64
import io
from typing import Optional

import httpx
from PIL import Image

from app.config import get_settings
from app.services.fastsam_client import SegmentResult, MultiSegmentResult

settings = get_settings()


class ReplicateClient:
    """Client for Replicate's SAM models."""

    REPLICATE_API_URL = "https://api.replicate.com/v1"

    def __init__(
        self,
        api_token: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """Initialize the client.

        Args:
            api_token: Replicate API token, defaults to config value
            model: SAM model to use, defaults to config value
            timeout: Request timeout in seconds
        """
        self.api_token = api_token or settings.replicate_api_token
        self.model = model or settings.replicate_sam_model
        self.timeout = timeout

    def _get_headers(self) -> dict:
        """Get request headers with auth."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def health_check(self) -> bool:
        """Check if Replicate API is available.

        Returns:
            True if API is accessible and token is valid
        """
        if not self.api_token:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.REPLICATE_API_URL}/models/{self.model}",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    async def _run_prediction(
        self,
        image_bytes: bytes,
        points_per_side: int = 32,
        pred_iou_thresh: float = 0.88,
    ) -> dict:
        """Run a SAM prediction on Replicate.

        Args:
            image_bytes: Raw image bytes
            points_per_side: Points per side for automatic mask generation
            pred_iou_thresh: IoU threshold for predictions

        Returns:
            Prediction result dict
        """
        # Convert image to base64 data URI
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Detect image format
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        else:
            mime_type = "image/jpeg"  # Default to JPEG

        image_uri = f"data:{mime_type};base64,{image_b64}"

        # Prepare input based on model
        if "sam-2" in self.model:
            # SAM 2 input format
            input_data = {
                "image": image_uri,
                "use_m2m": True,
                "points_per_side": points_per_side,
                "pred_iou_thresh": pred_iou_thresh,
                "stability_score_thresh": 0.95,
                "output_format": "png",
                "return_single_mask": False,
            }
        elif "grounded-sam" in self.model:
            # Grounded SAM input format
            input_data = {
                "image": image_uri,
                "text_prompt": "object, item, thing",
                "box_threshold": 0.3,
                "text_threshold": 0.25,
            }
        else:
            # Generic SAM input format
            input_data = {
                "image": image_uri,
                "points_per_side": points_per_side,
                "pred_iou_thresh": pred_iou_thresh,
            }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Create prediction
            response = await client.post(
                f"{self.REPLICATE_API_URL}/predictions",
                headers=self._get_headers(),
                json={
                    "version": await self._get_model_version(),
                    "input": input_data,
                },
            )

            if response.status_code not in (200, 201):
                raise Exception(f"Failed to create prediction: {response.text}")

            prediction = response.json()
            prediction_id = prediction["id"]

            # Poll for completion
            max_attempts = 60  # 2 minutes with 2 second intervals
            for _ in range(max_attempts):
                response = await client.get(
                    f"{self.REPLICATE_API_URL}/predictions/{prediction_id}",
                    headers=self._get_headers(),
                )

                if response.status_code != 200:
                    raise Exception(f"Failed to get prediction: {response.text}")

                prediction = response.json()
                status = prediction["status"]

                if status == "succeeded":
                    return prediction
                elif status == "failed":
                    raise Exception(prediction.get("error", "Prediction failed"))
                elif status == "canceled":
                    raise Exception("Prediction was canceled")

                await asyncio.sleep(2)

            raise Exception("Prediction timed out")

    async def _get_model_version(self) -> str:
        """Get the latest version of the model."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.REPLICATE_API_URL}/models/{self.model}",
                headers=self._get_headers(),
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get model info: {response.text}")

            model_info = response.json()
            return model_info["latest_version"]["id"]

    async def _download_mask(self, url: str) -> bytes:
        """Download a mask image from URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise Exception(f"Failed to download mask: {response.status_code}")
            return response.content

    async def _apply_mask_to_image(
        self,
        original_bytes: bytes,
        mask_bytes: bytes,
    ) -> tuple[bytes, tuple[int, int, int, int]]:
        """Apply a mask to create a transparent PNG.

        Args:
            original_bytes: Original image bytes
            mask_bytes: Mask image bytes (white = keep, black = remove)

        Returns:
            Tuple of (cropped PNG bytes, bounding box)
        """
        # Load images
        original = Image.open(io.BytesIO(original_bytes)).convert("RGBA")
        mask = Image.open(io.BytesIO(mask_bytes)).convert("L")

        # Resize mask to match original if needed
        if mask.size != original.size:
            mask = mask.resize(original.size, Image.LANCZOS)

        # Apply mask as alpha channel
        r, g, b, _ = original.split()
        result = Image.merge("RGBA", (r, g, b, mask))

        # Find bounding box of non-transparent pixels
        bbox = result.getbbox()
        if bbox:
            result = result.crop(bbox)
        else:
            bbox = (0, 0, original.width, original.height)

        # Save to bytes
        output = io.BytesIO()
        result.save(output, format="PNG")
        return output.getvalue(), bbox

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
            prediction = await self._run_prediction(
                image_bytes,
                points_per_side=32,
                pred_iou_thresh=confidence,
            )

            output = prediction.get("output")
            if not output:
                return SegmentResult(
                    success=False,
                    error="No output from model",
                )

            # Handle different output formats
            masks = []
            if isinstance(output, dict):
                # SAM 2 format: {"combined_mask": url, "individual_masks": [urls]}
                if "individual_masks" in output:
                    masks = output["individual_masks"]
                elif "combined_mask" in output:
                    masks = [output["combined_mask"]]
            elif isinstance(output, list):
                masks = output
            elif isinstance(output, str):
                masks = [output]

            if not masks:
                return SegmentResult(
                    success=False,
                    error="No masks generated",
                )

            # Find the largest mask
            largest_mask = None
            largest_area = 0

            for mask_url in masks[:10]:  # Limit to first 10
                mask_bytes = await self._download_mask(mask_url)
                mask_img = Image.open(io.BytesIO(mask_bytes)).convert("L")

                # Count white pixels (mask area)
                pixels = list(mask_img.getdata())
                area = sum(1 for p in pixels if p > 128)

                if area > largest_area:
                    largest_area = area
                    largest_mask = mask_bytes

            if not largest_mask:
                return SegmentResult(
                    success=False,
                    error="No valid masks found",
                )

            # Apply mask to create transparent PNG
            result_bytes, bbox = await self._apply_mask_to_image(
                image_bytes, largest_mask
            )

            # Calculate area ratio
            original = Image.open(io.BytesIO(image_bytes))
            total_pixels = original.width * original.height
            area_ratio = (largest_area / total_pixels) * 100

            return SegmentResult(
                success=True,
                image_bytes=result_bytes,
                bbox=bbox,
                confidence=confidence,
                area_ratio=area_ratio,
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
        import time
        start_time = time.time()

        try:
            prediction = await self._run_prediction(
                image_bytes,
                points_per_side=32,
                pred_iou_thresh=confidence,
            )

            output = prediction.get("output")
            if not output:
                return MultiSegmentResult(
                    success=False,
                    error="No output from model",
                )

            # Handle different output formats
            masks = []
            if isinstance(output, dict):
                if "individual_masks" in output:
                    masks = output["individual_masks"]
                elif "combined_mask" in output:
                    masks = [output["combined_mask"]]
            elif isinstance(output, list):
                masks = output
            elif isinstance(output, str):
                masks = [output]

            if not masks:
                return MultiSegmentResult(
                    success=False,
                    error="No masks generated",
                )

            # Get original image dimensions
            original = Image.open(io.BytesIO(image_bytes))
            total_pixels = original.width * original.height
            min_pixels = (min_area_ratio / 100) * total_pixels

            segments = []
            for mask_url in masks[:max_objects * 2]:  # Get more to filter
                try:
                    mask_bytes = await self._download_mask(mask_url)
                    mask_img = Image.open(io.BytesIO(mask_bytes)).convert("L")

                    # Count white pixels
                    pixels = list(mask_img.getdata())
                    area = sum(1 for p in pixels if p > 128)

                    # Skip if too small
                    if area < min_pixels:
                        continue

                    # Apply mask
                    result_bytes, bbox = await self._apply_mask_to_image(
                        image_bytes, mask_bytes
                    )

                    area_ratio = (area / total_pixels) * 100

                    segments.append(
                        SegmentResult(
                            success=True,
                            image_bytes=result_bytes,
                            bbox=bbox,
                            confidence=confidence,
                            area_ratio=area_ratio,
                        )
                    )

                    if len(segments) >= max_objects:
                        break

                except Exception as e:
                    continue  # Skip failed masks

            processing_time = int((time.time() - start_time) * 1000)

            if not segments:
                return MultiSegmentResult(
                    success=False,
                    error="No valid segments found",
                    processing_time_ms=processing_time,
                )

            # Sort by area (largest first)
            segments.sort(key=lambda s: s.area_ratio, reverse=True)

            return MultiSegmentResult(
                success=True,
                segments=segments[:max_objects],
                processing_time_ms=processing_time,
            )

        except Exception as e:
            return MultiSegmentResult(
                success=False,
                error=str(e),
            )


def get_replicate_client() -> ReplicateClient:
    """Get a Replicate client instance."""
    return ReplicateClient()
