#!/bin/bash
#
# Backup production database
#
SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
SERVER_USER="${STORAGEHUB_USER:-user}"
PROJECT_DIR="/opt/storagehub"
BACKUP_DIR="./backups"

mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/storagehub_${TIMESTAMP}.sql.gz"

echo "Backing up database from ${SERVER_HOST}..."

ssh "${SERVER_USER}@${SERVER_HOST}" "cd ${PROJECT_DIR} && docker compose exec -T postgres pg_dump -U storagehub storagehub" | gzip > "${BACKUP_FILE}"

echo "Backup saved to: ${BACKUP_FILE}"
ls -lh "${BACKUP_FILE}"
