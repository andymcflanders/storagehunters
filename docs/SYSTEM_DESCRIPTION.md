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
| container_type | String | Optional category — `box`, `drawer`, `shelf`, `cabinet`, `closet`, `bin`, `basket`, `other` |
| image_filepath | Text | Optional hero image (relative path under `upload_dir`); served as `image_url` in API responses |

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
| ai_names | JSONB | AI-generated names keyed by ISO language code, e.g. `{"en": "Red Sweater", "no": "Rød Genser"}` |
| ai_descriptions | JSONB | AI-generated descriptions keyed by ISO language code |
| ai_processed | Boolean | Whether AI has processed this item |
| needs_review | Boolean | Flagged for user review (kept for godview filter / Home Assistant stats; no UI sets it after the segmentation feature was removed) |
| primary_image_id | UUID | Hero image selection |

> Tags are still English-only by design — they're categorical labels, not
> user-facing prose. AI-generated tags live on `ItemImage.ai_tags` (see below).

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

#### AISettings
Configuration for OpenAI and language settings (singleton table).

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| vision_model | String | Model for image classification (default: gpt-4o) |
| vision_max_tokens | Integer | Max response tokens (default: 500) |
| vision_temperature | Float | Model temperature (default: 0.3) |
| vision_enabled | Boolean | Enable vision classification |
| summary_model | String | Model for summaries (default: gpt-4o-mini) |
| summary_max_tokens | Integer | Max summary tokens (default: 150) |
| summary_temperature | Float | Summary temperature (default: 0.3) |
| summary_enabled | Boolean | Enable AI summaries |
| supported_languages | String[] | ISO codes the AI generates content in (default: `{en, no}`). Add `de`, `sv`, etc. to extend; the OpenAI prompt is built dynamically from this list |
| default_language | String | Fallback language when a translation is missing for the user's locale (default: `en`) |
| openai_api_key | Text | Persisted API key. Wins over the `OPENAI_API_KEY` env var, which stays as a fallback for un-onboarded installs |

#### BackupConfig
Configuration for automatic backups (singleton table).

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| enabled | Boolean | Enable automatic backups |
| frequency_hours | Integer | Hours between backups |
| retention_count | Integer | Number of backups to keep |
| google_drive_enabled | Boolean | Sync to Google Drive |
| google_credentials | JSON | OAuth credentials (encrypted) |
| last_backup_at | DateTime | Last successful backup time |

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
- AI-generated names and descriptions in every language listed under
  `AISettings.supported_languages` (defaults to English + Norwegian; admins
  can add more without a code change). Translations are stored as JSONB
  dicts on `Item.ai_names` and `Item.ai_descriptions` keyed by ISO code,
  and the OpenAI prompt is built dynamically from the language list.
- Background processing via Celery workers
- Reprocessing capability for updated results

**Configurable AI Models:**
- Vision model selection (gpt-4o, gpt-4o-mini, gpt-4-turbo)
- Summary model selection
- Adjustable max tokens and temperature
- Real-time cost estimation per operation
- Settings stored in database with caching

**Container Summaries:**
- AI-generated content descriptions for labels
- Considers item owners, seasons, and categories
- Configurable model and parameters

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

**First-run Setup Wizard:**
- A clean install (empty users table) auto-redirects to `/setup`
- Steps: welcome → admin account (email + password required) →
  OpenAI key + AI languages (skippable) → first location (skippable) → done
- `POST /api/setup/complete` is one-shot — returns 409 once any user exists,
  so the public endpoint can't be re-used to inject a second admin

**Identity Separation:**
- Admins are excluded from the household card grid on `/login` (the page
  calls `GET /api/users?include_admins=false`)
- Admins sign in via the "Administer this instance" link with email +
  password (`POST /api/auth/login` with `{email, password}`)

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
- OpenAI model selection (vision and summary)
- Persisted API key (rotatable from the panel; survives container restart)
- Supported AI languages and default fallback
- Per-feature enable/disable toggles
- Cost estimate display

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

### 11. Backup & Restore System

**Manual Backups:**
- Create database dumps on demand
- Download backups as compressed archives
- View backup history with timestamps and sizes

**Automatic Backups:**
- Configurable backup frequency (hourly to weekly)
- Retention policy (number of backups to keep)
- Runs via Celery beat scheduler

**Google Drive Integration:**
- OAuth-based authentication
- Automatic upload after backup completion
- List and manage cloud backups
- Sync backup deletions

**Restore Operations:**
- Point-in-time restore from any backup
- Full database replacement
- Automatic service restart after restore

---

## API Structure

### Base URL
All API endpoints are prefixed with `/api/`

### Authentication
Most endpoints require authentication via session cookie. Public endpoints:
- `GET /api/shares/public/{token}` - View shared containers
- `GET /api/health` - Health check
- `GET /api/setup/status` - First-run probe (returns `{needs_setup: bool}`)
- `POST /api/setup/complete` - One-shot bootstrap; refuses with 409 once any user exists

`POST /api/auth/login` accepts either `user_id` (household card-tap login) or
`email` (admin sign-in via the "Administer this instance" link). Email lookup
is case-insensitive.

`GET /api/users` accepts `?include_admins=false` so the login screen can hide
admins from the household card grid.

### Main Endpoint Groups

| Prefix | Description |
|--------|-------------|
| `/api/setup` | First-run wizard — `status` (public) and `complete` (public, one-shot) |
| `/api/auth` | Authentication (login by user_id or email, logout, current user) |
| `/api/users` | User management; `?include_admins=false` filters admins out of the list |
| `/api/locations` | Location CRUD |
| `/api/containers` | Container CRUD, QR codes, hero image upload (`POST /{id}/image`, `DELETE /{id}/image`) |
| `/api/items` | Item CRUD, images, tags |
| `/api/tags` | Tag management |
| `/api/search` | Search and autocomplete (matches across `ai_names`/`ai_descriptions` JSONB so Norwegian queries hit English-only items and vice versa) |
| `/api/reminders` | Reminder management |
| `/api/shares` | Share link management |
| `/api/printers` | Printer configuration |
| `/api/inventory` | God View tree data |
| `/api/activity` | Activity logs |
| `/api/export` | Data export |
| `/api/admin` | Admin operations (users, stats, activity logs) |
| `/api/admin/openai` | OpenAI model configuration + persisted API key |
| `/api/admin/languages` | Manage `supported_languages` / `default_language` |
| `/api/admin/ssl` | SSL certificate management |
| `/api/api-keys` | Long-lived API keys (used by the Home Assistant integration) |
| `/api/webhooks` | Webhook subscription management |
| `/api/ha` | Home Assistant integration endpoints (API-key auth) |
| `/api/backup` | Backup and restore operations |

---

## Background Processing

### Celery Queues

| Queue | Purpose |
|-------|---------|
| celery | Default queue |
| ai | AI processing tasks |
| default | General tasks |

### Task Types

- **process_item_image**: AI classification of uploaded images
- **create_backup**: Create database backup
- **cleanup_old_backups**: Remove backups exceeding retention limit
- **upload_backup_to_drive**: Sync backup to Google Drive

---

## File Storage

### Upload Directory Structure
```
uploads/
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

### UI translation
The frontend ships locale files under `frontend/src/lib/i18n/locales/`. English
(`en.json`) and Norwegian (`no.json`) are bundled today; adding another locale
is a matter of dropping a JSON file with the same shape and registering it in
`frontend/src/lib/i18n/index.ts`. The user's `language` field on the User
model selects which locale loads.

### AI-generated content
AI translation languages are governed by `AISettings.supported_languages`
(JSONB list of ISO codes) and `default_language` — both editable from
Admin → AI Settings or from the first-run wizard. The OpenAI prompt iterates
this list, so adding `de` or `sv` to it makes the next item ingestion
generate German or Swedish names and descriptions automatically. Existing
items are not back-translated; reprocess them if you need older items in the
new language.

`getLocalizedAI()` on the frontend (and `app.services.localized.localized()`
on the backend) resolve a translations dict to a single string with the
order: user's language → `default_language` → any value present.

### Where each language is constrained
- **`User.language` enum**: currently restricted to `en` / `no` (both have
  shipped UI locale files). Add to the enum + ship a locale file to extend.
- **`AISettings.supported_languages`**: free-form list. Adding a code here
  only affects AI generation, not the UI strings the user sees.

---

## Deployment

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy. Auto-generates a self-signed cert on first boot so HTTPS works without setup |
| frontend | 3000 | SvelteKit app (Node 20 SSR adapter) |
| backend | 8000 | FastAPI server |
| postgres | 5432 | Database (PostgreSQL 16) |
| redis | 6379 | Cache / Celery broker |
| celery | - | Background workers (queues: `celery`, `ai`, `default`) |
| celery-beat | - | Scheduled tasks (e.g. backup runner) |
| certbot | - | On-demand Let's Encrypt cert helper |

### Environment Variables

Required (compose refuses to start without them — `${VAR:?...}` interpolation):
- `SECRET_KEY` — session/JWT signing. Generate with `openssl rand -hex 32` or `just genkey`.
- `POSTGRES_PASSWORD` — database password.

Recommended:
- `OPENAI_API_KEY` — pre-fills the wizard. The wizard / admin panel can also
  store the key in `ai_settings.openai_api_key`, which takes precedence over
  this env var.
- `FRONTEND_URL` — public URL used in QR codes and share links.
- `CORS_ORIGINS` — comma-separated additional origins.

Internal (set by compose):
- `DATABASE_URL`, `REDIS_URL`, `UPLOAD_DIR`

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
11. Add API keys and webhooks
12. Add backup_config table
13. Add ai_settings table (OpenAI configuration)
14. Remove segmentation feature
15. Switch AI translations to JSONB (`ai_names`, `ai_descriptions`) and add `supported_languages` / `default_language` to `ai_settings`
16. Add `container_type` and `image_filepath` to containers
17. Add `openai_api_key` to `ai_settings` (persisted across restarts)

Run migrations: `alembic upgrade head`
