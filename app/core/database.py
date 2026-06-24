"""
Database Configuration and Session Management

This module handles:
- Database engine creation and connection pooling
- Session management with dependency injection
- Database health checks
- Connection cleanup and error handling
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import logging
from typing import AsyncGenerator

from app.core.config import settings

# Connection arguments for asyncpg
connect_args = {}

# SSL support for managed databases
if "ssl=require" in settings.database_url:
    connect_args["ssl"] = "require"

# Disable prepared statement caching for pgBouncer (Supabase transaction pooler)
if "pooler.supabase.com" in settings.database_url or "pgbouncer" in settings.database_url.lower():
    connect_args["statement_cache_size"] = 0

# Database engine for async operations
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
    connect_args=connect_args
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Alias for compatibility
async_session_maker = AsyncSessionLocal

# Base class for all database models
class Base(DeclarativeBase):
    """
    Base class for all database models.
    
    This provides the foundation for all ORM models in the application,
    ensuring consistent table naming and metadata handling.
    """
    pass


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.
    
    This function provides an async database session for use in
    FastAPI endpoints. It automatically handles session cleanup.
    
    Yields:
        AsyncSession: Database session for database operations
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logging.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# Alias for common naming pattern
get_db = get_database_session


async def check_database_health() -> bool:
    """
    Check database connectivity and health.
    
    This function verifies that the database is accessible and
    responsive. Used for health checks and startup validation.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    import asyncio
    try:
        # Use a strict 10s timeout for health checks
        async with AsyncSessionLocal() as session:
            result = await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=10.0)
            return result.scalar() == 1
    except asyncio.TimeoutError:
        logging.error("Database health check timed out after 10s")
        return False
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return False


def run_alembic_migrations():
    """
    Run Alembic migrations programmatically.
    
    This connects to the database and runs all migrations up to the head.
    """
    import os
    import sys
    from alembic.config import Config
    from alembic import command
    
    logger = logging.getLogger(__name__)
    logger.info("Running database migrations via Alembic...")
    try:
        # Locate alembic.ini relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ini_path = os.path.join(base_dir, "alembic.ini")
        
        # Ensure project root is in python path so env.py can import app modules
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
            
        alembic_cfg = Config(ini_path)
        
        # Override connection URL with current env config (escape '%' for configparser)
        migration_url = (settings.database_migration_url or settings.database_url).replace("%", "%%")
        alembic_cfg.set_main_option("sqlalchemy.url", migration_url)
        
        # Run upgrade
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        import traceback
        with open("migration_error.log", "w") as f:
            traceback.print_exc(file=f)
        logger.error(f"Failed to run database migrations: {e}")
        raise


async def seed_database():
    """
    Seed the database with default superadmin.
    """
    import os
    from app.auth.models import User, UserRole
    from app.core.security import SecurityManager
    from sqlalchemy import select

    # Import other models so SQLAlchemy relationships resolve correctly
    import app.booking.models  # noqa: F401

    seed_email = os.getenv("SEED_ADMIN_EMAIL", "admin@demo.com")
    seed_password = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.email == seed_email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                logging.info(f"{seed_email} already exists, skipping seeding.")
                return

            user = User(
                email=seed_email,
                password_hash=SecurityManager.hash_password(seed_password),
                name="Admin",
                role=UserRole.SUPERADMIN,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.commit()
            logging.info(f"Seeded {seed_email} (SUPERADMIN)")
        except Exception as e:
            logging.error(f"Failed to seed database: {e}")


async def init_database():
    """
    Initialize database tables via Alembic migrations.
    
    This function runs the migrations and seeds the initial data.
    Should be called during application startup.
    """
    import asyncio
    
    # Run migrations synchronously in a thread pool to avoid blocking the event loop
    await asyncio.to_thread(run_alembic_migrations)
    
    # Seed the database
    await seed_database()
