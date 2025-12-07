# StorageHub - System Description

## Overview

StorageHub is a comprehensive inventory management system designed for households, small businesses, or anyone who needs to organize and track their belongings across multiple storage locations. The system uses a hierarchical organization structure with AI-powered features for automatic item classification and semantic search.

## Architecture

### Technology Stack

**Backend:**
- Python 3.11 with FastAPI
- PostgreSQL 16 database
- Redis for caching and task queues
- Celery for background task processing
- SQLAlchemy ORM with async support

**Frontend:**
- SvelteKit with TypeScript
- Tailwind CSS for styling
- Progressive Web App (PWA) capabilities

**AI Services:**
- OpenAI Vision API for item classification
- FastSAM for image segmentation
- Replicate API (alternative segmentation provider)

**Infrastructure:**
- Docker Compose orchestration
- Nginx reverse proxy
- Let's Encrypt SSL support

---

## Core Data Model

### Hierarchy Structure

```
Locations (e.g., "Garage", "Attic", "Storage Unit")
    └── Containers (e.g., "Box 1", "Blue Bin")
            └── Containers (nested, e.g., "Small Box inside Box 1")
            └── Items (e.g., "Winter Jacket", "Christmas Decorations")
```

### Entity Relationships

#### Location
The top-level organizational unit representing a physical storage area.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Location name |
| description | Text | Optional description |
| address | String | Physical address |
| sort_order | Integer | Display ordering |

#### Container
A storage unit (box, bin, shelf) that holds items or other containers.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Container name |
| qr_code | String | Auto-generated unique QR code |
| notes | Text | Optional notes |
| location_id | UUID | Parent location |
| parent_container_id | UUID | Optional parent container (for nesting) |

#### Item
An individual belonging stored in a container.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Item name |
| description | Text | Manual description |
| size | String | Size information |
| condition | Enum | GOOD, FAIR, DAMAGED, NEEDS_REPAIR |
| seasonal | Enum | NONE, SPRING, SUMMER, FALL, WINTER, HOLIDAY |
| value_estimate | Decimal | Estimated value |
| owner_id | UUID | Owner (user) |
| container_id | UUID | Parent container |
| ai_name | String | AI-generated name (English) |
| ai_name_no | String | AI-generated name (Norwegian) |
| ai_description | Text | AI-generated description (English) |
| ai_description_no | Text | AI-generated description (Norwegian) |
| ai_tags | JSON | AI-generated tags |
| ai_processed | Boolean | Whether AI has processed this item |
| needs_review | Boolean | Flagged for user review |
| primary_image_id | UUID | Hero image selection |

#### ItemImage
Images attached to items.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| item_id | UUID | Parent item |
| filename | String | Original filename |
| filepath | String | Storage path |

#### User
System users with authentication.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Display name |
| email | String | Unique email |
| role | Enum | ADMIN, USER |
| language | Enum | EN, NO |
| avatar_url | String | Profile picture |
| password_hash | String | Argon2 hashed password |
| is_active | Boolean | Account status |

#### Tag
Labels for organizing items.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Unique tag name |

#### ShareLink
Public access tokens for sharing containers.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| container_id | UUID | Shared container |
| user_id | UUID | Creator |
| token | String | Public access token |
| is_active | Boolean | Link status |
| show_items | Boolean | Whether to show items |
| expires_at | DateTime | Optional expiration |
| view_count | Integer | Access counter |

#### Reminder
Scheduled alerts and tasks.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| item_id | UUID | Optional linked item |
| container_id | UUID | Optional linked container |
| user_id | UUID | Owner |
| title | String | Reminder title |
| description | Text | Details |
| reminder_type | Enum | CHECK_ITEM, EXPIRATION, MAINTENANCE, RESTOCK, CUSTOM |
| due_date | DateTime | When due |
| is_recurring | Boolean | Repeats |
| recurrence_days | Integer | Days between recurrences |
| is_completed | Boolean | Completion status |
| completed_at | DateTime | When completed |

#### Printer
Label printer configurations.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Printer name |
| printer_type | Enum | ZEBRA_ZPL, BROTHER_QL, GENERIC_PDF |
| connection_type | Enum | NETWORK, USB, FILE |
| address | String | Network address or path |
| port | Integer | Network port |
| label_width_mm | Integer | Label width |
| label_height_mm | Integer | Label height |
| is_default | Boolean | Default printer flag |

#### ActivityLog
Audit trail for all changes.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Who made the change |
| action | Enum | CREATED, UPDATED, DELETED, MOVED |
| entity_type | String | What was changed |
| entity_id | UUID | ID of changed entity |
| entity_name | String | Name at time of change |
| old_values | JSON | Previous values |
| new_values | JSON | New values |
| created_at | DateTime | When it happened |

---

## Feature Modules

### 1. Inventory Management

**Locations:**
- Create, edit, delete storage locations
- View all containers within a location
- Statistics (container count, item count)

**Containers:**
- Nested container support (boxes within boxes)
- Automatic QR code generation
- Path breadcrumbs showing full hierarchy
- Smart deletion with three modes:
  - **Fail**: Prevent deletion if contents exist
  - **Recursive**: Delete container and all contents
  - **Transfer**: Move contents to another container first

**Items:**
- Full CRUD operations
- Multiple image support with primary image selection
- Condition tracking (Good, Fair, Damaged, Needs Repair)
- Seasonal classification
- Value estimation
- Owner assignment
- Tag management (manual and AI-generated)
- Move between containers

### 2. AI-Powered Features

**Image Classification:**
- Automatic tag generation from uploaded images
- AI-generated names and descriptions
- Bilingual support (English and Norwegian)
- Background processing via Celery workers
- Reprocessing capability for updated results

**Image Segmentation:**
- Upload a single image containing multiple items
- AI detects and segments individual objects
- Creates separate items for each detected object
- Review workflow for AI-created items
- Two providers: Local FastSAM or Replicate API

**Semantic Search:**
- Natural language queries ("red dress size 104")
- Color synonym understanding (emerald → green)
- Item type synonyms (cardigan → sweater)
- Owner name matching
- Relevance-based ranking:
  - Exact matches in name: 100 points
  - Description matches: 50 points
  - Owner matches: 40 points
  - Color matches: 30 points
  - Tag matches: 10-15 points
- Autocomplete suggestions

### 3. QR Code System

**Generation:**
- Every container automatically gets a unique QR code
- QR codes are URL-based for easy scanning
- Codes persist across container updates

**Scanning:**
- Built-in QR scanner in the app
- Direct navigation to scanned container
- Mobile-optimized camera interface

**Printing:**
- Print QR code labels
- Multiple printer support (Zebra, Brother, PDF)
- Customizable label sizes
- Contents summary on labels

### 4. Sharing System

**Share Links:**
- Create public links for containers
- Token-based access (no login required)
- Configurable options:
  - Active/inactive toggle
  - Expiration dates
  - Show/hide items
- View count tracking
- Revocable at any time

### 5. Reminder System

**Reminder Types:**
- CHECK_ITEM: Periodic item checks
- EXPIRATION: Expiring items (food, medications)
- MAINTENANCE: Maintenance schedules
- RESTOCK: Inventory replenishment
- CUSTOM: User-defined reminders

**Features:**
- Link to specific items or containers
- Recurring reminders with configurable intervals
- Completion tracking
- Overdue detection
- Upcoming reminder views

### 6. God View (Inventory Tree)

**Features:**
- Complete hierarchy visualization
- Inline editing of all fields
- Drag-and-drop item movement
- Expand/collapse all controls
- Location and container filters
- Create containers/locations inline
- Bulk operations support

### 7. Admin Panel

**User Management:**
- Create/edit/delete users
- Role assignment (Admin/User)
- Password management
- Avatar uploads

**System Statistics:**
- Total users, locations, containers, items
- Recent activity counts
- Growth metrics (30-day)

**Activity Logs:**
- Complete audit trail
- Filter by user, action, entity type
- Old/new value comparison

**AI Configuration:**
- Segmentation provider selection
- Service health monitoring
- Enable/disable features

### 8. Data Export

**JSON Export:**
- Complete data dump
- Includes all relationships
- Suitable for backup/migration

**CSV Export:**
- Item-focused spreadsheet
- Includes location, container, tags
- Excel-compatible

### 9. Printer Integration

**Supported Printers:**
- Zebra ZPL (thermal label printers)
- Brother QL (label makers)
- Generic PDF (any printer)

**Connection Types:**
- Network (IP address)
- USB (direct connection)
- File (save to path)

**Features:**
- Connection testing
- Label preview
- Custom label sizes
- QR code + text labels

### 10. Security & Authentication

**Authentication:**
- Session-based authentication
- Argon2 password hashing
- Optional passwordless accounts

**Authorization:**
- Role-based access (Admin/User)
- Admin-only endpoints protected
- Public share links for unauthenticated access

**SSL/TLS:**
- Self-signed certificate generation
- Let's Encrypt integration
- Auto-renewal support

---

## API Structure

### Base URL
All API endpoints are prefixed with `/api/`

### Authentication
Most endpoints require authentication via session cookie. Public endpoints:
- `GET /api/shares/public/{token}` - View shared containers
- `GET /api/health` - Health check

### Main Endpoint Groups

| Prefix | Description |
|--------|-------------|
| `/api/auth` | Authentication (login, logout, current user) |
| `/api/users` | User management |
| `/api/locations` | Location CRUD |
| `/api/containers` | Container CRUD, QR codes |
| `/api/items` | Item CRUD, images, tags |
| `/api/tags` | Tag management |
| `/api/search` | Search and autocomplete |
| `/api/reminders` | Reminder management |
| `/api/shares` | Share link management |
| `/api/printers` | Printer configuration |
| `/api/inventory` | God View tree data |
| `/api/uploads` | Image upload and segmentation |
| `/api/activity` | Activity logs |
| `/api/export` | Data export |
| `/api/admin` | Admin operations |
| `/api/ssl` | SSL configuration |

---

## Background Processing

### Celery Queues

| Queue | Purpose |
|-------|---------|
| celery | Default queue |
| ai | AI processing tasks |
| segmentation | Image segmentation |
| default | General tasks |

### Task Types

- **process_item_image**: AI classification of uploaded images
- **segment_image**: Object detection and segmentation
- **create_items_from_segments**: Item creation from segmented objects

---

## File Storage

### Upload Directory Structure
```
uploads/
├── temp/                    # Temporary uploads for segmentation
├── 2025/
│   └── 12/
│       └── {item_id}/
│           ├── {image_id}.jpg
│           └── {image_id}.png
```

### Image URLs
Images are served via nginx at `/uploads/{filepath}`

---

## Internationalization

### Supported Languages
- English (en) - Default
- Norwegian (no)

### Localized Content
- UI strings (frontend i18n)
- AI-generated names and descriptions
- User language preference

---

## Deployment

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy |
| frontend | 3000 | SvelteKit app |
| backend | 8000 | FastAPI server |
| postgres | 5432 | Database |
| redis | 6379 | Cache/queue |
| celery | - | Background workers |
| fastsam | 8001 | Segmentation service |

### Environment Variables

Key configuration via environment:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - For AI features
- `REPLICATE_API_TOKEN` - Alternative AI provider
- `SECRET_KEY` - Session encryption
- `UPLOAD_DIR` - File storage path

---

## Database Migrations

Managed via Alembic. Current migrations:
1. Initial schema
2. Add printers table
3. Add reminders and share_links
4. Add user language preference
5. Add file connection type for printers
6. Add SSL configuration
7. Add AI fields to items
8. Add segmentation support
9. Add Norwegian AI fields
10. Add primary_image_id to items

Run migrations: `alembic upgrade head`
