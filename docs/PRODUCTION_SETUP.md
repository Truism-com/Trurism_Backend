# Production Deployment Checklist

## 🔧 Environment Variables Required for Production

This guide explains what needs to be added to your `.env` file to make the platform production-ready.

---

## ✅ What You Already Have (Working)

These are already configured and working:

- ✅ `DATABASE_URL` - PostgreSQL connection
- ✅ `REDIS_URL` - Redis for caching
- ✅ `JWT_SECRET_KEY` - Authentication (⚠️ change for production!)
- ✅ Basic app configuration

---

## ❌ What You MUST Add for Production

### 1. **XML.AGENCY Flight API Credentials** 🔴 CRITICAL

**Current Status:** Empty (using mock data)

```bash
# Required for real flight search and booking
XML_AGENCY_USERNAME=your_xml_agency_username
XML_AGENCY_PASSWORD=your_xml_agency_password
```

**How to get credentials:**

1. Visit: https://xml.agency/
2. Sign up for an account
3. Review the documentation in: `XML Agency Flight API.pdf` (already in your repo)
4. Get your API credentials from the dashboard
5. Add them to `.env`

**What this enables:**
- ✅ Real-time flight search
- ✅ Live flight availability
- ✅ Actual airline bookings
- ✅ Real pricing

---

### 2. **Razorpay Payment Gateway** 🔴 CRITICAL

**Current Status:** Empty (using 90% random success mock)

```bash
# Required for real payment processing
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxx
```

**How to get credentials:**

1. Visit: https://razorpay.com/
2. Sign up for a business account
3. Complete KYC verification (for live keys)
4. Dashboard: https://dashboard.razorpay.com/#/app/keys

**Test vs Live Keys:**
- **Test keys** (for development): `rzp_test_xxxxx`
- **Live keys** (for production): `rzp_live_xxxxx`

**What this enables:**
- ✅ Real payment processing
- ✅ Credit/Debit card payments
- ✅ UPI payments
- ✅ Net banking
- ✅ Payment verification
- ✅ Refund processing

---

### 3. **Email Configuration** ⚠️ IMPORTANT

**Current Status:** Placeholder values

```bash
MAIL_FROM=noreply@yourdomain.com
MAIL_PASSWORD=your-gmail-app-password
```

**Gmail Setup (if using Gmail):**

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Create password for "Mail"
   - Use the 16-character password (not your regular password)

**Alternative Email Services:**
- SendGrid (recommended for production)
- Amazon SES
- Mailgun
- SMTP2GO

**What this enables:**
- ✅ Booking confirmation emails
- ✅ Password reset emails
- ✅ Agent approval notifications
- ✅ Payment receipts

---

### 4. **Security: JWT Secret Key** 🔴 CRITICAL for Production

**Current Status:** Weak placeholder

```bash
# Current (INSECURE for production)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-to-random-string

# Generate a strong key:
```

**Generate a secure key:**

```bash
# Run this command:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output:
# xK8vN2mP9qR4sT6uW7yZ1aB3cD5eF7gH9iJ0kL2mN4oP6qR8sT0uV2wX4yZ6
```

**⚠️ NEVER commit the real secret key to Git!**

---

### 5. **Celery Configuration** ⚠️ OPTIONAL (but recommended)

**Current Status:** Empty

```bash
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

**What this enables:**
- ✅ Background email sending
- ✅ Async booking confirmations
- ✅ Report generation
- ✅ Scheduled tasks

**Already in your `.env`:** These are now added! ✅

---

## 📋 Complete Production `.env` Checklist

### Critical (Must Have for Production)
- [ ] `XML_AGENCY_USERNAME` - Get from xml.agency
- [ ] `XML_AGENCY_PASSWORD` - Get from xml.agency
- [ ] `RAZORPAY_KEY_ID` - Get from razorpay.com
- [ ] `RAZORPAY_KEY_SECRET` - Get from razorpay.com
- [ ] `JWT_SECRET_KEY` - Generate strong random key
- [ ] `MAIL_FROM` - Your email address
- [ ] `MAIL_PASSWORD` - App-specific password

### Important (Recommended)
- [ ] `ENVIRONMENT=production` - When deploying
- [ ] `DEBUG=false` - When deploying
- [ ] `CELERY_BROKER_URL` - For background tasks
- [ ] `CELERY_RESULT_BACKEND` - For background tasks

### Optional (Nice to Have)
- [ ] `SENTRY_DSN` - Error tracking
- [ ] `LOG_LEVEL=INFO` - Production logging
- [ ] `RAZORPAY_WEBHOOK_SECRET` - For payment webhooks

---

## 🚀 Deployment Steps

### Step 1: Development Environment (Current)
```bash
ENVIRONMENT=development
DEBUG=true
XML_AGENCY_BASE_URL=https://test-api.xml.agency  # Test API
RAZORPAY_KEY_ID=rzp_test_xxxxx  # Test keys
```

### Step 2: Staging Environment
```bash
ENVIRONMENT=staging
DEBUG=false
XML_AGENCY_BASE_URL=https://test-api.xml.agency  # Still test API
RAZORPAY_KEY_ID=rzp_test_xxxxx  # Still test keys
JWT_SECRET_KEY=<strong-random-key>  # Real secret
```

### Step 3: Production Environment
```bash
ENVIRONMENT=production
DEBUG=false
XML_AGENCY_BASE_URL=https://api.xml.agency  # LIVE API
RAZORPAY_KEY_ID=rzp_live_xxxxx  # LIVE keys
JWT_SECRET_KEY=<strong-random-key>  # Real secret
```

---

## 🔐 Security Best Practices

1. **Never commit `.env` to Git**
   - ✅ Already in `.gitignore`
   - Use `.env.example` for documentation

2. **Use different keys per environment**
   - Development: Test keys
   - Staging: Test keys
   - Production: Live keys

3. **Rotate secrets regularly**
   - JWT secret: Every 90 days
   - API keys: When team members leave
   - Database passwords: Quarterly

4. **Use environment-specific configs**
   ```bash
   # Development
   cp .env.example .env.dev
   
   # Production
   cp .env.example .env.prod
   ```

---

## 🧪 Testing Integrations

### Test XML.Agency Connection
```python
# Create: test_xml_agency.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_xml_agency():
    base_url = os.getenv("XML_AGENCY_BASE_URL")
    username = os.getenv("XML_AGENCY_USERNAME")
    password = os.getenv("XML_AGENCY_PASSWORD")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/test",  # Use actual endpoint
            auth=(username, password)
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

# Run: python -m asyncio test_xml_agency.py
```

### Test Razorpay Connection
```python
# Create: test_razorpay.py
import razorpay
import os
from dotenv import load_dotenv

load_dotenv()

def test_razorpay():
    client = razorpay.Client(
        auth=(
            os.getenv("RAZORPAY_KEY_ID"),
            os.getenv("RAZORPAY_KEY_SECRET")
        )
    )
    
    # Test: Fetch payment methods
    try:
        methods = client.payment.methods()
        print("✅ Razorpay connected successfully!")
        print(f"Available methods: {methods}")
    except Exception as e:
        print(f"❌ Razorpay connection failed: {e}")

# Run: python test_razorpay.py
```

---

## 📊 What Happens When You Add These

| Variable | Current Behavior | After Adding |
|----------|------------------|--------------|
| `XML_AGENCY_USERNAME/PASSWORD` | Mock flight data (random) | ✅ Real flights from airlines |
| `RAZORPAY_KEY_ID/SECRET` | 90% random success | ✅ Real payment processing |
| `MAIL_FROM/PASSWORD` | No emails sent | ✅ Actual email notifications |
| `CELERY_BROKER_URL` | Sync operations | ✅ Background task processing |
| Strong `JWT_SECRET_KEY` | Weak security | ✅ Production-grade auth |

---

## 🆘 Need Help?

### XML.Agency Support
- Documentation: Check `XML Agency Flight API.pdf` in repo root
- Support: support@xml.agency
- Website: https://xml.agency/

### Razorpay Support
- Documentation: https://razorpay.com/docs/
- Support: https://razorpay.com/support/
- Dashboard: https://dashboard.razorpay.com/

### Email Issues
- Gmail: https://support.google.com/accounts/answer/185833
- SendGrid: https://sendgrid.com/

---

## ✅ Verification Checklist

Before going to production, verify:

- [ ] Can start the app: `uvicorn app.main:app --reload`
- [ ] Database connects: Check `/health` endpoint
- [ ] Redis connects: Check `/health` endpoint
- [ ] Can register user: `POST /auth/register`
- [ ] Can login: `POST /auth/login`
- [ ] Can generate API key: `POST /api-keys`
- [ ] ⚠️ Flight search returns real data (after XML.Agency setup)
- [ ] ⚠️ Payment processing works (after Razorpay setup)
- [ ] ⚠️ Emails are sent (after email setup)

---

## 🎯 Quick Start for Production

1. **Copy and configure:**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Get API credentials:**
   - Sign up for XML.Agency
   - Sign up for Razorpay
   - Configure email service

3. **Generate secrets:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Test locally:**
   ```bash
   source .env.prod  # Or: set in PowerShell
   uvicorn app.main:app --reload
   ```

5. **Deploy:**
   - Use `.env.prod` on production server
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=false`

---

**Last Updated:** November 9, 2025
**Branch:** prod
**Status:** Ready for credential configuration
