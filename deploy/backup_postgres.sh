#!/usr/bin/env bash
set -euo pipefail
# Run on the host with DB credentials available in the environment.
: "${DB_NAME:?Set DB_NAME}"
: "${DB_USER:?Set DB_USER}"
: "${DB_HOST:=127.0.0.1}"
: "${DB_PORT:=5432}"
: "${BACKUP_DIR:=./backups}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
PGPASSWORD="${DB_PASSWORD:?Set DB_PASSWORD}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/library-$STAMP.dump"
echo "Backup created: $BACKUP_DIR/library-$STAMP.dump"
