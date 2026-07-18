# StorageHub — common ops
# Run `just` to list available recipes.

set dotenv-load

default:
    @just --list

# Start all services in the background
up:
    docker compose up -d

# Stop all services (preserves data)
down:
    docker compose down

# Rebuild images and restart
build:
    docker compose up -d --build

# Restart all services
restart:
    docker compose restart

# Tail logs for one service or all
logs service="":
    docker compose logs -f {{service}}

# Run pending Alembic migrations against the running backend
migrate:
    docker compose exec backend alembic upgrade head

# Open a shell in the backend container
shell-backend:
    docker compose exec backend bash

# Open a psql shell against the running database
shell-db:
    docker compose exec postgres psql -U "${POSTGRES_USER:-storagehub}" "${POSTGRES_DB:-storagehub}"

# Create the first admin on a FRESH instance (one-shot bootstrap; refuses once any user exists)
admin name email password:
    curl -sS -X POST http://localhost/api/setup/complete \
      -H "Content-Type: application/json" \
      -d '{"admin_name":"{{name}}","admin_email":"{{email}}","admin_password":"{{password}}","admin_language":"en"}'
    @echo

# Generate a fresh SECRET_KEY (paste the output into .env)
genkey:
    @openssl rand -hex 32

# Enable the repo's pre-commit hook (one-time, per clone).
install-hooks:
    git config core.hooksPath .githooks
    @echo "Pre-commit hook enabled. Bypass with: git commit --no-verify"

# Run svelte-check (frontend type-check) in an ephemeral container
check:
    docker run --rm \
      -v "$(pwd)/frontend:/src:ro" \
      -w /work \
      node:20-alpine \
      sh -c "cp -r /src/. /work/ && rm -rf node_modules .svelte-kit && npm install --legacy-peer-deps --no-audit --no-fund --silent && npm run check"

# DESTRUCTIVE: stop services and wipe all data volumes
reset:
    @echo "This will delete the database, uploads, and certs. Press Ctrl+C to cancel."
    @sleep 5
    docker compose down -v
