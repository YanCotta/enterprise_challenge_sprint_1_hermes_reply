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

# Restore original DATABASE_URL for the application
export DATABASE_URL="$ORIGINAL_DATABASE_URL"

# Start the FastAPI server
echo "Starting FastAPI server..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000