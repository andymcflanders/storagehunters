"""FastSAM segmentation service API."""

import base64
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from app.segmenter import get_segmenter, SegmentInfo, SegmentationResult


app = FastAPI(
    title="FastSAM Segmentation Service",
    description="Image segmentation service using FastSAM for background removal and multi-object detection",
    version="1.0.0",
)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class SegmentResponse(BaseModel):
    success: bool
    segments: list[dict]
    error: Optional[str] = None
    processing_time_ms: int


@app.on_event("startup")
async def startup_event():
    """Load the model on startup."""
    # This triggers model loading
    segmenter = get_segmenter()
    print(f"FastSAM model loaded: {segmenter.is_ready()}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and model status."""
    segmenter = get_segmenter()
    return HealthResponse(
        status="healthy" if segmenter.is_ready() else "unhealthy",
        model_loaded=segmenter.is_ready()
    )


@app.post("/segment", response_model=SegmentResponse)
async def segment_single(
    file: UploadFile = File(...),
    confidence: float = Form(0.5),
):
    """Segment the largest object from an image.

    Returns a single segmented image with transparent background.
    Use this for single-item photos where you want background removal.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    segmenter = get_segmenter()
    result = segmenter.segment_single(image_bytes, confidence_threshold=confidence)

    return SegmentResponse(
        success=result.success,
        segments=[
            {
                "image": seg.image_base64,
                "bbox": list(seg.bbox),
                "confidence": seg.confidence,
                "area_ratio": seg.area_ratio,
            }
            for seg in result.segments
        ],
        error=result.error,
        processing_time_ms=result.processing_time_ms,
    )


@app.post("/segment/multi", response_model=SegmentResponse)
async def segment_multi(
    file: UploadFile = File(...),
    min_area_ratio: float = Form(1.0),
    max_objects: int = Form(10),
    confidence: float = Form(0.5),
):
    """Segment multiple objects from an image.

    Returns multiple segmented images, one for each detected object.
    Objects are filtered by minimum area and limited to non-overlapping regions.

    Args:
        file: Image file to segment
        min_area_ratio: Minimum object area as percentage of image (default 1%)
        max_objects: Maximum number of objects to return (default 10)
        confidence: Minimum detection confidence (default 0.5)
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    segmenter = get_segmenter()
    result = segmenter.segment_multi(
        image_bytes,
        min_area_ratio=min_area_ratio,
        max_objects=max_objects,
        confidence_threshold=confidence,
    )

    return SegmentResponse(
        success=result.success,
        segments=[
            {
                "image": seg.image_base64,
                "bbox": list(seg.bbox),
                "confidence": seg.confidence,
                "area_ratio": seg.area_ratio,
            }
            for seg in result.segments
        ],
        error=result.error,
        processing_time_ms=result.processing_time_ms,
    )


@app.post("/segment/base64", response_model=SegmentResponse)
async def segment_single_base64(
    image: str,
    confidence: float = 0.5,
):
    """Segment from base64-encoded image.

    Alternative endpoint that accepts base64-encoded image data
    instead of file upload.
    """
    try:
        image_bytes = base64.b64decode(image)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image data")

    segmenter = get_segmenter()
    result = segmenter.segment_single(image_bytes, confidence_threshold=confidence)

    return SegmentResponse(
        success=result.success,
        segments=[
            {
                "image": seg.image_base64,
                "bbox": list(seg.bbox),
                "confidence": seg.confidence,
                "area_ratio": seg.area_ratio,
            }
            for seg in result.segments
        ],
        error=result.error,
        processing_time_ms=result.processing_time_ms,
    )
