/**
 * Technical documentation content.
 * Each section contains markdown content for the documentation.
 */

import type { DocSection } from './user-guide';

export const technicalSections: DocSection[] = [
	{
		id: 'architecture',
		titleKey: 'docs.technical.architecture.title',
		content: `
## Architecture Overview

StorageHub is built with a modern, scalable architecture designed for reliability and performance.

### Technology Stack

**Frontend:**
- **SvelteKit**: Full-stack web framework
- **Svelte 4**: Reactive UI framework
- **TypeScript**: Type-safe JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **svelte-i18n**: Internationalization

**Backend:**
- **Python**: Core backend language
- **FastAPI**: High-performance async API framework
- **SQLAlchemy**: SQL toolkit and ORM
- **SQLite**: Embedded database (default)
- **PostgreSQL**: Production database (optional)

**Infrastructure:**
- **Docker**: Containerization
- **Nginx**: Reverse proxy (production)
- **systemd**: Service management

### System Architecture

\`\`\`
┌─────────────────────────────────────────────────────────┐
│                     Client Browser                       │
│                   (SvelteKit SPA)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────┐
│                   Nginx Reverse Proxy                    │
│              (SSL Termination, Static Files)             │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼───────┐           ┌───────▼───────┐
│   Frontend    │           │    Backend    │
│   (Node.js)   │           │   (FastAPI)   │
│   Port 3000   │           │   Port 8000   │
└───────────────┘           └───────┬───────┘
                                    │
                            ┌───────▼───────┐
                            │   Database    │
                            │   (SQLite/    │
                            │  PostgreSQL)  │
                            └───────────────┘
\`\`\`

### Key Services

**Authentication Service:**
- Session-based authentication
- Password hashing with bcrypt
- Role-based access control (Admin/User)

**Storage Service:**
- Hierarchical data management
- Image upload and processing
- QR code generation

**AI Service:**
- OpenAI API integration
- Image classification
- Object segmentation

**Print Service:**
- Label generation
- Printer communication
- Template rendering
`
	},
	{
		id: 'database',
		titleKey: 'docs.technical.database.title',
		content: `
## Database Models

StorageHub uses a relational database with the following entity relationships.

### Entity Relationship Diagram

\`\`\`
┌──────────┐       ┌────────────┐       ┌──────────┐
│   User   │       │  Location  │       │   Tag    │
├──────────┤       ├────────────┤       ├──────────┤
│ id       │───┐   │ id         │       │ id       │
│ name     │   │   │ name       │       │ name     │
│ password │   │   │ address    │       │ color    │
│ role     │   │   │ user_id    │◄──┐   │ user_id  │
│ language │   │   │ created_at │   │   └──────────┘
└──────────┘   │   └────────────┘   │
               │          │         │
               │          │         │
               │   ┌──────▼─────┐   │
               │   │ Container  │   │
               │   ├────────────┤   │
               │   │ id         │   │
               └──►│ user_id    │   │
                   │ name       │   │
                   │ type       │   │
                   │ location_id│◄──┤
                   │ parent_id  │◄──┼─── (self-reference)
                   │ qr_code    │   │
                   └────────────┘   │
                          │         │
                   ┌──────▼─────┐   │
                   │    Item    │   │
                   ├────────────┤   │
                   │ id         │   │
                   │ user_id    │◄──┘
                   │ name       │
                   │ description│
                   │ quantity   │
                   │ condition  │
                   │ container_id
                   │ photos     │
                   └────────────┘
\`\`\`

### User Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Display name |
| password_hash | String(255) | Bcrypt hash (nullable) |
| role | Enum | 'admin' or 'user' |
| language | String(5) | Preferred language |
| is_active | Boolean | Account status |
| created_at | DateTime | Creation timestamp |
| last_login | DateTime | Last login timestamp |

### Location Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(200) | Location name |
| address | String(500) | Physical address |
| user_id | Integer | Foreign key to User |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Container Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(200) | Container name |
| description | Text | Optional description |
| type | Enum | Container type |
| location_id | Integer | Foreign key to Location |
| parent_id | Integer | Self-referential FK (nullable) |
| user_id | Integer | Foreign key to User |
| qr_code | String(100) | Unique QR code identifier |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Item Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(200) | Item name |
| description | Text | Optional description |
| quantity | Integer | Number of items |
| condition | Enum | Item condition |
| purchase_date | Date | When purchased |
| purchase_price | Decimal | Cost |
| seasonal | Enum | Seasonal category |
| container_id | Integer | Foreign key to Container |
| user_id | Integer | Foreign key to User |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Tag Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(50) | Tag name |
| color | String(7) | Hex color code |
| user_id | Integer | Foreign key to User |

### ItemTag (Junction Table)

| Column | Type | Description |
|--------|------|-------------|
| item_id | Integer | Foreign key to Item |
| tag_id | Integer | Foreign key to Tag |

### ItemPhoto Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| item_id | Integer | Foreign key to Item |
| filename | String(255) | Stored filename |
| original_name | String(255) | Original filename |
| mime_type | String(50) | File MIME type |
| size | Integer | File size in bytes |
| created_at | DateTime | Upload timestamp |

### ShareLink Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| token | String(100) | Unique share token |
| container_id | Integer | FK to Container (nullable) |
| location_id | Integer | FK to Location (nullable) |
| allow_item_view | Boolean | Show items flag |
| expires_at | DateTime | Expiration (nullable) |
| view_count | Integer | Access counter |
| created_by | Integer | Foreign key to User |
| created_at | DateTime | Creation timestamp |

### Reminder Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String(200) | Reminder title |
| description | Text | Optional details |
| due_date | DateTime | When due |
| is_recurring | Boolean | Repeat flag |
| recurrence_pattern | String(50) | Cron-like pattern |
| is_completed | Boolean | Completion status |
| item_id | Integer | FK to Item (nullable) |
| container_id | Integer | FK to Container (nullable) |
| user_id | Integer | Foreign key to User |
| created_at | DateTime | Creation timestamp |

### Printer Model

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Printer name |
| printer_type | Enum | Zebra, Brother, PDF |
| connection_type | Enum | Network, USB, File |
| address | String(255) | Connection address |
| user_id | Integer | Foreign key to User |
| is_default | Boolean | Default printer flag |
| settings | JSON | Printer-specific config |
`
	},
	{
		id: 'api-overview',
		titleKey: 'docs.technical.apiOverview.title',
		content: `
## API Overview

StorageHub provides a RESTful API for all operations.

### Base URL

\`\`\`
Production: https://your-domain.com/api
Development: http://localhost:8000/api
\`\`\`

### Authentication

All API requests (except login) require authentication via session cookie.

**Login:**
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": 1,
  "password": "optional-password"
}
\`\`\`

**Response:**
\`\`\`json
{
  "user": {
    "id": 1,
    "name": "John",
    "role": "admin"
  },
  "message": "Login successful"
}
\`\`\`

The response sets an HTTP-only session cookie.

**Logout:**
\`\`\`http
POST /api/auth/logout
\`\`\`

### Request Format

- All request bodies should be JSON
- Use \`Content-Type: application/json\` header
- File uploads use \`multipart/form-data\`

### Response Format

All responses follow this structure:

**Success:**
\`\`\`json
{
  "data": { ... },
  "message": "Operation successful"
}
\`\`\`

**Error:**
\`\`\`json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
\`\`\`

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

### Rate Limiting

API requests are rate-limited:
- 100 requests per minute per user
- 1000 requests per hour per user

Exceeded limits return \`429 Too Many Requests\`.

### Pagination

List endpoints support pagination:

\`\`\`http
GET /api/items?page=1&per_page=20
\`\`\`

Response includes pagination metadata:
\`\`\`json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
\`\`\`
`
	},
	{
		id: 'api-endpoints',
		titleKey: 'docs.technical.apiEndpoints.title',
		content: `
## API Endpoints

Complete reference for all API endpoints.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/auth/users | List all users (for login screen) |
| POST | /api/auth/login | Authenticate user |
| POST | /api/auth/logout | End session |
| GET | /api/auth/me | Get current user |

### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/locations | List user's locations |
| POST | /api/locations | Create location |
| GET | /api/locations/{id} | Get location details |
| PUT | /api/locations/{id} | Update location |
| DELETE | /api/locations/{id} | Delete location |

**Create Location:**
\`\`\`json
POST /api/locations
{
  "name": "Home",
  "address": "123 Main St"
}
\`\`\`

### Containers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/containers | List all containers |
| POST | /api/containers | Create container |
| GET | /api/containers/{id} | Get container details |
| PUT | /api/containers/{id} | Update container |
| DELETE | /api/containers/{id} | Delete container |
| POST | /api/containers/{id}/move | Move container |
| GET | /api/containers/{id}/qr | Get QR code |

**Create Container:**
\`\`\`json
POST /api/containers
{
  "name": "Storage Box 1",
  "type": "box",
  "location_id": 1,
  "parent_id": null
}
\`\`\`

### Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/items | List all items |
| POST | /api/items | Create item |
| GET | /api/items/{id} | Get item details |
| PUT | /api/items/{id} | Update item |
| DELETE | /api/items/{id} | Delete item |
| POST | /api/items/{id}/move | Move item |
| POST | /api/items/{id}/photos | Upload photo |
| DELETE | /api/items/{id}/photos/{photo_id} | Delete photo |

**Create Item:**
\`\`\`json
POST /api/items
{
  "name": "Winter Jacket",
  "description": "Blue puffer jacket",
  "quantity": 1,
  "condition": "good",
  "container_id": 5,
  "tags": [1, 3]
}
\`\`\`

### Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/tags | List user's tags |
| POST | /api/tags | Create tag |
| PUT | /api/tags/{id} | Update tag |
| DELETE | /api/tags/{id} | Delete tag |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/search | Search all entities |

**Search Parameters:**
\`\`\`
GET /api/search?q=jacket&type=item&location=1&tag=3
\`\`\`

### Reminders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/reminders | List reminders |
| POST | /api/reminders | Create reminder |
| PUT | /api/reminders/{id} | Update reminder |
| DELETE | /api/reminders/{id} | Delete reminder |
| POST | /api/reminders/{id}/complete | Mark complete |

### Sharing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/share | Create share link |
| GET | /api/share/{token} | Access shared content |
| DELETE | /api/share/{id} | Delete share link |

### Printers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/printers | List printers |
| POST | /api/printers | Add printer |
| PUT | /api/printers/{id} | Update printer |
| DELETE | /api/printers/{id} | Delete printer |
| POST | /api/printers/{id}/test | Test print |
| POST | /api/print/label | Print label |
| POST | /api/print/batch | Batch print |

### AI Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/ai/classify | Classify image |
| POST | /api/ai/segment | Segment objects |
| POST | /api/ai/summarize | Summarize container |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/users | List all users |
| POST | /api/admin/users | Create user |
| PUT | /api/admin/users/{id} | Update user |
| DELETE | /api/admin/users/{id} | Delete user |
| GET | /api/admin/stats | System statistics |
| GET | /api/admin/activity | Activity logs |
| GET | /api/admin/settings | Get settings |
| PUT | /api/admin/settings | Update settings |
`
	}
];
