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

# Connection arguments for asyncpg SSL support
# SSL is typically required for managed databases like Render PostgreSQL
# The URL already includes ssl=require if needed, but we also set it in connect_args
# for explicit SSL configuration with asyncpg
connect_args = {}
if "ssl=require" in settings.database_url:
    # For asyncpg, use ssl='require' for SSL connections
    # asyncpg accepts ssl as a string ('require', 'allow', 'prefer', etc.) or boolean
    connect_args["ssl"] = "require"

# Database engine for async operations
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
    connect_args=connect_args if connect_args else {}
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

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


async def check_database_health() -> bool:
    """
    Check database connectivity and health.
    
    This function verifies that the database is accessible and
    responsive. Used for health checks and startup validation.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
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
        # Import all models to ensure they are registered
        from app.auth.models import User
        from app.booking.models import FlightBooking, HotelBooking, BusBooking
        from app.api_keys.models import APIKey
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Database tables created successfully")
