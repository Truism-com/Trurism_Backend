# 🚀 Quick Environment Setup Guide

## What You Need to Add to `.env` for Production

### ❌ Currently Using Mock Data (Not Production Ready)

Your app works, but uses **fake/mock data** for:
1. **Flight Search** - Generates random flights
2. **Payments** - 90% random success rate
3. **Booking Confirmations** - No real tickets

---

## 🔑 Required Credentials

### 1. **XML.AGENCY Flight API** ⚠️ CRITICAL

**Get it from:** https://xml.agency/

Add to `.env`:
```bash
XML_AGENCY_USERNAME=your_username_here
XML_AGENCY_PASSWORD=your_password_here
```

**What it does:**
- Replaces mock flight data with REAL flights
- Connects to actual airlines
- Provides real-time pricing and availability

**Documentation:** See `XML Agency Flight API.pdf` in your repo root

---

### 2. **Razorpay Payment Gateway** ⚠️ CRITICAL

**Get it from:** https://razorpay.com/

Add to `.env`:
```bash
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxx
```

**Steps:**
1. Sign up at https://razorpay.com/
2. Go to Dashboard → Settings → API Keys
3. Generate Test Keys (for development)
4. Generate Live Keys (for production, requires KYC)

**What it does:**
- Replaces mock payment with REAL payment processing
- Supports UPI, Cards, Net Banking, Wallets
- Handles refunds automatically

---

### 3. **Email Configuration** ⚠️ IMPORTANT

**Using Gmail:**

Add to `.env`:
```bash
MAIL_FROM=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
```

**How to get Gmail App Password:**
1. Enable 2FA: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" → Generate
4. Copy the 16-character password

**What it does:**
- Sends booking confirmations
- Password reset emails
- Agent approval notifications

---

### 4. **JWT Secret (Security)** 🔐 CRITICAL

**Generate a strong key:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy output and add to `.env`:
```bash
JWT_SECRET_KEY=xK8vN2mP9qR4sT6uW7yZ1aB3cD5eF7gH9iJ0kL2mN4oP6qR8sT0uV2wX4yZ6
```

**⚠️ NEVER use the default key in production!**

---

## ✅ Already Working (No Action Needed)

These are already configured and working:
- ✅ Database (PostgreSQL)
- ✅ Redis Cache
- ✅ User Authentication
- ✅ API Key Management
- ✅ Admin Panel

---

## 📝 Updated `.env` File

Your `.env` should look like this:

```bash
# Application
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://trurism_user:tru_user2025@localhost:5432/trurism_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT - CHANGE THIS!
JWT_SECRET_KEY=<paste-generated-key-here>

# ⚠️ ADD THESE FOR PRODUCTION:
XML_AGENCY_USERNAME=<get-from-xml.agency>
XML_AGENCY_PASSWORD=<get-from-xml.agency>

RAZORPAY_KEY_ID=<get-from-razorpay.com>
RAZORPAY_KEY_SECRET=<get-from-razorpay.com>

MAIL_FROM=<your-email>
MAIL_PASSWORD=<gmail-app-password>

# Celery (already added)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 🧪 How to Test

### 1. Start your app:
```bash
uvicorn app.main:app --reload
```

### 2. Test what's working:
- ✅ Register user: http://localhost:8000/docs → POST /auth/register
- ✅ Login: POST /auth/login
- ✅ Search flights: POST /search/flights (returns mock data for now)

### 3. After adding credentials:
- ✅ Flight search returns REAL flights from XML.Agency
- ✅ Booking payment goes through REAL Razorpay
- ✅ Confirmation emails are sent

---

## 🎯 Priority Order

1. **First:** Get XML.Agency credentials (for flight search)
2. **Second:** Get Razorpay credentials (for payments)
3. **Third:** Configure email (for notifications)
4. **Fourth:** Generate strong JWT secret (for security)

---

## 📚 Full Documentation

See `docs/PRODUCTION_SETUP.md` for complete details.

---

## ⚡ TL;DR

**What you need RIGHT NOW:**

1. Sign up → https://xml.agency/ → Get username/password
2. Sign up → https://razorpay.com/ → Get API keys
3. Generate JWT secret → Run command above
4. Add all to `.env`
5. Restart your app

**That's it!** Your app will then use real data instead of mocks.

---

**Questions?** Check `docs/PRODUCTION_SETUP.md` or your existing documentation.
