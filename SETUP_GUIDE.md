# 🚀 Complete Setup Guide for Trurism Travel Booking Platform

## 📋 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Python Packages** | ✅ All Installed | razorpay just installed |
| **Module Imports** | ✅ All Working | No syntax errors |
| **Database** | ❌ **NOT WORKING** | Supabase project doesn't exist |
| **Razorpay** | ❌ Not Configured | Keys missing in .env |
| **Redis** | ⚠️ Disabled | Set to `none` |
| **Email** | ⚠️ Not Configured | Placeholder values |

---

## 🔴 STEP 1: Fix Database (CRITICAL)

Your Supabase project `bpnbypsvkmgzetosqcbl` **does not exist**. You need to:

### Option A: Create New Supabase Project (Recommended)

1. **Go to Supabase Dashboard:**
   ```
   https://supabase.com/dashboard
   ```

2. **Create New Project:**
   - Click "New Project"
   - Choose organization
   - Set Project Name: `trurism-travel`
   - Set Database Password: (save this securely!)
   - Select Region: Choose closest to you
   - Click "Create new project"
   - **Wait 2-3 minutes** for project to be ready

3. **Get Connection Details:**
   - Go to: Project Settings → Database
   - Scroll to "Connection String"
   - Copy "URI" (Direct connection - Port 5432)
   - Replace `[YOUR-PASSWORD]` with your database password

4. **Get API Keys:**
   - Go to: Project Settings → API
   - Copy:
     - Project URL → `SUPABASE_URL`
     - `service_role` secret → `SUPABASE_SERVICE_KEY`

### Option B: Use Local PostgreSQL (For Development)

```powershell
# Install PostgreSQL locally
# Download from: https://www.postgresql.org/download/windows/

# Create database
createdb trurism_db

# Use local connection:
# DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/trurism_db
# DATABASE_MIGRATION_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/trurism_db
```

---

## 📝 STEP 2: Update .env File

Replace your `.env` file with these values. Fill in the **PLACEHOLDER** values:

```env
# ============================================
# TRAVEL BOOKING PLATFORM - ENVIRONMENT VARIABLES
# ============================================

# --------------------------------------------
# APPLICATION SETTINGS
# --------------------------------------------
APP_NAME=Travel Booking Platform
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
SKIP_DB_INIT=false

# --------------------------------------------
# DATABASE CONFIGURATION (SUPABASE)
# --------------------------------------------
# ⚠️ REPLACE THESE WITH YOUR ACTUAL SUPABASE CREDENTIALS

# From Supabase Dashboard → Project Settings → API
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# Connection pool settings
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# From Supabase Dashboard → Project Settings → Database → Connection String
# IMPORTANT: Replace [YOUR-PASSWORD] with actual password
# IMPORTANT: Replace YOUR_PROJECT_REF with your project reference
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
DATABASE_MIGRATION_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres

# --------------------------------------------
# REDIS CACHE CONFIGURATION
# --------------------------------------------
# For now, keep disabled. Enable when needed.
REDIS_URL=none
REDIS_DB=0
SEARCH_CACHE_TTL=900
SESSION_CACHE_TTL=3600

# --------------------------------------------
# JWT AUTHENTICATION
# --------------------------------------------
# Generate new secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=BkZsGSThYtgN8atowMvwol4d36mat4jltyUcgwhDVYA
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# --------------------------------------------
# SECURITY SETTINGS
# --------------------------------------------
BCRYPT_ROUNDS=12
RATE_LIMIT_PER_MINUTE=60

# --------------------------------------------
# CELERY / BACKGROUND TASKS
# --------------------------------------------
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# --------------------------------------------
# EXTERNAL API: XML.AGENCY
# --------------------------------------------
XML_AGENCY_BASE_URL=https://test-api.xml.agency
XML_AGENCY_USERNAME=
XML_AGENCY_PASSWORD=
XML_AGENCY_TIMEOUT=30

# --------------------------------------------
# PAYMENT GATEWAY: RAZORPAY
# --------------------------------------------
# ⚠️ REPLACE WITH YOUR ACTUAL RAZORPAY CREDENTIALS
# Get from: https://dashboard.razorpay.com/#/app/keys
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXX
RAZORPAY_KEY_SECRET=your_key_secret_here
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret_here

# --------------------------------------------
# EMAIL CONFIGURATION
# --------------------------------------------
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_FROM=your-email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_USE_TLS=true

# --------------------------------------------
# FILE UPLOAD SETTINGS
# --------------------------------------------
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=.jpg,.jpeg,.png,.pdf

# --------------------------------------------
# LOGGING
# --------------------------------------------
LOG_LEVEL=INFO
```

---

## 🔧 STEP 3: Get Razorpay Credentials

1. **Login to Razorpay Dashboard:**
   ```
   https://dashboard.razorpay.com
   ```

2. **Generate API Keys:**
   - Go to: Settings → API Keys
   - Click "Generate Key"
   - Choose "Test Mode" for development
   - Copy:
     - `Key ID` → `RAZORPAY_KEY_ID`
     - `Key Secret` → `RAZORPAY_KEY_SECRET`

3. **Configure Webhook (After Deployment):**
   - Go to: Settings → Webhooks
   - Click "Add New Webhook"
   - URL: `https://yourdomain.com/payments/webhook`
   - Select Events:
     - `payment.captured`
     - `payment.failed`
     - `order.paid`
     - `refund.processed`
   - Copy Webhook Secret → `RAZORPAY_WEBHOOK_SECRET`

---

## 🗃️ STEP 4: Run Database Migrations

Once database is connected:

```powershell
# Activate virtual environment
& H:\Trurism\venv\Scripts\Activate.ps1

# Test database connection
H:/Trurism/venv/Scripts/python.exe -c "from dotenv import load_dotenv; load_dotenv(); import os; from sqlalchemy import create_engine, text; e = create_engine(os.getenv('DATABASE_MIGRATION_URL')); c = e.connect(); print(c.execute(text('SELECT 1')).fetchone()); c.close()"

# Run migrations
H:/Trurism/venv/Scripts/python.exe -m alembic upgrade head
```

---

## 🧪 STEP 5: Verify Setup

```powershell
# Run setup check script
H:/Trurism/venv/Scripts/python.exe setup_check.py
```

All checks should pass.

---

## 🚀 STEP 6: Start the Server

```powershell
# Start FastAPI server
H:/Trurism/venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

## 📊 STEP 7: Test Payment System

### Create Test User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "name": "Test User",
    "role": "customer"
  }'
```

### Login and Get Token
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
# Copy the access_token from response
```

### Create Payment Order
```bash
curl -X POST "http://localhost:8000/payments/create-order" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": 1,
    "booking_type": "flight",
    "base_amount": 5000.0,
    "payment_method": "card"
  }'
```

---

## ⚙️ OPTIONAL: Configure Redis (For Caching)

### Option A: Install Locally

```powershell
# Download Redis for Windows
# From: https://github.com/microsoftarchive/redis/releases

# Or use Docker:
docker run -d --name redis -p 6379:6379 redis:alpine
```

### Option B: Use Cloud Redis (Free Tier)

1. Go to: https://upstash.com
2. Create free Redis database
3. Copy connection URL
4. Update `.env`:
   ```env
   REDIS_URL=redis://default:password@your-redis.upstash.io:6379
   ```

---

## 📧 OPTIONAL: Configure Email

### For Gmail:

1. Enable 2FA on your Google account
2. Go to: https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Update `.env`:
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_FROM=your-email@gmail.com
   MAIL_PASSWORD=your_16_char_app_password
   MAIL_USE_TLS=true
   ```

---

## 🔄 OPTIONAL: Start Celery Workers

Requires Redis to be configured first.

```powershell
# Start Celery worker
celery -A app.celery worker --loglevel=info --pool=solo

# In another terminal, start Celery beat (for scheduled tasks)
celery -A app.celery beat --loglevel=info
```

---

## 📝 Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Async database connection | `postgresql+asyncpg://...` |
| `DATABASE_MIGRATION_URL` | Sync database connection | `postgresql+psycopg://...` |
| `JWT_SECRET_KEY` | JWT signing secret | 32+ character string |
| `RAZORPAY_KEY_ID` | Razorpay API Key ID | `rzp_test_xxx` |
| `RAZORPAY_KEY_SECRET` | Razorpay API Secret | 24 char string |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required for Supabase |
| `SUPABASE_SERVICE_KEY` | Supabase service role | Required for Supabase |
| `REDIS_URL` | Redis connection | `none` (disabled) |
| `ENVIRONMENT` | App environment | `development` |
| `DEBUG` | Debug mode | `true` |
| `SKIP_DB_INIT` | Skip DB initialization | `false` |
| `RAZORPAY_WEBHOOK_SECRET` | Webhook signature secret | Generate in dashboard |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_FROM` | From email address | Your email |
| `MAIL_PASSWORD` | SMTP password | App password |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/2` |

---

## 🔍 Troubleshooting

### Database Connection Failed
```
Error: [Errno 11001] getaddrinfo failed
```
**Cause:** Supabase project doesn't exist or hostname is wrong.
**Fix:** Create new Supabase project and update credentials.

### Razorpay Import Error
```
Error: No module named 'razorpay'
```
**Fix:**
```powershell
H:/Trurism/venv/Scripts/pip.exe install razorpay
```

### Migration Failed
```
Error: Can't proceed with migration
```
**Fix:**
1. Ensure database is connected
2. Check `DATABASE_MIGRATION_URL` uses `postgresql+psycopg://`
3. Run: `alembic current` to see current state
4. Run: `alembic upgrade head` to apply migrations

### Server Won't Start
```
Error: Cannot import module
```
**Fix:**
```powershell
# Check for syntax errors
H:/Trurism/venv/Scripts/python.exe -m py_compile app/main.py

# Check all imports
H:/Trurism/venv/Scripts/python.exe setup_check.py
```

---

## ✅ Final Checklist

Before going to production:

- [ ] Create Supabase project and update credentials
- [ ] Run database migrations
- [ ] Configure Razorpay credentials
- [ ] Test payment flow
- [ ] (Optional) Configure Redis
- [ ] (Optional) Configure email
- [ ] (Optional) Start Celery workers
- [ ] Generate production JWT secret
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure CORS for your domain
- [ ] Set up HTTPS

---

**Created:** January 31, 2026
**Status:** Ready for configuration
