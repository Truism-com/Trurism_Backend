# Database Setup - Local vs Production

## Current Situation

### Your Local Environment
- PostgreSQL running on `localhost:5432`
- Database name: `travel_booking` (or similar)
- Contains your development data
- Accessed directly by your local app

### Render Production (After Deployment)
- PostgreSQL Flexible Server (managed by Render)
- Hosted on Render's infrastructure (cloud)
- Completely separate from your local database
- Will start EMPTY - no data transferred automatically

---

## What Happens During Deployment

```
┌─────────────────────────────────────────────────────────────┐
│  DEPLOYMENT PROCESS                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Render creates NEW PostgreSQL database in cloud         │
│     ↓                                                       │
│  2. Render builds your Docker container                     │
│     ↓                                                       │
│  3. start.sh runs: alembic upgrade head                     │
│     ↓                                                       │
│  4. Alembic creates all tables from your models             │
│     ↓                                                       │
│  5. App starts and connects to cloud database               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tables That Will Be Created

Based on your models, these tables will be created automatically:

### From `app/auth/models.py`:
- ✅ `users` - User accounts, authentication

### From `app/booking/models.py`:
- ✅ `flight_bookings` - Flight reservations
- ✅ `hotel_bookings` - Hotel reservations
- ✅ `bus_bookings` - Bus reservations

### From `app/api_keys/models.py`:
- ✅ `api_keys` - API key management

### From Alembic migrations:
- ✅ `alembic_version` - Migration tracking

**All tables will be EMPTY** - no data from your local DB

---

## Do You Need to Transfer Data?

### ❓ Questions to Ask Yourself:

**1. Is this data just for testing?**
   - ✅ **NO** - Let production start fresh
   - You can create new test data on production if needed

**2. Do you have important user accounts or bookings?**
   - ⚠️ **YES** - Consider exporting/importing
   - Or manually recreate important records

**3. Is this your first deployment?**
   - ✅ **YES** - Start fresh, it's cleaner

### Recommendation: **START FRESH**

For your first production deployment:
- Let Render create empty tables
- Test with new bookings
- Keep local data for development
- They don't need to match

---

## If You MUST Transfer Data

Only do this if you have critical data that can't be recreated:

### Export from Local:
```powershell
# In PowerShell (your local machine)
pg_dump -U postgres -d travel_booking -f backup.sql
```

### Import to Render:
```powershell
# Get DATABASE_URL from Render dashboard
# Then run:
$env:DATABASE_URL = "postgresql://user:pass@host/db"
psql $env:DATABASE_URL -f backup.sql
```

**⚠️ Warning:** This can cause conflicts with migrations!

---

## Recommended Workflow

### Development (Local):
```
Your PC → localhost:5432 → Local PostgreSQL
- Use for development
- Test features
- Run migrations
- Seed test data
```

### Production (Render):
```
Render Cloud → Managed PostgreSQL → Production Database
- Real user data
- Automatic backups by Render
- Separate from development
- Clean, fresh start
```

### Keep Them Separate!
- Local DB = Development & Testing
- Render DB = Production & Real Users

---

## After First Deployment

### To Create Admin User (Production):

You'll need to create users on production. Options:

**Option 1: Use Your API**
```bash
curl -X POST https://your-app.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "secure_password",
    "full_name": "Admin User"
  }'
```

**Option 2: Database Seed Script**

Create `app/seed.py`:
```python
# Run this once to create initial admin user
from app.core.database import AsyncSessionLocal
from app.auth.models import User
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as session:
        admin = User(
            email="admin@yourdomain.com",
            hashed_password=get_password_hash("ChangeMe123!"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        session.add(admin)
        await session.commit()
```

---

## Summary

✅ **What happens automatically:**
- Render creates database
- Migrations create tables
- App connects to cloud DB

❌ **What does NOT happen automatically:**
- Data transfer from local
- User account migration
- Booking history transfer

🎯 **What you should do:**
1. Let deployment create fresh database
2. Test the application
3. Create new admin user via API
4. Start fresh for production

Your local database remains untouched and separate! 🎉
