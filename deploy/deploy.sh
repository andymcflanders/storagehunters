#!/bin/bash
#
# StorageHub Deploy Script
# Deploys the latest code to the production server
#
set -e

# Configuration
SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
SERVER_USER="${STORAGEHUB_USER:-user}"
PROJECT_DIR="/opt/storagehub"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
BUILD_FLAG=""
MIGRATE_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            BUILD_FLAG="--build"
            shift
            ;;
        --migrate|-m)
            MIGRATE_FLAG="yes"
            shift
            ;;
        --help|-h)
            echo "Usage: deploy.sh [options]"
            echo ""
            echo "Options:"
            echo "  --build, -b    Force rebuild of containers"
            echo "  --migrate, -m  Run database migrations after deploy"
            echo "  --help, -h     Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "  StorageHub Deployment"
echo "=========================================="
echo ""
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "Time: $(date)"
echo ""

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "WARNING: You have uncommitted changes!"
    echo ""
    git status --short
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check SSH access
echo "==> Checking SSH access..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_HOST}" "echo 'OK'" 2>/dev/null; then
    echo "ERROR: Cannot connect to server. Check SSH key setup."
    exit 1
fi

# Check if .env.production exists
ENV_FILE="${SCRIPT_DIR}/.env.production"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: ${ENV_FILE} not found!"
    echo ""
    echo "Create it from the example:"
    echo "  cp deploy/.env.production.example deploy/.env.production"
    echo "  nano deploy/.env.production"
    exit 1
fi

# Sync code to server
echo "==> Syncing code to server..."
rsync -avz --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude '.env.local' \
    --exclude 'deploy/.env.production' \
    --exclude 'data/' \
    --exclude 'uploads/' \
    --exclude '.venv' \
    --exclude 'venv' \
    "${PROJECT_ROOT}/" \
    "${SERVER_USER}@${SERVER_HOST}:${PROJECT_DIR}/"

# Copy production environment file
echo "==> Copying environment configuration..."
scp "${ENV_FILE}" "${SERVER_USER}@${SERVER_HOST}:${PROJECT_DIR}/.env"

# Deploy on server
echo "==> Starting deployment on server..."
ssh "${SERVER_USER}@${SERVER_HOST}" bash << REMOTE_DEPLOY
set -e
cd ${PROJECT_DIR}

echo "==> Pulling/building containers..."
docker compose pull --ignore-pull-failures 2>/dev/null || true
docker compose build ${BUILD_FLAG}

echo "==> Stopping old containers..."
docker compose down --remove-orphans || true

echo "==> Starting new containers..."
docker compose up -d

echo "==> Waiting for services to be healthy..."
sleep 5

# Show container status
echo ""
echo "==> Container status:"
docker compose ps

REMOTE_DEPLOY

# Run migrations if requested
if [[ "$MIGRATE_FLAG" == "yes" ]]; then
    echo ""
    echo "==> Running database migrations..."
    ssh "${SERVER_USER}@${SERVER_HOST}" bash << REMOTE_MIGRATE
cd ${PROJECT_DIR}
docker compose exec -T backend alembic upgrade head
REMOTE_MIGRATE
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Application should be available at:"
echo "  https://${SERVER_HOST}  (HTTPS - recommended)"
echo "  http://${SERVER_HOST}   (HTTP fallback)"
echo ""
echo "Useful commands:"
echo "  ./deploy/logs.sh          - View logs"
echo "  ./deploy/logs.sh backend  - View backend logs"
echo "  ssh ${SERVER_USER}@${SERVER_HOST}  - SSH to server"
echo ""
