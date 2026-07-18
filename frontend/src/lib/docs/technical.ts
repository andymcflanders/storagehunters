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
- **SQLAlchemy**: Async ORM
- **PostgreSQL**: The database. StorageHub is PostgreSQL-only (\`asyncpg\` for the app, \`psycopg2\` for tooling) — the schema relies on JSONB and ARRAY columns, so other engines are not supported
- **Redis**: Message broker for background jobs
- **Celery**: Background worker (AI image processing) + beat scheduler (scheduled backups)

**Infrastructure:**
- **Docker Compose**: Runs the full stack — \`nginx\`, \`postgres\`, \`redis\`, \`backend\`, \`celery\` worker, \`celery-beat\`, \`frontend\`, and \`certbot\`
- **Nginx**: TLS entrypoint and reverse proxy
- **certbot**: Let's Encrypt certificate issuance and renewal

### System Architecture

\`\`\`
┌─────────────────────────────────────────────────────────┐
│                     Client Browser                       │
│                   (SvelteKit SPA)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────┐
│                   Nginx Reverse Proxy                    │
│         (TLS entrypoint, certs via certbot)              │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼───────┐           ┌───────▼───────┐
│   Frontend    │           │    Backend    │
│   (Node.js)   │           │   (FastAPI)   │
│   Port 3000   │           │   Port 8000   │
└───────────────┘           └───┬───────┬───┘
                                │       │
                   ┌────────────▼─┐   ┌─▼──────────┐
                   │  PostgreSQL  │   │   Redis    │
                   └──────▲───────┘   └─────▲──────┘
                          │                 │
                   ┌──────┴─────────────────┴──────┐
                   │  Celery worker + Celery beat  │
                   │  (AI image processing,        │
                   │   scheduled backups)          │
                   └───────────────────────────────┘
\`\`\`

### Key Services

**Authentication Service:**
- Session-based authentication (HTTP-only cookie)
- Password hashing with Argon2 (\`argon2-cffi\`)
- Role-based access control (Admin/User)
- API keys with scopes for external integrations

**Storage Service:**
- Hierarchical data management
- Image upload and processing
- QR code generation

**AI Service:**
- OpenAI API integration
- Runs asynchronously in the Celery worker: uploading an item image queues classification, and the results are written back to the item and image — there is no synchronous AI endpoint
- Optional owner suggestion based on household members' age and gender

**Print Service:**
- Label generation
- Printer communication
- Template rendering

**Backup Service:**
- JSON export, run on demand or on a schedule via Celery beat
- Multi-provider off-site storage: Google Drive (service account) and Dropbox
- Merge restore into an existing database

**Integrations:**
- Home Assistant API surface under \`/api/ha/*\`
- Webhooks (manageable via UI/API; event delivery is not yet wired up — only test deliveries are sent)
- SSL certificate management via \`/api/ssl\`
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
- **SQLAlchemy**: Asynkron ORM
- **PostgreSQL**: Databasen. StorageHub støtter kun PostgreSQL (\`asyncpg\` for appen, \`psycopg2\` for verktøy) — skjemaet bruker JSONB- og ARRAY-kolonner, så andre databaser støttes ikke
- **Redis**: Meldingskø for bakgrunnsjobber
- **Celery**: Bakgrunnsarbeider (AI-bildeprosessering) + beat-planlegger (planlagte sikkerhetskopier)

**Infrastruktur:**
- **Docker Compose**: Kjører hele stacken — \`nginx\`, \`postgres\`, \`redis\`, \`backend\`, \`celery\`-arbeider, \`celery-beat\`, \`frontend\` og \`certbot\`
- **Nginx**: TLS-inngangspunkt og reverse proxy
- **certbot**: Utstedelse og fornyelse av Let's Encrypt-sertifikater

### Systemarkitektur

\`\`\`
┌─────────────────────────────────────────────────────────┐
│                     Client Browser                       │
│                   (SvelteKit SPA)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────┐
│                   Nginx Reverse Proxy                    │
│         (TLS entrypoint, certs via certbot)              │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼───────┐           ┌───────▼───────┐
│   Frontend    │           │    Backend    │
│   (Node.js)   │           │   (FastAPI)   │
│   Port 3000   │           │   Port 8000   │
└───────────────┘           └───┬───────┬───┘
                                │       │
                   ┌────────────▼─┐   ┌─▼──────────┐
                   │  PostgreSQL  │   │   Redis    │
                   └──────▲───────┘   └─────▲──────┘
                          │                 │
                   ┌──────┴─────────────────┴──────┐
                   │  Celery worker + Celery beat  │
                   │  (AI image processing,        │
                   │   scheduled backups)          │
                   └───────────────────────────────┘
\`\`\`

### Hovedtjenester

**Autentisering:**
- Sesjonsbasert autentisering (HTTP-only-cookie)
- Passord-hashing med Argon2 (\`argon2-cffi\`)
- Rollebasert tilgangskontroll (admin/bruker)
- API-nøkler med scopes for eksterne integrasjoner

**Lagring:**
- Hierarkisk datahåndtering
- Bildeopplasting og prosessering
- QR-kodegenerering

**AI:**
- OpenAI API-integrasjon
- Kjører asynkront i Celery-arbeideren: opplasting av et gjenstandsbilde legger klassifisering i kø, og resultatene skrives tilbake til gjenstanden og bildet — det finnes ikke noe synkront AI-endepunkt
- Valgfritt eierforslag basert på husstandsmedlemmenes alder og kjønn

**Utskrift:**
- Etikettgenerering
- Skriverkommunikasjon
- Malrendering

**Sikkerhetskopiering:**
- JSON-eksport, på forespørsel eller etter plan via Celery beat
- Flere lagringstilbydere: Google Drive (tjenestekonto) og Dropbox
- Flettegjenoppretting inn i en eksisterende database

**Integrasjoner:**
- Home Assistant-API under \`/api/ha/*\`
- Webhooks (kan administreres via UI/API; hendelseslevering er ennå ikke koblet på — kun testleveranser sendes)
- SSL-sertifikathåndtering via \`/api/ssl\`
`
		}
	},
	{
		id: 'database',
		titleKey: 'docs.technical.database.title',
		content: {
			en: `
## Database Models

StorageHub uses PostgreSQL with the following entity relationships.

### Entity Relationships

\`\`\`
Location  1─*  Container   (self-referencing parent_container_id for nesting)
Container 1─*  Item
Item      1─*  ItemImage
Item      *──* Tag         (via the ItemTag junction table)
Item      *──1 User        (owner_id, nullable; plus suggested_owner_id)
Container 1─*  ShareLink   (sharing is container-only)
User      1─*  Session, APIKey, Webhook
Reminder  *──1 User        (optionally linked to one Item or Container)
\`\`\`

### User Model

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Display name |
| email | String(255) | Login email (nullable) |
| password_hash | String(255) | Argon2 hash (nullable) |
| avatar_url | Text | Optional avatar URL |
| requires_password | Boolean | If false, the household card grid lets the user log in with one click |
| role | Enum | \`admin\` or \`user\` |
| language | Enum | \`en\` or \`no\` (default \`en\`) — extendable via AI Settings |
| is_active | Boolean | Account status |
| is_profile | Boolean | Household member who owns items but never logs in (e.g. small kids); hidden from the login card grid |
| birthdate | Date | Used to compute age in months for AI owner suggestion + the Outgrown view (nullable) |
| gender | Enum | \`male\` / \`female\` / \`other\` — feeds the AI owner suggestion prompt (nullable) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Location Model

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String(200) | Location name |
| address | String(500) | Physical address |
| user_id | UUID | Foreign key to User |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Container Model

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Container name |
| notes | Text | Optional notes |
| container_type | String(32) | Optional category (\`box\`, \`drawer\`, \`shelf\`, \`cabinet\`, \`closet\`, \`bin\`, \`basket\`, \`other\`) |
| image_filepath | Text | Optional hero image (relative path under upload dir; served as \`image_url\`) |
| location_id | UUID | Foreign key to Location |
| parent_container_id | UUID | Self-referential FK (nullable) |
| qr_code | String(32) | Unique URL-safe base64 token |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Item Model

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Item name |
| description | Text | Manual description |
| size | String(50) | Size info |
| condition | Enum | \`good\` / \`fair\` / \`damaged\` / \`needs_repair\` |
| seasonal | Enum | \`none\` / \`spring\` / \`summer\` / \`fall\` / \`winter\` / \`holiday\` |
| value_estimate | Decimal | Estimated value |
| owner_id | UUID | Foreign key to User (nullable) |
| container_id | UUID | Foreign key to Container |
| ai_names | JSONB | AI-generated names keyed by ISO language code, e.g. \`{"en": "Red Sweater", "no": "Rød Genser"}\` |
| ai_descriptions | JSONB | AI-generated descriptions, same shape as \`ai_names\` |
| ai_processed | Boolean | Whether the AI pipeline has finished |
| needs_review | Boolean | Flag for the godview filter / Home Assistant stats |
| primary_image_id | UUID | Hero image selection |
| suggested_owner_id | UUID | AI's pick for likely owner; surfaced as a banner on the item page until applied or dismissed (nullable) |
| owner_suggestion_reason | Text | One-sentence rationale shown alongside the suggestion (nullable) |
| size_age_min_months | Integer | Lower bound of the size→age mapping; only set for kid-mapped sizes (nullable) |
| size_age_max_months | Integer | Upper bound of the size→age mapping; \`/outgrown\` shows items where the owner has aged past this (nullable) |
| outgrown_dismissed_at | DateTime | Set when the user dismisses an item from \`/outgrown\` (nullable) |
| triage_decision | String(20) | \`love\` / \`undecided\` / \`hate\` / null — set on \`/declutter\` |
| triage_decided_at | DateTime | When the triage decision was made (nullable) |
| triage_show_after | DateTime | Cooldown stamp; while \`now() < triage_show_after\` the item is hidden from \`/declutter\` (nullable) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Tag Model

Tags are shared household-wide — there is no per-user ownership and no color column.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String(100) | Tag name (globally unique) |
| user_created | Boolean | True for manually created tags, false for AI-generated ones |
| created_at | DateTime | Creation timestamp |

### ItemTag (Junction Table)

| Column | Type | Description |
|--------|------|-------------|
| item_id | UUID | Foreign key to Item |
| tag_id | UUID | Foreign key to Tag |

### ItemImage Model

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| item_id | UUID | Foreign key to Item |
| filename | String(255) | Stored filename |
| filepath | Text | Path under the upload directory |
| ai_tags | String[] | AI-generated tags used by search |
| ai_description | Text | AI description of the image (nullable) |
| ai_processed | Boolean | Whether the AI pipeline has processed this image |
| uploaded_by | UUID | FK to the uploading User (nullable) |
| created_at | DateTime | Upload timestamp |

### ShareLink Model

Share links are container-only — locations cannot be shared.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| container_id | UUID | FK to Container |
| user_id | UUID | FK to the User who created the link |
| token | String(32) | Unique URL-safe token |
| is_active | Boolean | Toggle a link off without deleting it |
| allow_item_view | Boolean | Show items flag |
| expires_at | DateTime | Expiration (nullable) |
| view_count | Integer | Access counter |
| created_at | DateTime | Creation timestamp |

### Reminder Model

Recurrence is a simple day interval — there are no cron patterns.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User |
| item_id | UUID | FK to Item (nullable) |
| container_id | UUID | FK to Container (nullable) |
| title | String(255) | Reminder title |
| description | Text | Optional details |
| reminder_type | String(32) | \`check_item\` / \`expiration\` / \`maintenance\` / \`restock\` / \`custom\` |
| due_date | DateTime | When due |
| is_completed | Boolean | Completion status |
| is_recurring | Boolean | Repeat flag |
| recurrence_days | Integer | Days between recurrences (nullable) |
| completed_at | DateTime | When completed (nullable) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Printer Model

Printers are shared household-wide (no \`user_id\`) and label dimensions live in dedicated columns — there is no free-form settings JSON.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | Printer name |
| printer_type | Enum | \`zebra_zpl\` / \`brother_ql\` / \`generic_pdf\` / \`network_ipp\` |
| connection_type | Enum | \`network\` / \`usb\` / \`file\` |
| address | String(255) | Connection address |
| label_width_mm | Float | Label width in millimeters |
| label_height_mm | Float | Label height in millimeters |
| is_default | Boolean | Default printer flag |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### AISettings (singleton)

A single-row config table read by the AI classifier and the semantic
search query parser. Updated from Admin → AI Settings or by the
\`/api/setup/complete\` wizard.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| vision_model | String(100) | OpenAI vision model id (default \`gpt-4o\`) |
| vision_max_tokens | Integer | Response token cap for classification |
| vision_temperature | Float | Sampling temperature |
| vision_enabled | Boolean | Toggle vision classification |
| summary_model | String(100) | OpenAI text model for label summaries |
| summary_max_tokens | Integer | Response token cap for summaries |
| summary_temperature | Float | Sampling temperature |
| summary_enabled | Boolean | Toggle AI summaries |
| owner_suggestion_enabled | Boolean | Toggle AI owner suggestion (matches item size/motif against each user's age and gender) |
| supported_languages | String[] | ISO codes the AI generates content in (default \`{en, no}\`) |
| default_language | String(10) | Fallback locale when a translation is missing |
| openai_api_key | Text | Persisted API key. Wins over \`OPENAI_API_KEY\` env var |
| instance_uuid | UUID | Stable identifier for this instance, surfaced by \`/api/ha/status\` for the Home Assistant integration |
`,
			no: `
## Databasemodeller

StorageHub bruker PostgreSQL med følgende entitetsforhold.

### Entitetsforhold

\`\`\`
Location  1─*  Container   (selvrefererende parent_container_id for nesting)
Container 1─*  Item
Item      1─*  ItemImage
Item      *──* Tag         (via koblingstabellen ItemTag)
Item      *──1 User        (owner_id, kan være null; pluss suggested_owner_id)
Container 1─*  ShareLink   (deling gjelder kun beholdere)
User      1─*  Session, APIKey, Webhook
Reminder  *──1 User        (kan i tillegg peke på én Item eller Container)
\`\`\`

> Kolonnenavn og typer holdes på engelsk siden de speiler det faktiske
> databaseskjemaet og koden.

### User-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| name | String(255) | Visningsnavn |
| email | String(255) | E-post for innlogging (kan være null) |
| password_hash | String(255) | Argon2-hash (kan være null) |
| avatar_url | Text | Valgfri avatar-URL |
| requires_password | Boolean | Hvis false kan brukeren logge inn med ett klikk fra kortrutenettet |
| role | Enum | \`admin\` eller \`user\` |
| language | Enum | \`en\` eller \`no\` (standard \`en\`) — kan utvides via AI-innstillinger |
| is_active | Boolean | Kontostatus |
| is_profile | Boolean | Husstandsmedlem som eier gjenstander men aldri logger inn (f.eks. små barn); skjules fra kortrutenettet |
| birthdate | Date | Brukes til å beregne alder i måneder for AI-eierforslag + Utvokst-visningen (kan være null) |
| gender | Enum | \`male\` / \`female\` / \`other\` — brukes i AI-eierforslagsprompten (kan være null) |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Location-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| name | String(200) | Stedsnavn |
| address | String(500) | Fysisk adresse |
| user_id | UUID | Fremmednøkkel til User |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Container-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| name | String(255) | Beholdernavn |
| notes | Text | Valgfrie notater |
| container_type | String(32) | Valgfri kategori (\`box\`, \`drawer\`, \`shelf\`, \`cabinet\`, \`closet\`, \`bin\`, \`basket\`, \`other\`) |
| image_filepath | Text | Valgfritt hovedbilde (relativ sti, eksponeres som \`image_url\`) |
| location_id | UUID | Fremmednøkkel til Location |
| parent_container_id | UUID | Selvreferanse (kan være null) |
| qr_code | String(32) | Unik URL-trygg base64-token |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Item-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| name | String(255) | Gjenstandsnavn |
| description | Text | Manuell beskrivelse |
| size | String(50) | Størrelsesinfo |
| condition | Enum | \`good\` / \`fair\` / \`damaged\` / \`needs_repair\` |
| seasonal | Enum | \`none\` / \`spring\` / \`summer\` / \`fall\` / \`winter\` / \`holiday\` |
| value_estimate | Decimal | Estimert verdi |
| owner_id | UUID | Fremmednøkkel til User (kan være null) |
| container_id | UUID | Fremmednøkkel til Container |
| ai_names | JSONB | AI-genererte navn etter ISO-språkkode, f.eks. \`{"en": "Red Sweater", "no": "Rød Genser"}\` |
| ai_descriptions | JSONB | AI-genererte beskrivelser, samme form som \`ai_names\` |
| ai_processed | Boolean | Om AI-prosesseringen er fullført |
| needs_review | Boolean | Flagg for godview-filteret / Home Assistant-statistikk |
| primary_image_id | UUID | Hovedbildevalg |
| suggested_owner_id | UUID | AI-ens forslag til sannsynlig eier; vises som banner på gjenstandssiden til det brukes eller avvises (kan være null) |
| owner_suggestion_reason | Text | Én setnings begrunnelse som vises sammen med forslaget (kan være null) |
| size_age_min_months | Integer | Nedre grense i størrelse→alder-koblingen; settes bare for barnestørrelser (kan være null) |
| size_age_max_months | Integer | Øvre grense i størrelse→alder-koblingen; \`/outgrown\` viser gjenstander der eieren har vokst forbi denne (kan være null) |
| outgrown_dismissed_at | DateTime | Settes når brukeren avviser en gjenstand fra \`/outgrown\` (kan være null) |
| triage_decision | String(20) | \`love\` / \`undecided\` / \`hate\` / null — settes på \`/declutter\` |
| triage_decided_at | DateTime | Når triage-avgjørelsen ble tatt (kan være null) |
| triage_show_after | DateTime | Nedkjølingsstempel; så lenge \`now() < triage_show_after\` skjules gjenstanden fra \`/declutter\` (kan være null) |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Tag-modell

Etiketter deles av hele husstanden — det finnes ingen eierskap per bruker og ingen fargekolonne.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| name | String(100) | Etikettnavn (globalt unikt) |
| user_created | Boolean | True for manuelt opprettede etiketter, false for AI-genererte |
| created_at | DateTime | Opprettet |

### ItemTag (koblingstabell)

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| item_id | UUID | Fremmednøkkel til Item |
| tag_id | UUID | Fremmednøkkel til Tag |

### ItemImage-modell

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| item_id | UUID | Fremmednøkkel til Item |
| filename | String(255) | Lagret filnavn |
| filepath | Text | Sti under opplastingskatalogen |
| ai_tags | String[] | AI-genererte etiketter brukt av søket |
| ai_description | Text | AI-beskrivelse av bildet (kan være null) |
| ai_processed | Boolean | Om AI-prosesseringen av bildet er fullført |
| uploaded_by | UUID | FK til brukeren som lastet opp (kan være null) |
| created_at | DateTime | Opplastet |

### ShareLink-modell

Delingslenker gjelder kun beholdere — steder kan ikke deles.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| container_id | UUID | FK til Container |
| user_id | UUID | FK til brukeren som opprettet lenken |
| token | String(32) | Unik URL-trygg token |
| is_active | Boolean | Slå av en lenke uten å slette den |
| allow_item_view | Boolean | Vis gjenstander |
| expires_at | DateTime | Utløp (kan være null) |
| view_count | Integer | Antall visninger |
| created_at | DateTime | Opprettet |

### Reminder-modell

Gjentakelse er et enkelt dagsintervall — det finnes ingen cron-mønstre.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| user_id | UUID | Fremmednøkkel til User |
| item_id | UUID | FK til Item (kan være null) |
| container_id | UUID | FK til Container (kan være null) |
| title | String(255) | Påminnelsestittel |
| description | Text | Valgfrie detaljer |
| reminder_type | String(32) | \`check_item\` / \`expiration\` / \`maintenance\` / \`restock\` / \`custom\` |
| due_date | DateTime | Forfallsdato |
| is_completed | Boolean | Fullført |
| is_recurring | Boolean | Gjentakende |
| recurrence_days | Integer | Dager mellom gjentakelser (kan være null) |
| completed_at | DateTime | Når fullført (kan være null) |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### Printer-modell

Skrivere deles av hele husstanden (ingen \`user_id\`), og etikettmålene ligger i egne kolonner — det finnes ingen fri konfigurasjons-JSON.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| name | String(255) | Skrivernavn |
| printer_type | Enum | \`zebra_zpl\` / \`brother_ql\` / \`generic_pdf\` / \`network_ipp\` |
| connection_type | Enum | \`network\` / \`usb\` / \`file\` |
| address | String(255) | Tilkoblingsadresse |
| label_width_mm | Float | Etikettbredde i millimeter |
| label_height_mm | Float | Etiketthøyde i millimeter |
| is_default | Boolean | Standardskriver |
| created_at | DateTime | Opprettet |
| updated_at | DateTime | Sist oppdatert |

### AISettings (singleton)

Singleton-rad som styrer AI-klassifisereren og det semantiske
søkeparserne. Oppdateres fra Admin → AI-innstillinger eller via
\`/api/setup/complete\`-veiviseren.

| Kolonne | Type | Beskrivelse |
|---------|------|-------------|
| id | UUID | Primærnøkkel |
| vision_model | String(100) | OpenAI vision-modell-ID (standard \`gpt-4o\`) |
| vision_max_tokens | Integer | Maks responstokens for klassifisering |
| vision_temperature | Float | Sampling-temperatur |
| vision_enabled | Boolean | Slå klassifisering av/på |
| summary_model | String(100) | OpenAI tekstmodell for etikettsammendrag |
| summary_max_tokens | Integer | Maks responstokens for sammendrag |
| summary_temperature | Float | Sampling-temperatur |
| summary_enabled | Boolean | Slå sammendrag av/på |
| owner_suggestion_enabled | Boolean | Slå AI-eierforslag av/på (matcher gjenstandens størrelse/motiv mot brukernes alder og kjønn) |
| supported_languages | String[] | ISO-koder AI genererer innhold i (standard \`{en, no}\`) |
| default_language | String(10) | Reservespråk når en oversettelse mangler |
| openai_api_key | Text | Lagret API-nøkkel. Tar forrang over \`OPENAI_API_KEY\`-miljøvariabel |
| instance_uuid | UUID | Stabil identifikator for denne instansen, eksponert via \`/api/ha/status\` for Home Assistant-integrasjonen |
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

All API requests (except login and public share links) require authentication via session cookie or an API key.

Household users are picked from the login card grid (backed by
\`GET /api/users?include_admins=false&include_profiles=false\`) and log in
by \`user_id\`; a password is only needed when the account has
\`requires_password\` set. Admins log in with email + password.

**Login (card grid):**
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": "7c9e6679-7425-40de-963d-a31c3e28d731",
  "password": "only-if-requires_password"
}
\`\`\`

**Login (admin, email + password):**
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "secret"
}
\`\`\`

**Response:**
\`\`\`json
{
  "token": "wN3xkQ...",
  "expires_at": "2026-08-17T12:00:00Z",
  "user": {
    "id": "7c9e6679-7425-40de-963d-a31c3e28d731",
    "name": "John",
    "role": "admin"
  }
}
\`\`\`

The response also sets an HTTP-only \`session_token\` cookie. Note that user IDs are UUIDs, not integers.

**Logout:**
\`\`\`http
POST /api/auth/logout
\`\`\`

### Request Format

- All request bodies should be JSON
- Use \`Content-Type: application/json\` header
- File uploads use \`multipart/form-data\`

### Response Format

The API does not wrap responses in an envelope. Each endpoint returns its
FastAPI/Pydantic model (or a bare array) directly:

**Success:**
\`\`\`json
{
  "id": "7c9e6679-7425-40de-963d-a31c3e28d731",
  "name": "Winter Jacket",
  "condition": "good"
}
\`\`\`

**Error** (FastAPI default shape):
\`\`\`json
{
  "detail": "Container not found"
}
\`\`\`

Validation errors (422) return \`detail\` as a list of per-field errors.

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (deletes and some actions) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

### Rate Limiting

The backend does not implement rate limiting — there are no request
quotas and the API never returns \`429\`. If you expose an instance to the
public internet, enforce limits in front of it (e.g. nginx \`limit_req\`).

### Pagination

There is no \`page\`/\`per_page\` scheme and no pagination envelope.
Endpoints that paginate (e.g. \`/api/search\`) take \`limit\` and \`offset\`
query parameters:

\`\`\`http
GET /api/search?q=jacket&limit=50&offset=0
\`\`\`

Most list endpoints (e.g. \`/api/items\`, \`/api/containers\`) simply return
the full result set as a bare JSON array.
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

Alle API-forespørsler (unntatt innlogging og offentlige delingslenker) krever autentisering via sesjons-cookie eller API-nøkkel.

Husstandsbrukere velges fra kortrutenettet på innloggingssiden (som bruker
\`GET /api/users?include_admins=false&include_profiles=false\`) og logger inn
med \`user_id\`; passord kreves bare når kontoen har \`requires_password\`.
Admins logger inn med e-post + passord.

**Innlogging (kortrutenett):**
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": "7c9e6679-7425-40de-963d-a31c3e28d731",
  "password": "only-if-requires_password"
}
\`\`\`

**Innlogging (admin, e-post + passord):**
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "secret"
}
\`\`\`

**Respons:**
\`\`\`json
{
  "token": "wN3xkQ...",
  "expires_at": "2026-08-17T12:00:00Z",
  "user": {
    "id": "7c9e6679-7425-40de-963d-a31c3e28d731",
    "name": "John",
    "role": "admin"
  }
}
\`\`\`

Responsen setter også en HTTP-only \`session_token\`-cookie. Merk at bruker-ID-er er UUID-er, ikke heltall.

**Utlogging:**
\`\`\`http
POST /api/auth/logout
\`\`\`

### Forespørselsformat

- Alle forespørselskropper skal være JSON
- Bruk \`Content-Type: application/json\`-header
- Filopplastinger bruker \`multipart/form-data\`

### Responsformat

API-et pakker ikke responser inn i noen konvolutt. Hvert endepunkt
returnerer sin FastAPI/Pydantic-modell (eller en ren liste) direkte:

**Suksess:**
\`\`\`json
{
  "id": "7c9e6679-7425-40de-963d-a31c3e28d731",
  "name": "Winter Jacket",
  "condition": "good"
}
\`\`\`

**Feil** (FastAPIs standardform):
\`\`\`json
{
  "detail": "Container not found"
}
\`\`\`

Valideringsfeil (422) returnerer \`detail\` som en liste med feltfeil.

### HTTP-statuskoder

| Kode | Betydning |
|------|-----------|
| 200 | OK |
| 201 | Opprettet |
| 204 | Ingen innhold (sletting og enkelte handlinger) |
| 400 | Ugyldig forespørsel |
| 401 | Ikke autentisert |
| 403 | Forbudt |
| 404 | Ikke funnet |
| 422 | Valideringsfeil |
| 500 | Serverfeil |

### Hastighetsgrenser

Backend har ingen hastighetsbegrensning — det finnes ingen kvoter, og
API-et returnerer aldri \`429\`. Eksponerer du en instans mot internett,
bør du håndheve grenser foran den (f.eks. nginx \`limit_req\`).

### Paginering

Det finnes ingen \`page\`/\`per_page\`-ordning og ingen
pagineringskonvolutt. Endepunkter som paginerer (f.eks. \`/api/search\`)
bruker \`limit\`- og \`offset\`-parametre:

\`\`\`http
GET /api/search?q=jacket&limit=50&offset=0
\`\`\`

De fleste listeendepunkter (f.eks. \`/api/items\`, \`/api/containers\`)
returnerer rett og slett hele resultatsettet som en ren JSON-liste.
`
		}
	},
	{
		id: 'api-endpoints',
		titleKey: 'docs.technical.apiEndpoints.title',
		content: {
			en: `
## API Endpoints

Complete reference for all API endpoints. Updates use \`PATCH\` (partial
update) throughout — the only \`PUT\` endpoints are \`/api/admin/openai\`
and \`/api/admin/languages\`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | Authenticate (card-tap \`user_id\`, or email + password for admins) |
| POST | /api/auth/logout | End session |
| GET | /api/auth/me | Get current user |

There is no \`/api/auth/users\` — the login card grid uses
\`GET /api/users?include_admins=false&include_profiles=false\`.

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users | List users (\`?include_admins=&include_profiles=\`) |
| POST | /api/users | Create user |
| GET | /api/users/{id} | Get user |
| PATCH | /api/users/{id} | Update user |
| DELETE | /api/users/{id} | Delete user |
| POST | /api/users/{id}/avatar | Upload avatar |

### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/locations | List locations |
| GET | /api/locations/stats | Dashboard statistics |
| POST | /api/locations | Create location |
| GET | /api/locations/{id} | Get location details |
| PATCH | /api/locations/{id} | Update location |
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
| PATCH | /api/containers/{id} | Update container |
| DELETE | /api/containers/{id} | Delete container |
| GET | /api/containers/qr/{qr_code} | Resolve a scanned QR token |
| GET | /api/containers/{id}/qr | Get QR code image |
| GET | /api/containers/{id}/path | Breadcrumb path |
| POST | /api/containers/{id}/image | Upload hero image |
| DELETE | /api/containers/{id}/image | Remove hero image |

Containers are moved via the inventory router:
\`POST /api/inventory/{id}/move\` (there is no
\`/api/containers/{id}/move\`).

**Create Container:**
\`\`\`json
POST /api/containers
{
  "name": "Storage Box 1",
  "container_type": "box",
  "location_id": "7c9e6679-7425-40de-963d-a31c3e28d731",
  "parent_container_id": null
}
\`\`\`

### Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/items | List all items |
| POST | /api/items | Create item |
| GET | /api/items/{id} | Get item details |
| PATCH | /api/items/{id} | Update item |
| DELETE | /api/items/{id} | Delete item |
| POST | /api/items/{id}/move | Move item to another container |
| POST | /api/items/{id}/images | Upload image (queues AI processing) |
| DELETE | /api/items/{id}/images/{image_id} | Delete image |
| POST | /api/items/{id}/images/{image_id}/set-primary | Set hero image |
| POST | /api/items/{id}/images/{image_id}/reprocess | Re-run AI on one image |
| POST | /api/items/{id}/process-all-images | Re-run AI on all images |
| POST | /api/items/{id}/tags | Attach tag |
| DELETE | /api/items/{id}/tags/{tag_id} | Detach tag |

**Create Item:**
\`\`\`json
POST /api/items
{
  "name": "Winter Jacket",
  "description": "Blue puffer jacket",
  "condition": "good",
  "container_id": "b3e1a1f0-52c4-4b8e-9d2f-0c5a7d9e1234"
}
\`\`\`

Tags are attached separately via \`POST /api/items/{id}/tags\` — there is
no \`quantity\` field.

### Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/tags | List tags |
| POST | /api/tags | Create tag |
| PATCH | /api/tags/{id} | Update tag |
| DELETE | /api/tags/{id} | Delete tag |
| POST | /api/tags/merge | Merge tags |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/search | Search items (AI-powered semantic ranking) |
| GET | /api/search/autocomplete | Autocomplete suggestions |

**Search Parameters** (\`q\`, \`owner\`, \`location\`, \`container\`, \`size\`,
\`condition\`, \`seasonal\`, \`tags\`, \`smart_search\`, \`limit\`, \`offset\`):
\`\`\`
GET /api/search?q=jacket&owner=<uuid>&location=<uuid>&container=<uuid>
    &size=104&condition=good&seasonal=winter&tags=kids,clothes
    &smart_search=true&limit=50&offset=0
\`\`\`

### Reminders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/reminders | List reminders |
| GET | /api/reminders/upcoming | Upcoming reminders |
| POST | /api/reminders | Create reminder |
| GET | /api/reminders/{id} | Get reminder |
| PATCH | /api/reminders/{id} | Update reminder |
| DELETE | /api/reminders/{id} | Delete reminder |
| POST | /api/reminders/{id}/complete | Mark complete |

### Sharing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/shares | Create share link (containers only) |
| GET | /api/shares | List share links |
| PATCH | /api/shares/{id}/toggle | Enable/disable a link |
| DELETE | /api/shares/{id} | Delete share link |
| GET | /api/shares/public/{token} | Public access (no auth) |

### Printers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/printers | List printers |
| POST | /api/printers | Add printer |
| GET | /api/printers/{id} | Get printer |
| PATCH | /api/printers/{id} | Update printer |
| DELETE | /api/printers/{id} | Delete printer |
| POST | /api/printers/{id}/test | Test print |
| POST | /api/printers/{id}/print | Print a label |
| POST | /api/printers/{id}/print-batch | Batch print |
| GET | /api/printers/{id}/preview | Label preview |
| GET | /api/printers/{id}/download | Download label file |
| GET | /api/printers/{id}/media | Suggested media size |

### AI Processing

There is no \`/api/ai\` router. AI classification runs automatically in
the Celery background worker whenever an item image is uploaded; results
land on the item (\`ai_names\`, \`ai_descriptions\`, owner suggestion) and
its images (\`ai_tags\`, \`ai_description\`). Manual re-runs use the
\`reprocess\` / \`process-all-images\` endpoints under \`/api/items\`, and
configuration lives at \`/api/admin/openai\`.

### Outgrown

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/outgrown | List items the household has aged out of, with optional inherit-to suggestions |

### Triage / Declutter

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/triage/next | Random eligible item (\`?owner_id=&tag=\`) |
| POST | /api/triage/{id}/decide | Body \`{decision: "love"\\|"undecided"\\|"hate"}\` |
| POST | /api/triage/{id}/undo | Clear a decision |
| POST | /api/triage/{id}/mark-donated | Soft-delete with a "donated" activity log entry |
| GET | /api/triage/filters | Owner + top-30 tag dropdown options |
| GET | /api/triage/discard | Hated items grouped by container path |

Cooldowns are hard-coded: love = 12 months, undecided = 3 months,
hate = no cooldown (item moves to the discard pile).

### Inventory

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/inventory/tree | Full location → container → item tree ("god view") |
| POST | /api/inventory/{id}/move | Move a container to a new location/parent |

### Activity & Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/activity | Activity log (admins see everyone's) |
| GET | /api/activity/my | Current user's activity |
| GET | /api/export/json | Full JSON export |
| GET | /api/export/csv | CSV export |

### API Keys

Managed from the Admin tab. Keys carry scopes (\`read\`, \`write\`,
\`search\`, \`webhooks\`, \`admin\`) and authenticate external clients such
as the Home Assistant integration.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/api-keys | List API keys |
| POST | /api/api-keys | Create key (secret shown once) |
| GET | /api/api-keys/{id} | Get key |
| PATCH | /api/api-keys/{id} | Update key |
| DELETE | /api/api-keys/{id} | Revoke key |

### Webhooks

Webhooks can be managed here, but event delivery is not yet wired into
the app — only the test endpoint actually sends anything.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/webhooks | List webhooks |
| POST | /api/webhooks | Create webhook |
| GET | /api/webhooks/events | Available event types |
| GET | /api/webhooks/{id} | Get webhook |
| PATCH | /api/webhooks/{id} | Update webhook |
| DELETE | /api/webhooks/{id} | Delete webhook |
| POST | /api/webhooks/{id}/test | Send a test delivery |
| GET | /api/webhooks/{id}/deliveries | Recent deliveries |

### Home Assistant

A read-oriented API surface under \`/api/ha/*\` (status, stats,
reminders, locations, containers, items, search, semantic search, tags)
consumed by the Home Assistant integration, authenticated with an API
key.

### Backups

Multi-provider backup system under \`/api/backup/*\`: backup configs and
schedules (run by Celery beat), on-demand \`create\`, history with
download, JSON \`quick-download\` export, restore
(\`upload\`/\`execute\`/\`from-history\`, merge restore into existing data),
and provider operations for Google Drive (service account) and Dropbox
(test, list, upload, download, delete).

### SSL

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/ssl | Get SSL configuration |
| GET | /api/ssl/status | Certificate status |
| PATCH | /api/ssl | Update configuration |
| POST | /api/ssl/generate | Issue certificate (Let's Encrypt) |
| POST | /api/ssl/renew | Renew certificate |
| POST | /api/ssl/test | Test configuration |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/stats | System statistics |
| GET | /api/admin/users | List all users |
| POST | /api/admin/users | Create user |
| PATCH | /api/admin/users/{id} | Update user |
| DELETE | /api/admin/users/{id} | Delete user |
| GET | /api/admin/activity | Activity logs |
| GET | /api/admin/usage-stats | AI usage and cost statistics |
| GET | /api/admin/openai | Read OpenAI configuration |
| PUT | /api/admin/openai | Update OpenAI config (incl. \`owner_suggestion_enabled\`) |
| GET | /api/admin/languages | Read AI language settings |
| PUT | /api/admin/languages | Update AI language settings |
| POST | /api/admin/recompute-size-ages | Backfill \`size_age_min/max_months\` for items with a size but no age range |

There is no \`/api/admin/settings\` endpoint — settings are split across
\`/api/admin/openai\`, \`/api/admin/languages\`, \`/api/ssl\`, and
\`/api/backup\`.
`,
			no: `
## API-endepunkter

Komplett referanse for alle API-endepunkter. Oppdateringer bruker
\`PATCH\` (delvis oppdatering) hele veien — de eneste
\`PUT\`-endepunktene er \`/api/admin/openai\` og \`/api/admin/languages\`.

> URL-er, HTTP-metoder, parameter- og JSON-felt holdes på engelsk
> siden de speiler det faktiske API-et som brukes av frontend.

### Autentisering

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| POST | /api/auth/login | Autentiser (kort-trykk med \`user_id\`, eller e-post + passord for admins) |
| POST | /api/auth/logout | Avslutt sesjon |
| GET | /api/auth/me | Hent gjeldende bruker |

Det finnes ikke noe \`/api/auth/users\` — kortrutenettet på
innloggingssiden bruker
\`GET /api/users?include_admins=false&include_profiles=false\`.

### Brukere

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/users | List brukere (\`?include_admins=&include_profiles=\`) |
| POST | /api/users | Opprett bruker |
| GET | /api/users/{id} | Hent bruker |
| PATCH | /api/users/{id} | Oppdater bruker |
| DELETE | /api/users/{id} | Slett bruker |
| POST | /api/users/{id}/avatar | Last opp avatar |

### Steder

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/locations | List steder |
| GET | /api/locations/stats | Dashbordstatistikk |
| POST | /api/locations | Opprett sted |
| GET | /api/locations/{id} | Hent stedsdetaljer |
| PATCH | /api/locations/{id} | Oppdater sted |
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
| PATCH | /api/containers/{id} | Oppdater beholder |
| DELETE | /api/containers/{id} | Slett beholder |
| GET | /api/containers/qr/{qr_code} | Slå opp skannet QR-token |
| GET | /api/containers/{id}/qr | Hent QR-kodebilde |
| GET | /api/containers/{id}/path | Brødsmulesti |
| POST | /api/containers/{id}/image | Last opp hovedbilde |
| DELETE | /api/containers/{id}/image | Fjern hovedbilde |

Beholdere flyttes via inventar-ruteren:
\`POST /api/inventory/{id}/move\` (det finnes ikke noe
\`/api/containers/{id}/move\`).

**Opprett beholder:**
\`\`\`json
POST /api/containers
{
  "name": "Storage Box 1",
  "container_type": "box",
  "location_id": "7c9e6679-7425-40de-963d-a31c3e28d731",
  "parent_container_id": null
}
\`\`\`

### Gjenstander

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/items | List alle gjenstander |
| POST | /api/items | Opprett gjenstand |
| GET | /api/items/{id} | Hent gjenstandsdetaljer |
| PATCH | /api/items/{id} | Oppdater gjenstand |
| DELETE | /api/items/{id} | Slett gjenstand |
| POST | /api/items/{id}/move | Flytt gjenstand til annen beholder |
| POST | /api/items/{id}/images | Last opp bilde (legger AI-prosessering i kø) |
| DELETE | /api/items/{id}/images/{image_id} | Slett bilde |
| POST | /api/items/{id}/images/{image_id}/set-primary | Sett hovedbilde |
| POST | /api/items/{id}/images/{image_id}/reprocess | Kjør AI på nytt for ett bilde |
| POST | /api/items/{id}/process-all-images | Kjør AI på nytt for alle bilder |
| POST | /api/items/{id}/tags | Legg til etikett |
| DELETE | /api/items/{id}/tags/{tag_id} | Fjern etikett |

**Opprett gjenstand:**
\`\`\`json
POST /api/items
{
  "name": "Winter Jacket",
  "description": "Blue puffer jacket",
  "condition": "good",
  "container_id": "b3e1a1f0-52c4-4b8e-9d2f-0c5a7d9e1234"
}
\`\`\`

Etiketter legges til separat via \`POST /api/items/{id}/tags\` — det
finnes ikke noe \`quantity\`-felt.

### Etiketter

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/tags | List etiketter |
| POST | /api/tags | Opprett etikett |
| PATCH | /api/tags/{id} | Oppdater etikett |
| DELETE | /api/tags/{id} | Slett etikett |
| POST | /api/tags/merge | Slå sammen etiketter |

### Søk

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/search | Søk i gjenstander (AI-drevet semantisk rangering) |
| GET | /api/search/autocomplete | Autofullfør-forslag |

**Søkeparametre** (\`q\`, \`owner\`, \`location\`, \`container\`, \`size\`,
\`condition\`, \`seasonal\`, \`tags\`, \`smart_search\`, \`limit\`, \`offset\`):
\`\`\`
GET /api/search?q=jacket&owner=<uuid>&location=<uuid>&container=<uuid>
    &size=104&condition=good&seasonal=winter&tags=kids,clothes
    &smart_search=true&limit=50&offset=0
\`\`\`

### Påminnelser

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/reminders | List påminnelser |
| GET | /api/reminders/upcoming | Kommende påminnelser |
| POST | /api/reminders | Opprett påminnelse |
| GET | /api/reminders/{id} | Hent påminnelse |
| PATCH | /api/reminders/{id} | Oppdater påminnelse |
| DELETE | /api/reminders/{id} | Slett påminnelse |
| POST | /api/reminders/{id}/complete | Marker som fullført |

### Deling

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| POST | /api/shares | Opprett delingslenke (kun beholdere) |
| GET | /api/shares | List delingslenker |
| PATCH | /api/shares/{id}/toggle | Slå lenke av/på |
| DELETE | /api/shares/{id} | Slett delingslenke |
| GET | /api/shares/public/{token} | Offentlig tilgang (uten innlogging) |

### Skrivere

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/printers | List skrivere |
| POST | /api/printers | Legg til skriver |
| GET | /api/printers/{id} | Hent skriver |
| PATCH | /api/printers/{id} | Oppdater skriver |
| DELETE | /api/printers/{id} | Slett skriver |
| POST | /api/printers/{id}/test | Testutskrift |
| POST | /api/printers/{id}/print | Skriv ut etikett |
| POST | /api/printers/{id}/print-batch | Masseutskrift |
| GET | /api/printers/{id}/preview | Forhåndsvisning av etikett |
| GET | /api/printers/{id}/download | Last ned etikettfil |
| GET | /api/printers/{id}/media | Foreslått mediestørrelse |

### AI-prosessering

Det finnes ingen \`/api/ai\`-ruter. AI-klassifisering kjører automatisk i
Celery-bakgrunnsarbeideren når et gjenstandsbilde lastes opp; resultatene
havner på gjenstanden (\`ai_names\`, \`ai_descriptions\`, eierforslag) og
bildene (\`ai_tags\`, \`ai_description\`). Manuelle omkjøringer bruker
\`reprocess\`- / \`process-all-images\`-endepunktene under \`/api/items\`,
og konfigurasjonen ligger på \`/api/admin/openai\`.

### Utvokst

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/outgrown | List gjenstander husstanden har vokst fra, med valgfrie arve-til-forslag |

### Triage / Rydding

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/triage/next | Tilfeldig kvalifisert gjenstand (\`?owner_id=&tag=\`) |
| POST | /api/triage/{id}/decide | Body \`{decision: "love"\\|"undecided"\\|"hate"}\` |
| POST | /api/triage/{id}/undo | Fjern en avgjørelse |
| POST | /api/triage/{id}/mark-donated | Myk sletting med "donated"-oppføring i aktivitetsloggen |
| GET | /api/triage/filters | Nedtrekksvalg for eier + topp-30-etiketter |
| GET | /api/triage/discard | Uønskede gjenstander gruppert etter beholdersti |

Nedkjølingstidene er hardkodet: love = 12 måneder, undecided = 3 måneder,
hate = ingen nedkjøling (gjenstanden havner i kastebunken).

### Inventar

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/inventory/tree | Fullt sted → beholder → gjenstand-tre («godview») |
| POST | /api/inventory/{id}/move | Flytt en beholder til nytt sted/ny forelder |

### Aktivitet og eksport

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/activity | Aktivitetslogg (admins ser alles) |
| GET | /api/activity/my | Gjeldende brukers aktivitet |
| GET | /api/export/json | Full JSON-eksport |
| GET | /api/export/csv | CSV-eksport |

### API-nøkler

Administreres fra Admin-fanen. Nøkler har scopes (\`read\`, \`write\`,
\`search\`, \`webhooks\`, \`admin\`) og autentiserer eksterne klienter som
Home Assistant-integrasjonen.

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/api-keys | List API-nøkler |
| POST | /api/api-keys | Opprett nøkkel (hemmeligheten vises én gang) |
| GET | /api/api-keys/{id} | Hent nøkkel |
| PATCH | /api/api-keys/{id} | Oppdater nøkkel |
| DELETE | /api/api-keys/{id} | Trekk tilbake nøkkel |

### Webhooks

Webhooks kan administreres her, men hendelseslevering er ennå ikke
koblet på i appen — bare testendepunktet sender faktisk noe.

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/webhooks | List webhooks |
| POST | /api/webhooks | Opprett webhook |
| GET | /api/webhooks/events | Tilgjengelige hendelsestyper |
| GET | /api/webhooks/{id} | Hent webhook |
| PATCH | /api/webhooks/{id} | Oppdater webhook |
| DELETE | /api/webhooks/{id} | Slett webhook |
| POST | /api/webhooks/{id}/test | Send en testleveranse |
| GET | /api/webhooks/{id}/deliveries | Siste leveranser |

### Home Assistant

Et leseorientert API under \`/api/ha/*\` (status, statistikk,
påminnelser, steder, beholdere, gjenstander, søk, semantisk søk,
etiketter) som brukes av Home Assistant-integrasjonen, autentisert med
API-nøkkel.

### Sikkerhetskopier

Sikkerhetskopisystem med flere tilbydere under \`/api/backup/*\`:
konfigurasjoner og tidsplaner (kjøres av Celery beat), \`create\` på
forespørsel, historikk med nedlasting, JSON-eksport via
\`quick-download\`, gjenoppretting
(\`upload\`/\`execute\`/\`from-history\`, flettegjenoppretting inn i
eksisterende data) og tilbyderoperasjoner for Google Drive
(tjenestekonto) og Dropbox (test, list, opplasting, nedlasting,
sletting).

### SSL

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/ssl | Hent SSL-konfigurasjon |
| GET | /api/ssl/status | Sertifikatstatus |
| PATCH | /api/ssl | Oppdater konfigurasjon |
| POST | /api/ssl/generate | Utsted sertifikat (Let's Encrypt) |
| POST | /api/ssl/renew | Forny sertifikat |
| POST | /api/ssl/test | Test konfigurasjon |

### Admin

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | /api/admin/stats | Systemstatistikk |
| GET | /api/admin/users | List alle brukere |
| POST | /api/admin/users | Opprett bruker |
| PATCH | /api/admin/users/{id} | Oppdater bruker |
| DELETE | /api/admin/users/{id} | Slett bruker |
| GET | /api/admin/activity | Aktivitetslogger |
| GET | /api/admin/usage-stats | AI-bruk og kostnadsstatistikk |
| GET | /api/admin/openai | Les OpenAI-konfigurasjon |
| PUT | /api/admin/openai | Oppdater OpenAI-konfig. (inkl. \`owner_suggestion_enabled\`) |
| GET | /api/admin/languages | Les AI-språkinnstillinger |
| PUT | /api/admin/languages | Oppdater AI-språkinnstillinger |
| POST | /api/admin/recompute-size-ages | Etterfyll \`size_age_min/max_months\` for gjenstander med størrelse men uten aldersspenn |

Det finnes ikke noe \`/api/admin/settings\`-endepunkt — innstillingene er
fordelt på \`/api/admin/openai\`, \`/api/admin/languages\`, \`/api/ssl\` og
\`/api/backup\`.
`
		}
	}
];
