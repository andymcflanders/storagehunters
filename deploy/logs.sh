#!/bin/bash
#
# View production logs
#
SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
SERVER_USER="${STORAGEHUB_USER:-user}"
PROJECT_DIR="/opt/storagehub"

SERVICE="${1:-}"

if [[ -n "$SERVICE" ]]; then
    ssh -t "${SERVER_USER}@${SERVER_HOST}" "cd ${PROJECT_DIR} && docker compose logs -f --tail=100 ${SERVICE}"
else
    ssh -t "${SERVER_USER}@${SERVER_HOST}" "cd ${PROJECT_DIR} && docker compose logs -f --tail=50"
fi
