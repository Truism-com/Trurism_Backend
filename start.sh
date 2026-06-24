#!/bin/sh
set -e

echo "Waiting for database to be ready..."

# Retry loop - Supabase pooler can take time to accept connections
MAX_ATTEMPTS=5
ATTEMPT=0
MIGRATION_SUCCESS=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "$(date) - Migration attempt $ATTEMPT of $MAX_ATTEMPTS..."
    if alembic upgrade head; then
        MIGRATION_SUCCESS=true
        break
    fi
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        echo "$(date) - Migration failed, retrying in 10s..."
        sleep 10
    fi
done

if [ "$MIGRATION_SUCCESS" = "false" ]; then
    echo "$(date) - All $MAX_ATTEMPTS migration attempts failed. Aborting."
    exit 1
fi

echo "$(date) - Database migrations completed successfully"

# Tell the FastAPI app NOT to re-run migrations (avoids double execution
# and lock contention when multiple uvicorn workers start).
export SKIP_DB_INIT=true

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-2}
