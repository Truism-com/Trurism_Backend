#!/bin/sh
set -e

# Wait for database to be ready (optional but recommended)
echo "Waiting for database to be ready..."
sleep 5

# Run database migrations
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Database migrations completed successfully"
else
    echo "WARNING: Database migrations failed. Attempting to continue..."
    # Don't exit - let the app try to start anyway
fi

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1

