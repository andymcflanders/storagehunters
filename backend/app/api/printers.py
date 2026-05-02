"""Printer API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.ai import ContainerItem, get_summary_generator
from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.models.container import Container
from app.models.item import Item, ItemImage
from app.models.location import Location
from app.models.printer import Printer
from app.models.user import User
from app.printing import get_driver
from app.printing.base import ItemDetail, LabelContent, LabelTemplate

settings = get_settings()
from app.schemas.printer import (
    BatchLabelData,
    BatchPrintResult,
    DetectedMediaResponse,
    LabelData,
    MediaSuggestion,
    PrinterCreate,
    PrinterResponse,
    PrinterUpdate,
)

router = APIRouter()


def suggest_template_for_media(
    width_mm: float | None, height_mm: float | None
) -> tuple[LabelTemplate, str, str]:
    """Suggest a template based on media dimensions.

    Returns: (template, confidence, reason)
    """
    if width_mm is None:
        return (
            LabelTemplate.QR_AI_SUMMARY,
            "low",
            "Could not detect media dimensions. Using default medium template.",
        )

    # For continuous media, estimate reasonable height
    effective_height = height_mm if height_mm and height_mm > 0 else width_mm

    area = width_mm * effective_height

    if area < 1500:  # Small (~29x52mm)
        return (
            LabelTemplate.QR_ONLY,
            "high" if height_mm else "medium",
            f"Small label ({width_mm}x{effective_height}mm) - QR code only for readability",
        )
    elif area < 5000:  # Medium (~62x80mm)
        return (
            LabelTemplate.QR_AI_SUMMARY,
            "high" if height_mm else "medium",
            f"Medium label ({width_mm}x{effective_height}mm) - QR code with AI summary",
        )
    elif area < 50000:  # Large label
        return (
            LabelTemplate.QR_FULL_CONTENTS,
            "high" if height_mm else "medium",
            f"Large label ({width_mm}x{effective_height}mm) - can fit full contents list",
        )
    else:  # A4 or larger (210x297mm = 62370 area)
        return (
            LabelTemplate.A4_FULL_DETAILS,
            "high",
            f"A4/Full page ({width_mm}x{effective_height}mm) - full details with item table",
        )


async def build_label_content(
    db: DbSession,
    container: Container,
    location: Location,
    template: LabelTemplate,
) -> LabelContent:
    """Build label content based on template type."""

    base_content = {
        "container_name": container.name,
        "container_qr_code": container.qr_code,
        "location_name": location.name,
        "template": template,
    }

    if template == LabelTemplate.QR_ONLY:
        # Minimal content - just the base fields
        return LabelContent(**base_content)

    elif template == LabelTemplate.QR_AI_SUMMARY:
        # Fetch items with details for AI summary, including owner name.
        # ai_descriptions is a JSONB dict; we resolve to a single string
        # below using the configured default language.
        result = await db.execute(
            select(
                Item.name,
                Item.description,
                Item.ai_descriptions,
                Item.seasonal,
                Item.size,
                User.name.label("owner_name"),
            )
            .outerjoin(User, Item.owner_id == User.id)
            .where(Item.container_id == container.id)
            .order_by(Item.name)
        )
        items = result.all()
        item_count = len(items)

        from app.ai import _load_ai_settings_sync
        from app.services.localized import localized

        default_lang = _load_ai_settings_sync().default_language

        container_items = [
            ContainerItem(
                name=item.name,
                description=item.description,
                ai_description=localized(item.ai_descriptions, default_lang),
                seasonal=item.seasonal.value if item.seasonal else None,
                size=item.size,
                owner_name=item.owner_name,
            )
            for item in items
        ]

        # Generate AI summary
        summary_generator = get_summary_generator()
        summary_result = await summary_generator.generate_summary(
            container_name=container.name,
            location_name=location.name,
            items=container_items,
            max_length=300,  # Allow 2-4 sentences for label printing
        )

        return LabelContent(
            **base_content,
            ai_summary=summary_result.summary,
            item_count=item_count,
        )

    elif template == LabelTemplate.QR_FULL_CONTENTS:
        # Fetch ALL items
        result = await db.execute(
            select(Item.name)
            .where(Item.container_id == container.id)
            .order_by(Item.name)
        )
        items = result.scalars().all()

        return LabelContent(
            **base_content,
            full_contents=list(items),
            item_count=len(items),
        )

    elif template == LabelTemplate.A4_FULL_DETAILS:
        # Fetch detailed item info with owner, size, description, and primary image
        result = await db.execute(
            select(
                Item.id,
                Item.name,
                Item.description,
                Item.ai_descriptions,
                Item.size,
                Item.primary_image_id,
                User.name.label("owner_name"),
            )
            .outerjoin(User, Item.owner_id == User.id)
            .where(Item.container_id == container.id)
            .order_by(Item.name)
        )
        items = result.all()
        item_count = len(items)

        # Collect item IDs that have primary images
        item_ids_with_images = [
            item.id for item in items if item.primary_image_id is not None
        ]

        # Fetch primary image paths in a single query
        image_paths: dict[str, str] = {}
        if item_ids_with_images:
            img_result = await db.execute(
                select(ItemImage.item_id, ItemImage.filepath)
                .where(ItemImage.id.in_(
                    select(Item.primary_image_id)
                    .where(Item.id.in_(item_ids_with_images))
                ))
            )
            for row in img_result.all():
                image_paths[str(row.item_id)] = str(settings.upload_dir / row.filepath)

        # Build item details
        from app.ai import _load_ai_settings_sync
        from app.services.localized import localized

        default_lang = _load_ai_settings_sync().default_language

        item_details = []
        for item in items:
            ai_desc = localized(item.ai_descriptions, default_lang)
            description = ai_desc or item.description

            # Get thumbnail path - first try primary_image_id, then fall back to first image
            thumbnail_path = None
            img_path = None

            if item.primary_image_id:
                # Query for the primary image
                img_result = await db.execute(
                    select(ItemImage.filepath)
                    .where(ItemImage.id == item.primary_image_id)
                )
                img_path = img_result.scalar_one_or_none()

            if not img_path:
                # Fall back to first image for this item
                img_result = await db.execute(
                    select(ItemImage.filepath)
                    .where(ItemImage.item_id == item.id)
                    .order_by(ItemImage.created_at)
                    .limit(1)
                )
                img_path = img_result.scalar_one_or_none()

            if img_path:
                full_path = settings.upload_dir / img_path
                if full_path.exists():
                    thumbnail_path = str(full_path)

            item_details.append(
                ItemDetail(
                    name=item.name,
                    description=description,
                    owner_name=item.owner_name,
                    size=item.size,
                    thumbnail_path=thumbnail_path,
                )
            )

        # Also generate AI summary for the header
        container_items = [
            ContainerItem(
                name=item.name,
                description=item.description,
                ai_description=localized(item.ai_descriptions, default_lang),
                size=item.size,
                owner_name=item.owner_name,
            )
            for item in items
        ]

        summary_generator = get_summary_generator()
        summary_result = await summary_generator.generate_summary(
            container_name=container.name,
            location_name=location.name,
            items=container_items,
            max_length=400,  # Longer summary for A4 page
        )

        return LabelContent(
            **base_content,
            ai_summary=summary_result.summary,
            item_count=item_count,
            item_details=item_details,
        )

    else:
        # Legacy behavior - first 5 items
        result = await db.execute(
            select(Item.name).where(Item.container_id == container.id).limit(5)
        )
        items = result.scalars().all()
        contents_summary = None
        if items:
            contents_summary = ", ".join(items)
            if len(items) == 5:
                contents_summary += "..."

        return LabelContent(
            **base_content,
            contents_summary=contents_summary,
        )


@router.get("", response_model=list[PrinterResponse])
async def list_printers(db: DbSession) -> list[PrinterResponse]:
    """List all configured printers."""
    result = await db.execute(select(Printer).order_by(Printer.name))
    printers = result.scalars().all()
    return [PrinterResponse.model_validate(p) for p in printers]


@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
async def create_printer(
    printer_data: PrinterCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> PrinterResponse:
    """Create a new printer configuration."""
    # If setting as default, unset other defaults
    if printer_data.is_default:
        result = await db.execute(select(Printer).where(Printer.is_default == True))
        for p in result.scalars():
            p.is_default = False

    printer = Printer(**printer_data.model_dump())
    db.add(printer)
    await db.flush()
    await db.refresh(printer)
    return PrinterResponse.model_validate(printer)


@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer(printer_id: UUID, db: DbSession) -> PrinterResponse:
    """Get a printer by ID."""
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )
    return PrinterResponse.model_validate(printer)


@router.patch("/{printer_id}", response_model=PrinterResponse)
async def update_printer(
    printer_id: UUID,
    printer_data: PrinterUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> PrinterResponse:
    """Update a printer configuration."""
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    update_data = printer_data.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        result = await db.execute(
            select(Printer).where(Printer.is_default == True, Printer.id != printer_id)
        )
        for p in result.scalars():
            p.is_default = False

    for field, value in update_data.items():
        setattr(printer, field, value)

    await db.flush()
    await db.refresh(printer)
    return PrinterResponse.model_validate(printer)


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a printer configuration."""
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )
    await db.delete(printer)


@router.post("/{printer_id}/test")
async def test_printer_connection(
    printer_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, str | bool]:
    """Test connection to a printer."""
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    from app.printing import get_driver

    try:
        driver = get_driver(printer)
        success = await driver.test_connection()
        return {
            "success": success,
            "message": "Connection successful" if success else "Connection failed",
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


@router.post("/{printer_id}/print")
async def print_label(
    printer_id: UUID,
    label_data: LabelData,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, str | bool]:
    """Print a label for a container."""
    # Get printer
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    # Get container
    result = await db.execute(
        select(Container).where(Container.id == label_data.container_id)
    )
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Get location
    result = await db.execute(
        select(Location).where(Location.id == container.location_id)
    )
    location = result.scalar_one()

    # Determine template - use explicit template or fall back to legacy behavior
    template = label_data.template
    if template == LabelTemplate.QR_ONLY and label_data.include_contents:
        # Legacy compatibility: include_contents implies at least summary
        template = LabelTemplate.QR_AI_SUMMARY

    # Build label content based on template
    label_content = await build_label_content(db, container, location, template)

    # Print
    try:
        driver = get_driver(printer)
        success = await driver.print_label(label_content)
        return {
            "success": success,
            "message": "Label printed successfully" if success else "Print failed",
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


@router.get("/{printer_id}/download")
async def download_label(
    printer_id: UUID,
    container_id: UUID,
    template: LabelTemplate = Query(default=LabelTemplate.QR_ONLY),
    db: DbSession = None,
) -> Response:
    """Download a label as PDF file."""
    from app.models.printer import PrinterTypeEnum
    from app.printing.pdf_generator import PDFLabelDriver

    # Get printer
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    # Get container
    result = await db.execute(select(Container).where(Container.id == container_id))
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Get location
    result = await db.execute(
        select(Location).where(Location.id == container.location_id)
    )
    location = result.scalar_one()

    # Build label content
    label_content = await build_label_content(db, container, location, template)

    # Generate PDF using the PDF driver
    pdf_driver = PDFLabelDriver(
        address="download",
        label_width_mm=printer.label_width_mm,
        label_height_mm=printer.label_height_mm,
    )
    pdf_bytes = await pdf_driver.generate_pdf([label_content])

    # Create a safe filename
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in container.name)
    filename = f"label_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{printer_id}/preview")
async def preview_label(
    printer_id: UUID,
    container_id: UUID,
    template: LabelTemplate = Query(default=LabelTemplate.QR_ONLY),
    include_contents: bool = False,  # Legacy parameter
    db: DbSession = None,
) -> Response:
    """Generate a preview image of a label."""
    # Get printer
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    # Get container
    result = await db.execute(select(Container).where(Container.id == container_id))
    container = result.scalar_one_or_none()
    if not container:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Container not found",
        )

    # Get location
    result = await db.execute(
        select(Location).where(Location.id == container.location_id)
    )
    location = result.scalar_one()

    # Determine template - use explicit template or fall back to legacy behavior
    effective_template = template
    if template == LabelTemplate.QR_ONLY and include_contents:
        # Legacy compatibility
        effective_template = LabelTemplate.QR_AI_SUMMARY

    # Build label content based on template
    label_content = await build_label_content(db, container, location, effective_template)

    # Generate preview
    driver = get_driver(printer)
    image_bytes = await driver.generate_preview(label_content)

    return Response(content=image_bytes, media_type="image/png")


@router.get("/{printer_id}/media", response_model=MediaSuggestion)
async def detect_printer_media(
    printer_id: UUID,
    db: DbSession,
) -> MediaSuggestion:
    """Detect media loaded in the printer and suggest appropriate template.

    Queries the printer for currently loaded label media and returns
    dimensions along with a suggested template based on label size.
    """
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    driver = get_driver(printer)
    detected = await driver.detect_media()

    # Convert to response model
    detected_response = DetectedMediaResponse(
        supported=detected.supported,
        width_mm=detected.width_mm,
        height_mm=detected.height_mm,
        media_type=detected.media_type,
        printer_status=detected.printer_status,
        error_message=detected.error_message,
    )

    # Get suggestion
    suggested_template, confidence, reason = suggest_template_for_media(
        detected.width_mm, detected.height_mm
    )

    # Calculate suggested dimensions
    suggested_width = detected.width_mm if detected.width_mm else printer.label_width_mm
    suggested_height = (
        detected.height_mm
        if detected.height_mm and detected.height_mm > 0
        else printer.label_height_mm
    )

    return MediaSuggestion(
        detected=detected_response,
        suggested_template=suggested_template,
        suggested_width_mm=suggested_width,
        suggested_height_mm=suggested_height,
        confidence=confidence,
        reason=reason,
    )


@router.post("/{printer_id}/print-batch", response_model=BatchPrintResult)
async def print_batch(
    printer_id: UUID,
    batch_data: BatchLabelData,
    db: DbSession,
    current_user: CurrentUser,
) -> BatchPrintResult:
    """Print labels for multiple containers.

    Used for batch printing from God View.
    """
    # Get printer
    result = await db.execute(select(Printer).where(Printer.id == printer_id))
    printer = result.scalar_one_or_none()
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found",
        )

    driver = get_driver(printer)
    results = []
    success_count = 0
    failed_count = 0

    for container_id in batch_data.container_ids:
        try:
            # Get container
            result = await db.execute(
                select(Container).where(Container.id == container_id)
            )
            container = result.scalar_one_or_none()
            if not container:
                results.append({
                    "container_id": str(container_id),
                    "success": False,
                    "message": "Container not found",
                })
                failed_count += 1
                continue

            # Get location
            result = await db.execute(
                select(Location).where(Location.id == container.location_id)
            )
            location = result.scalar_one()

            # Build and print label
            label_content = await build_label_content(
                db, container, location, batch_data.template
            )
            success = await driver.print_label(label_content)

            if success:
                success_count += 1
                results.append({
                    "container_id": str(container_id),
                    "container_name": container.name,
                    "success": True,
                    "message": "Printed successfully",
                })
            else:
                failed_count += 1
                results.append({
                    "container_id": str(container_id),
                    "container_name": container.name,
                    "success": False,
                    "message": "Print failed",
                })

        except Exception as e:
            failed_count += 1
            results.append({
                "container_id": str(container_id),
                "success": False,
                "message": str(e),
            })

    return BatchPrintResult(
        total=len(batch_data.container_ids),
        success=success_count,
        failed=failed_count,
        results=results,
    )
