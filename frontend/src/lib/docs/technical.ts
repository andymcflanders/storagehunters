/**
 * Technical documentation content.
 * Each section's body is keyed by ISO language code (see DocSection in
 * ./user-guide). Code blocks, table headers, and JSON examples stay in
 * English regardless of locale — translating those would just create
 * confusion for developers consulting the actual API.
 */

import type { DocSection } from './user-guide';

export const technicalSections: DocSection[] = [
	{
		id: 'architecture',
		titleKey: 'docs.technical.architecture.title',
		content: {
			en: `
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

**Print Service:**
- Label generation
- Printer communication
- Template rendering
`,
			no: `
## Arkitekturoversikt

StorageHub er bygd med en moderne, skalerbar arkitektur designet for pålitelighet og ytelse.

### Teknologi

**Frontend:**
- **SvelteKit**: Fullstack-rammeverk for web
- **Svelte 4**: Reaktivt UI-rammeverk
- **TypeScript**: Typesikker JavaScript
- **TailwindCSS**: Utility-first CSS-rammeverk
- **svelte-i18n**: Internasjonalisering

**Backend:**
- **Python**: Hovedspråk på server
- **FastAPI**: Asynkront API-rammeverk med høy ytelse
- **SQLAlchemy**: SQL-verktøy og ORM
- **SQLite**: Innebygd database (standard)
- **PostgreSQL**: Produksjonsdatabase (valgfritt)

**Infrastruktur:**
- **Docker**: Containerisering
- **Nginx**: Reverse proxy (produksjon)
- **systemd**: Tjenestestyring

### Systemarkitektur

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

### Hovedtjenester

**Autentisering:**
- Sesjonsbasert autentisering
- Passord-hashing med bcrypt
- Rollebasert tilgangskontroll (admin/bruker)

**Lagring:**
- Hierarkisk datahåndtering
- Bildeopplasting og prosessering
- QR-kodegenerering

**AI:**
- OpenAI API-integrasjon
- Bildeklassifisering

**Utskrift:**
- Etikettgenerering
- Skriverkommunikasjon
- Malrendering
`
		}
	},
	{
		id: 'database',
		titleKey: 'docs.technical.database.title',
		content: {
			en: `
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
`,
			no: `
## Databasemodeller

StorageHub bruker en relasjonsdatabase med følgende entitetsforhold.

### Entitetsforholdsdiagram

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
                   │ parent_id  │◄──┼─── (selvreferanse)
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

> Kolonnenavn og typer holdes på engelsk siden de speiler det faktiske
> databaseskjemaet og koden.

### User-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| name | String(100) | Visningsnavn |
| password_hash | String(255) | Bcrypt-hash (kan være null) |
| role | Enum | 'admin' eller 'user' |
| language | String(5) | Foretrukket språk |
| is_active | Boolean | Kontostatus |
| created_at | DateTime | Opprettet |
| last_login | DateTime | Siste innlogging |

### Location-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| name | String(200) | Stedsnavn |
| address | String(500) | Fysisk adresse |
| user_id | Integer | Fremmednøkkel til User |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Container-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| name | String(200) | Beholdernavn |
| description | Text | Valgfri beskrivelse |
| type | Enum | Beholdertype |
| location_id | Integer | Fremmednøkkel til Location |
| parent_id | Integer | Selvreferanse (kan være null) |
| user_id | Integer | Fremmednøkkel til User |
| qr_code | String(100) | Unik QR-kode |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Item-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| name | String(200) | Gjenstandsnavn |
| description | Text | Valgfri beskrivelse |
| quantity | Integer | Antall |
| condition | Enum | Tilstand |
| purchase_date | Date | Kjøpsdato |
| purchase_price | Decimal | Pris |
| seasonal | Enum | Sesongkategori |
| container_id | Integer | Fremmednøkkel til Container |
| user_id | Integer | Fremmednøkkel til User |
| notes | Text | Notater |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Tag-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| name | String(50) | Etikettnavn |
| color | String(7) | Hex-fargekode |
| user_id | Integer | Fremmednøkkel til User |

### ItemTag (koblingstabell)

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| item_id | Integer | Fremmednøkkel til Item |
| tag_id | Integer | Fremmednøkkel til Tag |

### ItemPhoto-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| item_id | Integer | Fremmednøkkel til Item |
| filename | String(255) | Lagret filnavn |
| original_name | String(255) | Opprinnelig filnavn |
| mime_type | String(50) | MIME-type |
| size | Integer | Filstørrelse i byte |
| created_at | DateTime | Opplastet |

### ShareLink-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| token | String(100) | Unikt delingstoken |
| container_id | Integer | FK til Container (kan være null) |
| location_id | Integer | FK til Location (kan være null) |
| allow_item_view | Boolean | Vis gjenstander |
| expires_at | DateTime | Utløp (kan være null) |
| view_count | Integer | Antall visninger |
| created_by | Integer | Fremmednøkkel til User |
| created_at | DateTime | Opprettet |

### Reminder-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| title | String(200) | Påminnelsestittel |
| description | Text | Valgfrie detaljer |
| due_date | DateTime | Forfallsdato |
| is_recurring | Boolean | Gjentakende |
| recurrence_pattern | String(50) | Cron-lignende mønster |
| is_completed | Boolean | Fullført |
| item_id | Integer | FK til Item (kan være null) |
| container_id | Integer | FK til Container (kan være null) |
| user_id | Integer | Fremmednøkkel til User |
| created_at | DateTime | Opprettet |

### Printer-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | Integer | Primærnøkkel |
| name | String(100) | Skrivernavn |
| printer_type | Enum | Zebra, Brother, PDF |
| connection_type | Enum | Network, USB, File |
| address | String(255) | Tilkoblingsadresse |
| user_id | Integer | Fremmednøkkel til User |
| is_default | Boolean | Standardskriver |
| settings | JSON | Skriverkonfigurasjon |
`
		}
	},
	{
		id: 'api-overview',
		titleKey: 'docs.technical.apiOverview.title',
		content: {
			en: `
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
`,
			no: `
## API-oversikt

StorageHub har et REST-API for alle operasjoner.

### Base-URL

\`\`\`
Produksjon:  https://din-domene.no/api
Utvikling:   http://localhost:8000/api
\`\`\`

### Autentisering

Alle API-forespørsler (unntatt innlogging) krever autentisering via sesjons-cookie.

**Innlogging:**
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": 1,
  "password": "optional-password"
}
\`\`\`

**Respons:**
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

Responsen setter en HTTP-only sesjons-cookie.

**Utlogging:**
\`\`\`http
POST /api/auth/logout
\`\`\`

### Forespørselsformat

- Alle forespørselskropper skal være JSON
- Bruk \`Content-Type: application/json\`-header
- Filopplastinger bruker \`multipart/form-data\`

### Responsformat

Alle responser følger denne strukturen:

**Suksess:**
\`\`\`json
{
  "data": { ... },
  "message": "Operation successful"
}
\`\`\`

**Feil:**
\`\`\`json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
\`\`\`

### HTTP-statuskoder

| Kode | Betydning |
|------|-----------|
| 200 | OK |
| 201 | Opprettet |
| 400 | Ugyldig forespørsel |
| 401 | Ikke autentisert |
| 403 | Forbudt |
| 404 | Ikke funnet |
| 422 | Valideringsfeil |
| 500 | Serverfeil |

### Hastighetsgrenser

API-forespørsler har hastighetsgrenser:
- 100 forespørsler per minutt per bruker
- 1000 forespørsler per time per bruker

Overskredet grense gir \`429 Too Many Requests\`.

### Paginering

Listeendepunkter støtter paginering:

\`\`\`http
GET /api/items?page=1&per_page=20
\`\`\`

Responsen inkluderer pagineringsmetadata:
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
		}
	},
	{
		id: 'api-endpoints',
		titleKey: 'docs.technical.apiEndpoints.title',
		content: {
			en: `
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
`,
			no: `
## API-endepunkter

Komplett referanse for alle API-endepunkter.

> URL-er, HTTP-metoder, parameter- og JSON-felt holdes på engelsk
> siden de speiler det faktiske API-et som brukes av frontend.

### Autentisering

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/auth/users | List alle brukere (for innloggingsskjerm) |
| POST | /api/auth/login | Autentiser bruker |
| POST | /api/auth/logout | Avslutt sesjon |
| GET | /api/auth/me | Hent gjeldende bruker |

### Steder

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/locations | List brukerens steder |
| POST | /api/locations | Opprett sted |
| GET | /api/locations/{id} | Hent stedsdetaljer |
| PUT | /api/locations/{id} | Oppdater sted |
| DELETE | /api/locations/{id} | Slett sted |

**Opprett sted:**
\`\`\`json
POST /api/locations
{
  "name": "Home",
  "address": "123 Main St"
}
\`\`\`

### Beholdere

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/containers | List alle beholdere |
| POST | /api/containers | Opprett beholder |
| GET | /api/containers/{id} | Hent beholderdetaljer |
| PUT | /api/containers/{id} | Oppdater beholder |
| DELETE | /api/containers/{id} | Slett beholder |
| POST | /api/containers/{id}/move | Flytt beholder |
| GET | /api/containers/{id}/qr | Hent QR-kode |

**Opprett beholder:**
\`\`\`json
POST /api/containers
{
  "name": "Storage Box 1",
  "type": "box",
  "location_id": 1,
  "parent_id": null
}
\`\`\`

### Gjenstander

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/items | List alle gjenstander |
| POST | /api/items | Opprett gjenstand |
| GET | /api/items/{id} | Hent gjenstandsdetaljer |
| PUT | /api/items/{id} | Oppdater gjenstand |
| DELETE | /api/items/{id} | Slett gjenstand |
| POST | /api/items/{id}/move | Flytt gjenstand |
| POST | /api/items/{id}/photos | Last opp bilde |
| DELETE | /api/items/{id}/photos/{photo_id} | Slett bilde |

**Opprett gjenstand:**
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

### Etiketter

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/tags | List brukerens etiketter |
| POST | /api/tags | Opprett etikett |
| PUT | /api/tags/{id} | Oppdater etikett |
| DELETE | /api/tags/{id} | Slett etikett |

### Søk

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/search | Søk i alle entiteter |

**Søkeparametre:**
\`\`\`
GET /api/search?q=jacket&type=item&location=1&tag=3
\`\`\`

### Påminnelser

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/reminders | List påminnelser |
| POST | /api/reminders | Opprett påminnelse |
| PUT | /api/reminders/{id} | Oppdater påminnelse |
| DELETE | /api/reminders/{id} | Slett påminnelse |
| POST | /api/reminders/{id}/complete | Marker som fullført |

### Deling

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| POST | /api/share | Opprett delingslenke |
| GET | /api/share/{token} | Tilgang til delt innhold |
| DELETE | /api/share/{id} | Slett delingslenke |

### Skrivere

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/printers | List skrivere |
| POST | /api/printers | Legg til skriver |
| PUT | /api/printers/{id} | Oppdater skriver |
| DELETE | /api/printers/{id} | Slett skriver |
| POST | /api/printers/{id}/test | Testutskrift |
| POST | /api/print/label | Skriv ut etikett |
| POST | /api/print/batch | Masseutskrift |

### AI-funksjoner

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| POST | /api/ai/classify | Klassifiser bilde |
| POST | /api/ai/segment | Segmenter objekter |
| POST | /api/ai/summarize | Oppsummer beholder |

### Admin

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/admin/users | List alle brukere |
| POST | /api/admin/users | Opprett bruker |
| PUT | /api/admin/users/{id} | Oppdater bruker |
| DELETE | /api/admin/users/{id} | Slett bruker |
| GET | /api/admin/stats | Systemstatistikk |
| GET | /api/admin/activity | Aktivitetslogger |
| GET | /api/admin/settings | Hent innstillinger |
| PUT | /api/admin/settings | Oppdater innstillinger |
`
		}
	}
];
