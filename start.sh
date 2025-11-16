#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || echo "Migration failed, continuing anyway..."

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1

