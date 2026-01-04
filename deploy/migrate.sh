#!/bin/bash
#
# Run database migrations on production
#
SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
SERVER_USER="${STORAGEHUB_USER:-user}"
PROJECT_DIR="/opt/storagehub"

echo "Running database migrations on ${SERVER_HOST}..."

ssh "${SERVER_USER}@${SERVER_HOST}" bash << REMOTE
cd ${PROJECT_DIR}
docker compose exec -T backend alembic upgrade head
REMOTE

echo "Migrations complete!"
