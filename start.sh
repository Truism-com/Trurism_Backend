#!/bin/sh
set -e

echo "Waiting for database to be ready..."
sleep 5

# Run database migrations — fail hard if they fail.
# The container orchestrator will restart us.
echo "$(date) - Running database migrations..."
alembic upgrade head
echo "$(date) - Database migrations completed successfully"

# Tell the FastAPI app NOT to re-run migrations (avoids double execution
# and lock contention when multiple uvicorn workers start).
export SKIP_DB_INIT=true

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-2}
