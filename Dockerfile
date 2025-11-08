FROM python:3.11-slim

# Keep Python output deterministic
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps needed by some Python packages (lxml, asyncpg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev libxml2-dev libxslt1-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application
COPY . .

# Expose default port (Render will supply $PORT env var at runtime)
EXPOSE 8000

# Start the app using Uvicorn. Render provides $PORT; fallback to 8000.
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
