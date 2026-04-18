# ---------- STAGE 1: BUILDER ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies (ONLY builder me)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libxml2-dev libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv

# Activate venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt


# ---------- STAGE 2: RUNTIME ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN useradd -m appuser

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv

# Set path
ENV PATH="/opt/venv/bin:$PATH"

# Copy application files
COPY . .

# Make script executable
RUN chmod +x /app/start.sh

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Start app
CMD ["/app/start.sh"]