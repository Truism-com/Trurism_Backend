#!/bin/sh
set -e

echo "Starting container..."

# Wait for database
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "$(date) - Running database migrations..."

if timeout 60 alembic upgrade head; then
    echo "$(date) - Database migrations completed successfully"
else
    echo "$(date) - WARNING: Database migrations failed or timed out after 60s."
    echo "Attempting to start the application anyway..."
fi

# Start FastAPI
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1