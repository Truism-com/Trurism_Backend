#!/bin/bash
set -e

# Azure App Service startup script
# This script handles the virtual environment activation and starts the application

echo "Starting Travel Booking Platform on Azure..."

# Oryx builds antenv at a hashed path under /tmp, not /antenv
# Activate whichever virtualenv Oryx created, then hand off to gunicorn
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
echo "Starting Gunicorn server..."

# Start Gunicorn with Uvicorn workers
# Settings optimized for Azure App Service
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
