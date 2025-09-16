#!/usr/bin/env bash
set -euo pipefail

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_USER=${DB_USER:-smart_user}
DB_NAME=${DB_NAME:-smart_maintenance_db}
BACKUP_FILE=${1:-}

if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <backup.sql.gz>" >&2
  exit 1
fi

echo "Restoring $DB_NAME from $BACKUP_FILE to $DB_HOST:$DB_PORT"
set +e
PGPASSWORD=${POSTGRES_PASSWORD:-strong_password} dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
set -e
PGPASSWORD=${POSTGRES_PASSWORD:-strong_password} createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
gzip -dc "$BACKUP_FILE" | PGPASSWORD=${POSTGRES_PASSWORD:-strong_password} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
echo "Restore complete."
