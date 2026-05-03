# StorageHub

A self-hosted web application for tracking personal belongings across multiple storage locations.

## Features

### Core Inventory
- **Location Management**: Organize your storage by locations (garage, loft, storage units)
- **Container Tracking**: Containers with type (box, drawer, shelf, …), QR code, and an
  optional hero image you can snap with the device camera
- **Nested Containers**: Support for containers within containers (drawers in cabinets)
- **Item Catalog**: Track items with photos, descriptions, and metadata
- **Owner Tracking**: Assign items to family members or users

### AI Features
- **AI Image Classification**: Automatic item identification using OpenAI Vision
- **Configurable AI Models**: Choose models, adjust temperature, max tokens, and view cost estimates
- **Multi-language Translations**: AI generates names and descriptions in every language
  configured under Admin → AI Settings (defaults to English + Norwegian; add more with a
  config tweak — no code or migration required)
- **Smart Search**: Natural-language query understanding with color and clothing-type
  synonyms across both languages (e.g. "rød ullgenser" matches an item named "Red Wool
  Cardigan")

### User Interface
- **God View**: Complete inventory tree with inline editing and drag-and-drop
- **Dark Mode**: Full dark theme support
- **PWA Support**: Install as an app with offline capabilities
- **QR Scanner**: Built-in scanner for quick container access

### Printing & Labels
- **Label Printing**: Print QR-coded labels for containers
- **Batch Printing**: Print labels for all containers in a location from God View
- **AI Summaries**: Auto-generated container content summaries on labels
- **Multiple Printer Support**: Zebra ZPL, Brother QL, and PDF output

### Backup & Restore
- **Full Backup**: Export complete database as downloadable archive
- **Google Drive Sync**: Automatic backups to Google Drive
- **Point-in-Time Restore**: Restore from any backup
- **Scheduled Backups**: Configure automatic backup frequency

### Sharing & Collaboration
- **Share Links**: Create public links for containers without requiring login
- **Reminders**: Set recurring reminders for maintenance, expiration, restocking
- **Activity Logs**: Complete audit trail of all changes

### Admin Features
- **First-run Setup Wizard**: A clean install lands on `/setup` to create the admin
  account, optionally save an OpenAI API key, pick AI languages, and add the first
  location — no `curl` ceremony required
- **Separate Admin Identity**: Admins sign in via email + password through an
  "Administer this instance" link on the login screen; they're hidden from the
  household card grid so they don't get used as everyday accounts
- **User Management**: Create and manage user accounts with role-based access
- **AI Configuration**: Configure OpenAI models, temperature, max tokens, view cost
  estimates, and rotate the API key — all from the admin panel
- **System Statistics**: Dashboard with usage metrics and growth trends

## Tech Stack

### Backend
- Python 3.11+ with FastAPI
- PostgreSQL database
- SQLAlchemy ORM with Alembic migrations
- Celery + Redis for background tasks

### Frontend
- SvelteKit with TypeScript
- Tailwind CSS
- PWA with offline support

## Getting Started

### Quick Start with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/storagehub.git
cd storagehub

# Create .env from the template
cp .env.example .env

# Set the two required values (compose will refuse to start without them):
#   SECRET_KEY        — generate with: openssl rand -hex 32
#   POSTGRES_PASSWORD — any strong password
# Optionally also set:
#   AI_PROVIDER=openai and OPENAI_API_KEY=sk-... for AI features

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

Access the application:
- **Application**: http://localhost (or https://localhost — nginx generates a
  self-signed cert on first boot, so HTTPS works without any extra setup)
- **API Docs**: http://localhost/docs

**First visit**: the app detects an empty database and redirects you to `/setup`.
The wizard walks you through creating the admin account, pasting an OpenAI key
(optional, can be added later), picking AI languages, and adding your first
location. After you click "Open StorageHub" you're already logged in.

To stop:
```bash
docker compose down
```

To reset everything (including data):
```bash
docker compose down -v
```

### Common operations via `just`

A `justfile` at the repo root wraps the most-used commands:

```bash
just up              # docker compose up -d
just down            # stop, keep data
just build           # rebuild images and start
just logs backend    # tail logs for one service
just check           # run frontend type checks (svelte-check)
just genkey          # generate a fresh SECRET_KEY
just shell-db        # psql into the running database
just install-hooks   # one-time: enable .githooks/pre-commit
just reset           # DESTRUCTIVE: down -v
```

### Production Checklist

When deploying to a real server (single VPS, cloud, etc.):

1. **Generate a strong `SECRET_KEY`**: `openssl rand -hex 32`
2. **Set a strong `POSTGRES_PASSWORD`** in `.env` (don't reuse the example)
3. **Set `FRONTEND_URL`** to the public URL where users will reach the app
   (e.g. `https://storagehub.example.com`). This is used for QR codes and
   share links — wrong values will produce broken links.
4. **Set `CORS_ORIGINS`** if the app is reachable at additional URLs (LAN IP,
   alternate domains). Comma-separated.
5. **Configure HTTPS** — nginx auto-generates a self-signed cert on first boot
   so HTTPS works immediately. For a real domain, use the bundled `certbot`
   service to obtain a Let's Encrypt cert; the SSL admin panel can also accept
   a custom upload. See `deploy/README.md`.
6. **Back up regularly** — use the in-app Admin → Backups panel, or the
   `deploy/backup.sh` script for CLI dumps.

The deployment is portable: the same `docker-compose.yml` works on a single
VPS, a cloud VM, or any platform that runs Docker Compose (Coolify, Dokploy,
etc.). The `deploy/` directory contains optional helpers for an SSH-based
laptop→server workflow.

### Manual Setup (Development)

#### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis (for Celery)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example ../.env
# Edit .env with your database credentials

# Create database
createdb storagehub

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Access (Manual Setup)

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secure key for session tokens
- `OPENAI_API_KEY`: API key for AI image classification

## Project Structure

```
storagehub/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI app
│   └── alembic/           # Database migrations
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/       # API client
│   │   │   ├── components/# Svelte components
│   │   │   └── stores/    # Svelte stores
│   │   └── routes/        # SvelteKit pages
│   └── static/            # Static assets
└── uploads/               # Image storage
```

## License

MIT
