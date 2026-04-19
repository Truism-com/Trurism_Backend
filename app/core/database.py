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


async def init_database():
    """
    Initialize database tables.
    
    This function creates all database tables based on the
    defined models. Should be called during application startup.
    """
    async with engine.begin() as conn:
        # Import all model modules to register them with Base.metadata.
        # Module-level import is sufficient; all classes inheriting from Base
        # get registered when the module is executed.
        import app.auth.models  # noqa: F401
        import app.booking.models  # noqa: F401
        import app.api_keys.models  # noqa: F401
        import app.tenant.models  # noqa: F401
        import app.markup.models  # noqa: F401
        import app.wallet.models  # noqa: F401
        import app.payments.models  # noqa: F401
        import app.pricing.models  # noqa: F401
        import app.settings.models  # noqa: F401
        import app.dashboard.models  # noqa: F401
        import app.holidays.models  # noqa: F401
        import app.visa.models  # noqa: F401
        import app.activities.models  # noqa: F401
        import app.transfers.models  # noqa: F401
        import app.cms.models  # noqa: F401
        import app.hotels.models  # noqa: F401
        import app.company.models  # noqa: F401
        import app.newsletter.models
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created successfully")
