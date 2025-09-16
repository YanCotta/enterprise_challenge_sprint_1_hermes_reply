#!/usr/bin/env bash
set -euo pipefail

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_USER=${DB_USER:-smart_user}
DB_NAME=${DB_NAME:-smart_maintenance_db}
BACKUP_DIR=${BACKUP_DIR:-./backups}

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Backing up $DB_NAME from $DB_HOST:$DB_PORT to $FILE"
PGPASSWORD=${POSTGRES_PASSWORD:-strong_password} pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" | gzip > "$FILE"
echo "Backup complete: $FILE"
