"""Printer API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.printer import Printer
from app.schemas.printer import LabelData, PrinterCreate, PrinterResponse, PrinterUpdate

router = APIRouter()


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
    from app.models.container import Container
    from app.models.location import Location
    from app.printing import get_driver
    from app.printing.base import LabelContent

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

    # Get location name
    result = await db.execute(
        select(Location).where(Location.id == container.location_id)
    )
    location = result.scalar_one()

    # Build content summary if requested
    contents_summary = None
    if label_data.include_contents:
        from app.models.item import Item

        result = await db.execute(
            select(Item.name).where(Item.container_id == container.id).limit(5)
        )
        items = result.scalars().all()
        if items:
            contents_summary = ", ".join(items)
            if len(items) == 5:
                contents_summary += "..."

    # Create label content
    label_content = LabelContent(
        container_name=container.name,
        container_qr_code=container.qr_code,
        location_name=location.name,
        contents_summary=contents_summary,
    )

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


@router.get("/{printer_id}/preview")
async def preview_label(
    printer_id: UUID,
    container_id: UUID,
    include_contents: bool = False,
    db: DbSession = None,
) -> Response:
    """Generate a preview image of a label."""
    from app.models.container import Container
    from app.models.location import Location
    from app.printing import get_driver
    from app.printing.base import LabelContent

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

    # Build content summary
    contents_summary = None
    if include_contents:
        from app.models.item import Item

        result = await db.execute(
            select(Item.name).where(Item.container_id == container.id).limit(5)
        )
        items = result.scalars().all()
        if items:
            contents_summary = ", ".join(items)

    # Create label content
    label_content = LabelContent(
        container_name=container.name,
        container_qr_code=container.qr_code,
        location_name=location.name,
        contents_summary=contents_summary,
    )

    # Generate preview
    driver = get_driver(printer)
    image_bytes = await driver.generate_preview(label_content)

    return Response(content=image_bytes, media_type="image/png")
