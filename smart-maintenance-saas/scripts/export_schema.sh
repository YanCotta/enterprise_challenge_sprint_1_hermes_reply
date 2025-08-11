#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

: ${DATABASE_URL:="postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db"}

# Convert async URL to sync for pg_dump if necessary
DB_URL_SYNC=${DATABASE_URL/"postgresql+asyncpg"/"postgresql"}

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump not found. Please install postgresql-client (or run inside the API container)." >&2
  exit 1
fi

mkdir -p docs/db
pg_dump --no-owner --no-privileges --schema-only --file docs/db/schema.sql "$DB_URL_SYNC"
echo "Schema exported to docs/db/schema.sql"
