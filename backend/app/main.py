"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: ensure upload directory exists
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: cleanup if needed


DESCRIPTION = """
# StorageHub API

StorageHub is a self-hosted personal belongings tracker with AI-powered image recognition.

## Features

- **Inventory Management**: Organize items in locations and containers
- **AI Image Processing**: Automatic item detection and tagging
- **Semantic Search**: Natural language search for items
- **Multi-user Support**: Role-based access control
- **API Integration**: Full API for external integrations

## Home Assistant Integration

StorageHub provides a dedicated API for Home Assistant integration at `/api/ha/*`.

### Authentication

Use API keys for Home Assistant integration:
1. Create an API key in the web UI under Settings > API Keys
2. Include the key in requests using either:
   - `X-API-Key` header
   - `Authorization: Bearer <key>` header

### Available Scopes

- `read`: Read-only access to inventory data
- `write`: Create/update items and containers
- `search`: Search functionality
- `webhooks`: Manage webhooks
- `admin`: Full administrative access

## Webhooks

Subscribe to real-time events for Home Assistant automations:
- Item created/updated/deleted/moved
- Container created/updated/deleted
- Location created/updated/deleted
- Reminder due/overdue/completed
"""

app = FastAPI(
    title="StorageHub API",
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Home Assistant", "description": "Dedicated API for Home Assistant integration. Uses API key authentication."},
        {"name": "API Keys", "description": "Manage API keys for external integrations."},
        {"name": "Webhooks", "description": "Manage webhooks for real-time event notifications."},
        {"name": "Authentication", "description": "User authentication (session-based)."},
        {"name": "Locations", "description": "Manage storage locations (rooms, buildings, etc.)."},
        {"name": "Containers", "description": "Manage storage containers (boxes, bins, shelves)."},
        {"name": "Items", "description": "Manage individual items in your inventory."},
        {"name": "Search", "description": "Search for items with AI-powered semantic search."},
        {"name": "Tags", "description": "Manage tags for item categorization."},
        {"name": "Reminders", "description": "Manage reminders for items and containers."},
        {"name": "Activity", "description": "View activity logs and audit trail."},
        {"name": "Shares", "description": "Manage public share links for containers."},
        {"name": "Inventory", "description": "Bulk inventory operations and God View."},
        {"name": "Users", "description": "User management."},
        {"name": "Printers", "description": "Printer configuration for QR labels."},
        {"name": "Export", "description": "Export inventory data."},
        {"name": "Uploads", "description": "Image upload and AI processing."},
        {"name": "SSL", "description": "SSL/TLS certificate management."},
    ],
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",  # Docker with nginx
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
uploads_path = Path(settings.upload_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
