#!/bin/bash
#
# Restart production services
#
SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
SERVER_USER="${STORAGEHUB_USER:-john}"
PROJECT_DIR="/opt/storagehub"

SERVICE="${1:-}"

echo "Restarting services on ${SERVER_HOST}..."

if [[ -n "$SERVICE" ]]; then
    ssh "${SERVER_USER}@${SERVER_HOST}" "cd ${PROJECT_DIR} && docker compose restart ${SERVICE}"
else
    ssh "${SERVER_USER}@${SERVER_HOST}" "cd ${PROJECT_DIR} && docker compose restart"
fi

echo "Done!"
