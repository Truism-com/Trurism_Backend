#!/bin/bash
set -e

# Oryx builds antenv at a hashed path under /tmp, not /antenv
# Activate whichever virtualenv Oryx created, then hand off to gunicorn
ORYX_ENV=$(find /tmp -maxdepth 3 -name activate -path "*/antenv/*" 2>/dev/null | head -1)
if [ -n "$ORYX_ENV" ]; then
    source "$ORYX_ENV"
fi

exec gunicorn app.main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile '-' \
  --error-logfile '-'
