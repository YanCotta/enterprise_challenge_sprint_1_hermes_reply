#!/bin/bash
set -e

echo "Starting API server..."
echo "PATH: $PATH"
echo "PYTHONPATH: $PYTHONPATH"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI server
echo "Starting FastAPI server..."
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000