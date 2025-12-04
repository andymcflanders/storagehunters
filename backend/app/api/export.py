"""Data export API routes."""

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.container import Container
from app.models.item import Item, ItemImage, ItemTag
from app.models.location import Location
from app.models.tag import Tag

router = APIRouter()


@router.get("/json")
async def export_json(
    db: DbSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    """Export all data as JSON."""
    # Get all locations
    locations_result = await db.execute(select(Location).order_by(Location.name))
    locations = locations_result.scalars().all()

    # Get all containers
    containers_result = await db.execute(select(Container).order_by(Container.name))
    containers = containers_result.scalars().all()

    # Get all items with tags
    items_result = await db.execute(select(Item).order_by(Item.name))
    items = items_result.scalars().all()

    # Get item tags
    item_tags_result = await db.execute(select(ItemTag))
    item_tags = item_tags_result.scalars().all()
    item_tag_map: dict[str, list[str]] = {}

    # Get tag names
    tags_result = await db.execute(select(Tag))
    tags = {t.id: t.name for t in tags_result.scalars().all()}

    for it in item_tags:
        item_id = str(it.item_id)
        if item_id not in item_tag_map:
            item_tag_map[item_id] = []
        if it.tag_id in tags:
            item_tag_map[item_id].append(tags[it.tag_id])

    # Get item images
    images_result = await db.execute(select(ItemImage))
    images = images_result.scalars().all()
    item_image_map: dict[str, list[dict]] = {}
    for img in images:
        item_id = str(img.item_id)
        if item_id not in item_image_map:
            item_image_map[item_id] = []
        item_image_map[item_id].append({
            "filename": img.filename,
            "ai_tags": img.ai_tags or [],
            "ai_description": img.ai_description,
        })

    # Build export data
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": current_user.name,
        "locations": [
            {
                "id": str(loc.id),
                "name": loc.name,
                "description": loc.description,
                "address": loc.address,
            }
            for loc in locations
        ],
        "containers": [
            {
                "id": str(c.id),
                "name": c.name,
                "location_id": str(c.location_id),
                "parent_container_id": str(c.parent_container_id) if c.parent_container_id else None,
                "qr_code": c.qr_code,
                "notes": c.notes,
            }
            for c in containers
        ],
        "items": [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "container_id": str(item.container_id),
                "size": item.size,
                "condition": item.condition.value if item.condition else None,
                "seasonal": item.seasonal.value if item.seasonal else None,
                "value_estimate": item.value_estimate,
                "tags": item_tag_map.get(str(item.id), []),
                "images": item_image_map.get(str(item.id), []),
            }
            for item in items
        ],
    }

    # Create streaming response
    json_str = json.dumps(export_data, indent=2)

    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=storagehub_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        },
    )


@router.get("/csv")
async def export_csv(
    db: DbSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    """Export items as CSV."""
    # Get all items with related data
    items_result = await db.execute(select(Item).order_by(Item.name))
    items = items_result.scalars().all()

    # Get containers
    containers_result = await db.execute(select(Container))
    containers = {c.id: c for c in containers_result.scalars().all()}

    # Get locations
    locations_result = await db.execute(select(Location))
    locations = {loc.id: loc for loc in locations_result.scalars().all()}

    # Get item tags
    item_tags_result = await db.execute(select(ItemTag))
    item_tags = item_tags_result.scalars().all()

    tags_result = await db.execute(select(Tag))
    tags = {t.id: t.name for t in tags_result.scalars().all()}

    item_tag_map: dict[str, list[str]] = {}
    for it in item_tags:
        item_id = str(it.item_id)
        if item_id not in item_tag_map:
            item_tag_map[item_id] = []
        if it.tag_id in tags:
            item_tag_map[item_id].append(tags[it.tag_id])

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Item Name",
        "Description",
        "Container",
        "Location",
        "QR Code",
        "Size",
        "Condition",
        "Seasonal",
        "Value Estimate",
        "Tags",
    ])

    # Data rows
    for item in items:
        container = containers.get(item.container_id)
        location = locations.get(container.location_id) if container else None
        item_tags_list = item_tag_map.get(str(item.id), [])

        writer.writerow([
            item.name,
            item.description or "",
            container.name if container else "",
            location.name if location else "",
            container.qr_code if container else "",
            item.size or "",
            item.condition.value if item.condition else "",
            item.seasonal.value if item.seasonal else "",
            item.value_estimate or "",
            ", ".join(item_tags_list),
        ])

    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=storagehub_items_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )
