"""
Alembic Environment Configuration

This module configures Alembic for database migrations in the Travel Booking Platform.
It sets up the database connection, imports all models, and configures migration settings.
"""

import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import all model modules to register them with Base.metadata for autogenerate
from app.core.database import Base
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

# Import settings to get database URL
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """
    Get database URL from environment variable or settings.
    
    This function ensures we always use the environment DATABASE_URL in production
    (e.g., Render) and never fall back to localhost. It converts postgresql:// 
    to postgresql+asyncpg:// for asyncpg compatibility and adds SSL for remote databases.
    """
    # Prefer DATABASE_URL or SQLALCHEMY_URL from environment variables (required in production)
    # Prefer a dedicated migration URL (e.g., Supabase transaction pooler or psycopg)
    db_url = os.getenv("DATABASE_MIGRATION_URL") or os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_URL")
    
    # If not in environment, use settings (which reads from .env file)
    if not db_url:
        db_url = settings.database_url
    
    # Convert postgresql:// to postgresql+asyncpg:// for async migrations
    # If user provides a psycopg URL for migrations, keep it as-is
    if db_url.startswith("postgresql://") and not (db_url.startswith("postgresql+asyncpg://") or db_url.startswith("postgresql+psycopg://")):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Add SSL requirements only for remote/production databases (e.g., Render PostgreSQL)
    # Local databases typically don't require SSL
    # Note: asyncpg only supports 'ssl' parameter, not 'sslmode'
    if "postgresql+asyncpg://" in db_url:
        # Map sslmode=require to ssl=require for asyncpg
        if "sslmode=require" in db_url and "ssl=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}ssl=require"
        # Remove sslmode parameter entirely (asyncpg doesn't accept it)
        if "sslmode=" in db_url:
            db_url = db_url.replace("sslmode=require", "")
            db_url = db_url.replace("?&", "?").replace("&&", "&").rstrip("?&")
        
        if "ssl=" not in db_url:
            # Check if this is a remote database that requires SSL
            is_local = "localhost" in db_url or "127.0.0.1" in db_url
            is_production = settings.environment in ["production", "staging"]
            is_remote_host = any(host in db_url for host in ["render.com", ".onrender.com", ".amazonaws.com", "cloud", "managed", ".supabase.co"])
            
            # Only add SSL for remote/production databases, not local development
            if (is_production or is_remote_host) and not is_local:
                separator = "&" if "?" in db_url else "?"
                # For asyncpg, use ssl=require for SSL connections
                db_url = f"{db_url}{separator}ssl=require"
    
    return db_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()
    
    # Choose engine type based on driver: psycopg -> sync, asyncpg -> async
    is_psycopg = url.startswith("postgresql+psycopg://")
    if is_psycopg:
        connectable = engine_from_config(
            {"sqlalchemy.url": url},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    else:
        connectable = AsyncEngine(
            engine_from_config(
                {"sqlalchemy.url": url},
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
                future=True,
            )
        )

    async def do_run_migrations_async(connection: Connection):
        await connection.run_sync(do_run_migrations)

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await do_run_migrations_async(connection)
        await connectable.dispose()

    def run_sync_migrations():
        with connectable.connect() as connection:
            do_run_migrations(connection)
        connectable.dispose()

    if is_psycopg:
        run_sync_migrations()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
