# Trurism B2B2C Travel Platform - System Architecture 
## 1. System Architecture

### 1a. High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        B2C["B2C Frontend<br/>Next.js on Vercel"]
        B2B["B2B Portal<br/>Next.js on Vercel"]
        ADMIN["Admin Panel<br/>Next.js on Vercel"]
    end

    subgraph "API Gateway Layer"
        API["FastAPI Backend<br/>Render Free Tier"]
    end

    subgraph "Service Layer"
        AUTH["Auth Module"]
        SEARCH["Search Module"]
        BOOK["Booking Module"]
        PAY["Payments Module"]
        TENANT["Tenant Module"]
        WALLET["Wallet Module"]
        CMS["CMS Module"]
        DASH["Dashboard Module"]
    end

    subgraph "External APIs"
        XML["XML.Agency<br/>Flight SOAP API"]
        RAZORPAY["Razorpay<br/>Payment Gateway"]
        SMTP["SMTP<br/>Email Service"]
    end

    subgraph "Data Layer"
        DB["PostgreSQL<br/>Supabase Free Tier"]
        CACHE["Redis<br/>Upstash Free Tier"]
    end

    subgraph "AI/ML Layer"
        HF["HuggingFace<br/>Inference API"]
    end

    B2C --> API
    B2B --> API
    ADMIN --> API
    API --> AUTH & SEARCH & BOOK & PAY & TENANT & WALLET & CMS & DASH
    SEARCH --> XML
    PAY --> RAZORPAY
    AUTH --> SMTP
    AUTH --> DB
    BOOK --> DB
    SEARCH --> CACHE
    TENANT --> CACHE
    DASH --> HF
```

### 1b. Component Structure (Existing - Preserve)

```
app/
  core/          - Config, DB engine, Redis, Security, Mixins
  auth/          - JWT auth, RBAC, User model, Refresh tokens
  search/        - Flight/Hotel/Bus search, XML.Agency client
  booking/       - Flight/Hotel/Bus booking, Payment processor
  payments/      - Razorpay integration, Webhook handling
  wallet/        - Agent/User wallet, Credits, Transactions
  tenant/        - Multi-tenant middleware, Tenant CRUD
  markup/        - Price markup rules per tenant
  pricing/       - Pricing engine, Discounts, Convenience fees
  admin/         - Admin operations
  superadmin/    - Platform-level operations
  dashboard/     - B2C dashboard, Activity logs
  holidays/      - Holiday packages
  visa/          - Visa services
  activities/    - Tours and activities
  transfers/     - Airport transfers
  cms/           - Content management
  company/       - Company settings, Branding
  settings/      - System settings, Staff management
  files/         - File upload/download
  services/      - Email, PDF, Storage (cross-cutting)
  api_keys/      - API key management
migrations/      - Alembic migration chain (15 files)
scripts/         - seed.py, promote_superadmin.py
```

### 1c. Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant M as Tenant Middleware
    participant A as Auth Guard
    participant S as Search Service
    participant X as XML.Agency
    participant R as Redis
    participant D as Database

    C->>M: Request + X-Tenant-ID
    M->>R: Check tenant cache
    R-->>M: Tenant data (or miss)
    M->>D: Resolve tenant (if miss)
    M->>A: Pass to auth guard
    A->>D: Verify JWT user exists
    A->>S: Forward to search
    S->>R: Check search cache
    alt Cache Hit
        R-->>S: Cached results
    else Cache Miss
        S->>X: SOAP SearchFlights
        X-->>S: XML response
        S->>R: Cache results (TTL 15min)
    end
    S->>S: Apply tenant markup
    S-->>C: Search results
```

### 1d. API Design (Existing - 80+ endpoints)

Already documented in [API_REFERENCE.md](file:///h:/Trurism/docs/API_REFERENCE.md). Key groups:

| Group | Prefix | Auth | Endpoints |
|-------|--------|------|-----------|
| Health | `/`, `/health` | None | 2 |
| Auth | `/auth` | Mixed | 8 |
| Search | `/search` | None | 6 |
| Bookings | `/bookings` | Bearer | 10+ |
| Payments | `/payments` | Bearer/Webhook | 8 |
| Wallet | `/wallet` | Bearer | 10+ |
| Admin | `/admin`, `/superadmin` | Admin/Superadmin | 15+ |
| Tenant | `/tenants` | Superadmin | 5 |
| CMS | `/cms` | Mixed | 10+ |
| Dashboard | `/dashboard` | Bearer | 8 |
| Markup/Pricing | `/markup`, `/pricing` | Admin | 10+ |
| Others | `/holidays`, `/visa`, `/activities`, `/transfers` | Mixed | 20+ |

### 1e. Database Schema

```mermaid
erDiagram
    TENANTS ||--o{ USERS : "has"
    USERS ||--o{ FLIGHT_BOOKINGS : "makes"
    USERS ||--o{ HOTEL_BOOKINGS : "makes"
    USERS ||--o{ BUS_BOOKINGS : "makes"
    USERS ||--o{ REFRESH_TOKENS : "has"
    USERS ||--o{ API_KEYS : "owns"
    USERS ||--|| WALLETS : "has"
    WALLETS ||--o{ WALLET_TRANSACTIONS : "records"
    TENANTS ||--o{ MARKUP_RULES : "has"
    FLIGHT_BOOKINGS ||--o{ PAYMENT_RECORDS : "linked"
    TENANTS ||--o{ SYSTEM_SETTINGS : "configures"
    TENANTS ||--o{ CMS_PAGES : "has"

    USERS {
        int id PK
        string email
        string password_hash
        string name
        enum role "customer/agent/admin/superadmin"
        int tenant_id FK
        bool is_active
        bool is_verified
    }

    TENANTS {
        int id PK
        string code UK
        string name
        string domain
        string subdomain
        bool is_active
    }

    FLIGHT_BOOKINGS {
        int id PK
        string booking_reference UK
        int user_id FK
        int tenant_id FK
        string offer_id
        string pnr
        decimal total_amount
        enum status
        enum payment_status
    }
```

Full schema: 17 Alembic migrations, ~30 tables. `database_setup.sql` is stale (covers only 6 tables, missing tenants/wallet/payments/dashboard/pricing/CMS/holidays/visa/activities/transfers/company/settings/markup).

### 1f. Caching Strategy

| What | Key Pattern | TTL | Store |
|------|-------------|-----|-------|
| Search results | `search:{type}:{sha256}` | 15 min | Redis |
| Tenant resolution | `tenant:{id/code/host}` | 10 min | Redis |
| Token blacklist | `blacklist:{sha256}` | Token TTL | Redis (fallback: DB) |
| Wallet holds | `hold:{id}` | 30 min | Redis |
| OTP codes | `pwd_reset_otp:{email}` | 15 min | Redis |

Redis is optional. App degrades gracefully without it (no caching, DB-based blacklist).

### 1g. Hosting Strategy (Free Tier)

| Component | Service | Tier | Limits |
|-----------|---------|------|--------|
| Backend API | **Render** | Free | Spins down after 15min idle, 750h/month |
| Database | **Supabase** | Free | 500MB, 2 projects |
| Redis/Cache | **Upstash** | Free | 10k commands/day |
| Frontend | **Vercel** | Free | 100GB bandwidth |
| AI/ML | **HuggingFace** | Free inference | Rate limited |
| Email | **Gmail SMTP** | Free | 500/day |
| File Storage | **Supabase Storage** | Free | 1GB |
| CI/CD | **GitHub Actions** | Free | 2000 min/month |
| Monitoring | **UptimeRobot** + Render logs | Free | 50 monitors |

---

## 2. Scaling Analysis

| Users | DB | Cache | Backend | Concerns |
|-------|----|-------|---------|----------|
| 1 | Supabase free | None needed | Render free | Cold start 30s |
| 10 | Supabase free | Upstash free | Render free | Acceptable |
| 100 | Supabase free | Upstash free | Render free (may hit limits) | Search API rate limits |
| 1000 | Supabase Pro ($25/mo) | Upstash Pro ($10/mo) | Render Starter ($7/mo) | Need connection pooling, horizontal scaling |

---

## 3. Tradeoff Decisions

| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| DB hosting | Local Docker Postgres | Supabase cloud | **Supabase** | Persistent, accessible from Render, free |
| Redis | Local Docker Redis | Upstash | **Upstash** (later). None for V0. | App works without Redis. Add when needed. |
| Migration source | `database_setup.sql` | Alembic migrations | **Alembic** | Single source of truth, versioned |
| Frontend deploy | Render static | Vercel | **Vercel** | Better Next.js support, edge CDN |
| AI integration | Self-hosted model | HuggingFace Inference API | **HF API** | Zero infra cost |
| Background jobs | Celery + Redis | In-process async | **In-process async** for now | No money for Redis worker. Celery later. |

---

## 4. Security Considerations

> [!IMPORTANT]
> These are non-negotiable before any public deployment.

- [x] JWT with refresh token rotation (implemented)
- [x] Token blacklisting with Redis + DB fallback (implemented)
- [x] Rate limiting via slowapi (implemented)
- [x] Security headers (CSP, HSTS, X-Frame-Options) (implemented)
- [x] Trusted host middleware (implemented)
- [x] Input validation via Pydantic v2 (implemented)
- [x] CORS restriction in production (implemented)



## 5. Deployment Architecture

```mermaid
graph LR
    subgraph "GitHub"
        REPO["Repository"]
        GA["GitHub Actions"]
    end

    subgraph "Render"
        WEB["Web Service<br/>Dockerfile"]
    end

    subgraph "Supabase"
        PG["PostgreSQL"]
    end

    subgraph "Vercel"
        FE["Next.js Frontend"]
    end

    subgraph "Upstash"
        REDIS["Redis"]
    end

    REPO -->|push to main| GA
    GA -->|deploy| WEB
    GA -->|deploy| FE
    WEB --> PG
    WEB --> REDIS
    FE --> WEB
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# Proposed workflow
on push to main:
  1. Lint (ruff)
  2. Type check (mypy)
  3. Test (pytest --cov)
  4. Build Docker image
  5. Deploy to Render (auto-deploy on push)
  6. Run alembic upgrade head (in start.sh)
  7. Health check verification
```

### Docker Setup (Already exists - `Dockerfile` + `start.sh`)

Existing Dockerfile is functional. `start.sh` runs `alembic upgrade head` then `uvicorn`. Good pattern.

---
