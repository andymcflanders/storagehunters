# StorageHub

A self-hosted web application for tracking personal belongings across multiple storage locations.

## Features

- **Location Management**: Organize your storage by locations (garage, loft, storage units)
- **Container Tracking**: Create containers with QR codes for easy identification
- **Item Catalog**: Track items with photos, descriptions, and metadata
- **AI Image Tagging**: Automatic image classification using AI (OpenAI Vision)
- **Label Printing**: Print QR-coded labels for containers
- **PWA Support**: Install as an app with offline capabilities

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
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

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
