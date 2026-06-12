"""
Seed script - creates initial superadmin user for testing.

Usage:
    python scripts/seed.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.auth.models import User, UserRole
from app.core.security import SecurityManager
# Import booking models so SQLAlchemy can resolve User.flight_bookings etc.
import app.booking.models  # noqa: F401


async def seed():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # Check if admin already exists
        result = await db.execute(
            select(User).where(User.email == "admin@demo.com")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print("admin@demo.com already exists, skipping.")
            return

        user = User(
            email="admin@demo.com",
            password_hash=SecurityManager.hash_password("admin123"),
            name="Demo Admin",
            role=UserRole.SUPERADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        print("Seeded admin@demo.com / admin123 (SUPERADMIN)")


if __name__ == "__main__":
    asyncio.run(seed())
