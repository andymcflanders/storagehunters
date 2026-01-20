# StorageHub

A self-hosted web application for tracking personal belongings across multiple storage locations.

## Features

### Core Inventory
- **Location Management**: Organize your storage by locations (garage, loft, storage units)
- **Container Tracking**: Create containers with QR codes for easy identification
- **Nested Containers**: Support for containers within containers (drawers in cabinets)
- **Item Catalog**: Track items with photos, descriptions, and metadata
- **Owner Tracking**: Assign items to family members or users

### AI Features
- **AI Image Classification**: Automatic item identification using OpenAI Vision
- **Multi-Item Detection**: Upload a photo of multiple items, AI separates them automatically
- **Configurable AI Models**: Choose models, adjust temperature, max tokens, and view cost estimates
- **Bilingual Support**: AI-generated descriptions in English and Norwegian
- **Smart Search**: Natural language search with color and synonym understanding

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
- **User Management**: Create and manage user accounts with role-based access
- **AI Configuration**: Configure OpenAI models and segmentation providers
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

The easiest way to run StorageHub is with Docker:

```bash
# Clone the repository
git clone https://github.com/yourusername/storagehub.git
cd storagehub

# Copy environment file
cp .env.docker .env

# (Optional) Edit .env to add your OpenAI API key for AI features
# AI_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

Access the application:
- **Application**: http://localhost
- **API Docs**: http://localhost/docs

To stop:
```bash
docker compose down
```

To reset everything (including data):
```bash
docker compose down -v
```

### Manual Setup (Development)

#### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
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
