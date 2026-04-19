#!/bin/sh
set -e

# Wait for database to be ready (optional but recommended)
echo "Waiting for database to be ready..."
sleep 5

# Run database migrations
echo "$(date) - Running database migrations..."
# Set a local timeout for migration - if it takes more than 60s, something is wrong
# but we still want to try starting the app.
if timeout 60 alembic upgrade head; then
    echo "$(date) - Database migrations completed successfully"
else
    echo "$(date) - WARNING: Database migrations failed or timed out after 60s."
    echo "This is likely due to database firewall settings or incorrect credentials."
    echo "Attempting to start the application anyway..."
fi

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1

