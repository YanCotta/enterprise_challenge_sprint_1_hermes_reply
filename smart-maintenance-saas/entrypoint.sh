#!/bin/bash
set -e

echo "Starting API server..."
echo "PATH: $PATH"
echo "PYTHONPATH: $PYTHONPATH"

# Run database migrations
echo "Running database migrations..."
# Set migration-specific database URL (direct connection, not through toxiproxy)
export MIGRATION_DATABASE_URL="${DATABASE_URL/toxiproxy:5434/db:5432}"
echo "Migration database URL: $MIGRATION_DATABASE_URL"

# Temporarily override DATABASE_URL for migration
ORIGINAL_DATABASE_URL="$DATABASE_URL"
export DATABASE_URL="$MIGRATION_DATABASE_URL"

alembic upgrade head

# Apply TimescaleDB schema fix (addresses recurring sequence issue from Day 15/21)
echo "Applying TimescaleDB schema fix..."
if [ -f "/app/scripts/fix_timescaledb_schema.sh" ]; then
    # Set environment variables for the fix script
    export DB_HOST="db"
    export DB_PORT="5432"
    export DB_NAME="smart_maintenance_db"
    export DB_USER="smart_user"
    export PGPASSWORD="strong_password"
    
    /app/scripts/fix_timescaledb_schema.sh
else
    echo "Warning: TimescaleDB fix script not found"
fi

# Restore original DATABASE_URL for the application
export DATABASE_URL="$ORIGINAL_DATABASE_URL"

# Start the FastAPI server
echo "Starting FastAPI server..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000