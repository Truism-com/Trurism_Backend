# Trurism Backend Architecture

A highly available, modular B2B2C travel booking platform built with FastAPI. This system provides core capabilities for flight, hotel, and bus inventory distribution, utilizing a multi-tenant architecture designed to support direct consumer channels alongside white-label travel agency portfolios.

## System Architecture Overview

The platform utilizes a strictly enforced Domain-Driven Design (DDD) to isolate business contexts.

```text
app/
├── core/                    # Shared utilities, configuration, and security models
├── auth/                    # JWT token lifecycle, role-based access control
├── search/                  # Asynchronous supplier aggregations (XML.Agency)
├── booking/                 # ACID compliance for transactional bookings
├── admin/                   # Privileged administration controllers
├── payments/                # Financial state mutations (Razorpay webhooks)
└── main.py                  # Uvicorn entry point
```

## Technical Foundation

*   **Framework:** FastAPI running asynchronously via Uvicorn.
*   **Database Engine:** PostgreSQL 14+ connected via asyncpg and SQLAlchemy 2.0.
*   **Caching Layer:** Redis for aggressive search payload caching and session invalidation.
*   **Background Processing:** Celery configured for asynchronous tasks.
*   **Security Posture:** Strict JWT refresh cycles with bcrypt hashing and rate limiting via slowapi.

## Infrastructure Prerequisites

Local development requires the following services:
*   Python 3.11+
*   PostgreSQL 14+
*   Redis 6+
*   Git

## Local Environment Setup

### 1. Repository Initialization
Clone the repository and bootstrap the environment.

```bash
git clone https://github.com/Truism-com/Trurism_Backend.git
cd Trurism_Backend
python -m venv venv
```

Activate the virtual environment:
*   Windows: `venv\Scripts\activate`
*   Unix: `source venv/bin/activate`

### 2. Dependency Management
Install frozen requirements to guarantee environmental parity.

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Duplicate the configuration template and populate your local variables.

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/travel_booking
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=cryptographically_secure_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=120

RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

XML_AGENCY_USERNAME=test
XML_AGENCY_PASSWORD=test
```

### 4. Database Seeding
Execute Alembic migrations to apply structural schemas.

```bash
alembic upgrade head
```

### 5. Application Launch
Initialize the Uvicorn ASGI server.

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation is dynamically generated at `http://localhost:8000/docs`.

## Integration Engineering Guidelines

When contributing to this repository, teams must adhere to the following standards:
1. **No Direct Master Commits:** All changes must originate from feature branches.
2. **Mandatory Type Verification:** MyPy structural typing checks must pass.
3. **Automated Testing:** All core supplier logic must be vetted via pytest prior to Pull Request submission. 
4. **Synchronous Safety:** No blocking synchronous external network calls may be placed inside main execution threads.

## Azure App Service Deployment strategy

This application is containerized and optimized for Azure Application Services. 

1. Ensure target variables are securely vaulted within Azure App Configuration.
2. Validate PostgreSQL connection tracking handles expected pooling load.
3. Verify Redis caches are provisioned to offset supplier XML payloads natively.
4. Execute `startup_azure.sh` upon container initialization.

## Roadmap Status

### Phase 1: Authentication and Scaffolding (Complete)
*   JWT RBAC implementation
*   PostgreSQL asynchronous scaling configuration
*   Modular routing definitions

### Phase 2: Core Revenue Operations (Complete)
*   Razorpay API integrations and secure webhook ingestion
*   XML.Agency SOAP 1.2 client construction via Zeep

### Phase 3: Platform Stabilization (In Progress)
*   Unit Test coverage enforcement
*   Automated staging environments via GitHub Actions
*   Database seeding utilities for local development
