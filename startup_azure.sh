#!/bin/bash
set -e

# Azure App Service startup script
echo "Starting Travel Booking Platform on Azure..."

# Oryx builds antenv at a hashed path under /tmp, not /antenv
ORYX_ENV=$(find /tmp -maxdepth 3 -name activate -path "*/antenv/*" 2>/dev/null | head -1)
if [ -n "$ORYX_ENV" ]; then
    echo "Activating Oryx virtualenv: $ORYX_ENV"
    source "$ORYX_ENV"
else
    echo "Warning: Could not find Oryx virtualenv, proceeding without activation"
fi

# Verify Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python not found in PATH"
    exit 1
fi

echo "Python version: $(python --version)"

# Run database migrations before starting the app
echo "$(date) - Running database migrations..."
python -m alembic upgrade head
echo "$(date) - Database migrations completed successfully"

# Skip in-app migration to avoid double execution
export SKIP_DB_INIT=true

echo "Starting Gunicorn server..."

# Start Gunicorn with Uvicorn workers
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile '-' \
  --error-logfile '-' \
  --log-level info
