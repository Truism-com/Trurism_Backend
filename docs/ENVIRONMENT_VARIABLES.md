# Environment Variables Configuration

> **Version:** 1.0.0  
> **Last Updated:** February 2026  
> **Platform:** Travel Booking Platform

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Required Variables](#required-variables)
- [Optional Variables](#optional-variables)
- [Sample Configuration](#sample-configuration)
- [Environment-Specific Settings](#environment-specific-settings)
- [Security Best Practices](#security-best-practices)

---

## Overview

This document outlines all environment variables required to configure the Travel Booking Platform. Variables are loaded from a `.env` file in the project root directory using Pydantic Settings.

**Configuration Loading Order:**
1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

---

## Quick Start

1. Copy `.env.example` to `.env`
2. Update required variables with your values
3. Ensure `JWT_SECRET_KEY` is set for production

```bash
cp .env.example .env
```

---

## Required Variables

### Core Application

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `DATABASE_URL` | string | **Yes** | - | PostgreSQL connection string |
| `JWT_SECRET_KEY` | string | **Yes*** | `""` | JWT signing key (required in production) |
| `ENVIRONMENT` | string | No | `development` | `development` \| `staging` \| `production` |

> **Note:** `JWT_SECRET_KEY` must be set when `ENVIRONMENT=production`

### Database Connection String Format

```
postgresql+asyncpg://username:password@host:port/database_name
```

**Examples:**
```bash
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/travel_booking

# Supabase
DATABASE_URL=postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres

# Render
DATABASE_URL=postgresql+asyncpg://user:pass@oregon-postgres.render.com/travel_db
```

> **Note:** The system automatically converts `postgresql://` to `postgresql+asyncpg://` and handles SSL configuration for remote databases.

---

## Optional Variables

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | string | `Travel Booking Platform` | Application display name |
| `APP_VERSION` | string | `1.0.0` | Application version |
| `DEBUG` | boolean | `false` | Enable debug mode (enables SQL logging) |

### Database Pool Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_POOL_SIZE` | integer | `10` | Number of permanent connections |
| `DATABASE_MAX_OVERFLOW` | integer | `20` | Additional connections when pool is full |

### CORS & Security

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORS_ORIGINS` | string | `*` | Comma-separated allowed origins or `*` |
| `TRUSTED_HOSTS` | string | `*` | Comma-separated trusted hosts |

**Examples:**
```bash
# Allow specific origins
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Allow all origins (development only)
CORS_ORIGINS=*
```

### JWT & Token Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JWT_ALGORITHM` | string | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `120` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | integer | `7` | Refresh token TTL in days |
| `BCRYPT_ROUNDS` | integer | `12` | Password hashing cost factor |
| `RATE_LIMIT_PER_MINUTE` | integer | `60` | API rate limit per user |

### Redis Configuration (Optional)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | `None` | Redis connection URL |
| `REDIS_DB` | integer | `0` | Redis database number |
| `SEARCH_CACHE_TTL` | integer | `900` | Search results cache TTL (seconds) |
| `SESSION_CACHE_TTL` | integer | `3600` | Session cache TTL (seconds) |

**Redis URL Format:**
```bash
REDIS_URL=redis://username:password@host:port
REDIS_URL=redis://localhost:6379
```

### Celery Background Tasks (Optional)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CELERY_BROKER_URL` | string | `None` | Message broker URL |
| `CELERY_RESULT_BACKEND` | string | `None` | Task result storage URL |

### Payment Gateway - Razorpay

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RAZORPAY_KEY_ID` | string | `""` | Razorpay API Key ID |
| `RAZORPAY_KEY_SECRET` | string | `""` | Razorpay API Key Secret |
| `RAZORPAY_WEBHOOK_SECRET` | string | `""` | Webhook signature verification secret |

**Getting Razorpay Credentials:**
1. Sign up at [Razorpay Dashboard](https://dashboard.razorpay.com)
2. Navigate to Settings → API Keys
3. Generate keys for Test/Live mode
4. For webhooks: Settings → Webhooks → Add New Webhook

### External Flight API - XML.Agency

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `XML_AGENCY_BASE_URL` | string | `https://api.xmlagency.com` | API base URL |
| `XML_AGENCY_USERNAME` | string | `""` | API username |
| `XML_AGENCY_PASSWORD` | string | `""` | API password |
| `XML_AGENCY_TIMEOUT` | integer | `30` | Request timeout (seconds) |

### Generic External APIs

#### Flight API
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FLIGHT_API_URL` | string | `""` | Flight provider API URL |
| `FLIGHT_API_KEY` | string | `""` | API key |
| `FLIGHT_API_SECRET` | string | `""` | API secret |

#### Hotel API
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HOTEL_API_URL` | string | `""` | Hotel provider API URL |
| `HOTEL_API_KEY` | string | `""` | API key |
| `HOTEL_API_SECRET` | string | `""` | API secret |

#### Bus API
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BUS_API_URL` | string | `""` | Bus provider API URL |
| `BUS_API_KEY` | string | `""` | API key |
| `BUS_API_SECRET` | string | `""` | API secret |

### Email/SMTP Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAIL_SERVER` | string | `smtp.gmail.com` | SMTP server hostname |
| `MAIL_PORT` | integer | `587` | SMTP port |
| `MAIL_FROM` | string | `""` | Sender email address |
| `MAIL_PASSWORD` | string | `""` | SMTP password or app password |

**Gmail Configuration:**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_FROM=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use App Password, not account password
```

### File Upload

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_FILE_SIZE` | integer | `10485760` | Maximum upload size in bytes (10MB) |

### Special Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SKIP_DB_INIT` | boolean | `false` | Skip database initialization on startup |

---

## Sample Configuration

### Development Environment

```env
# ============================================
# DEVELOPMENT ENVIRONMENT CONFIGURATION
# ============================================

# Application
APP_NAME=Travel Booking Platform
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Database (Local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/travel_booking
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=10
RATE_LIMIT_PER_MINUTE=100

# CORS (Allow all in development)
CORS_ORIGINS=*
TRUSTED_HOSTS=*

# Redis (Optional for development)
# REDIS_URL=redis://localhost:6379
# REDIS_DB=0

# Razorpay (Test Mode)
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=

# Email (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_FROM=
MAIL_PASSWORD=

# Skip DB init for faster restarts (optional)
# SKIP_DB_INIT=false
```

### Production Environment

```env
# ============================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================

# Application
APP_NAME=Travel Booking Platform
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Database (Remote PostgreSQL with SSL)
DATABASE_URL=postgresql+asyncpg://user:secure_password@db.example.com:5432/production_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Security (STRONG VALUES REQUIRED)
JWT_SECRET_KEY=your-ultra-secure-random-string-minimum-64-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
RATE_LIMIT_PER_MINUTE=60

# CORS (Restrict to your domains)
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
TRUSTED_HOSTS=app.yourdomain.com,admin.yourdomain.com,api.yourdomain.com

# Redis (Required for production)
REDIS_URL=redis://username:password@redis.example.com:6379
REDIS_DB=0
SEARCH_CACHE_TTL=900
SESSION_CACHE_TTL=3600

# Celery (Required for background tasks)
CELERY_BROKER_URL=redis://username:password@redis.example.com:6379/1
CELERY_RESULT_BACKEND=redis://username:password@redis.example.com:6379/2

# Razorpay (Live Mode)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# External APIs
XML_AGENCY_BASE_URL=https://api.xmlagency.com
XML_AGENCY_USERNAME=your_username
XML_AGENCY_PASSWORD=your_password
XML_AGENCY_TIMEOUT=30

FLIGHT_API_URL=https://api.flightprovider.com
FLIGHT_API_KEY=your_key
FLIGHT_API_SECRET=your_secret

# Email
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_FROM=noreply@yourdomain.com
MAIL_PASSWORD=your_smtp_password

# File Upload
MAX_FILE_SIZE=10485760
```

---

## Environment-Specific Settings

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| `DEBUG` | `true` | `false` | `false` |
| `DATABASE_POOL_SIZE` | `5` | `10` | `20` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | `15` | `15` |
| `BCRYPT_ROUNDS` | `10` | `12` | `12` |
| `CORS_ORIGINS` | `*` | Specific domains | Specific domains |
| `REDIS_URL` | Optional | Required | Required |

---

## Security Best Practices

### DO ✅

- Use strong, random `JWT_SECRET_KEY` (minimum 64 characters)
- Store `.env` file outside version control
- Use different credentials for each environment
- Rotate secrets periodically
- Use environment-specific API keys (test vs live)
- Enable SSL for database connections in production

### DON'T ❌

- Commit `.env` files to version control
- Use default or weak secret keys in production
- Share production credentials
- Use `CORS_ORIGINS=*` in production
- Disable rate limiting in production

### Generating Secure Secrets

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# OpenSSL
openssl rand -base64 64

# Node.js
node -e "console.log(require('crypto').randomBytes(64).toString('base64'))"
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```
Error: socket.gaierror: [Errno 11001] getaddrinfo failed
```
- Check `DATABASE_URL` format
- Verify database server is accessible
- Check network/firewall settings

**2. JWT Secret Key Error in Production**
```
Error: JWT_SECRET_KEY must be set in production environment
```
- Set `JWT_SECRET_KEY` environment variable
- Ensure it's at least 32 characters

**3. Redis Connection Failed**
```
Error: Connection refused
```
- Verify `REDIS_URL` is correct
- Check Redis server is running
- Verify network access to Redis

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [Deployment Guide](./PRODUCTION_SETUP.md)
- [Security Guide](./architecture/security.md)
