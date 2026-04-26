"""
Setup Verification Script

This script verifies that all dependencies and configurations are correct
for the Travel Booking Platform.

Run: python setup_check.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add project to path
sys.path.insert(0, str(script_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def check_env_variable(name: str, required: bool = True, secret: bool = False) -> tuple:
    """Check if environment variable is set."""
    value = os.getenv(name)
    if value:
        display = "***" if secret else (value[:50] + "..." if len(value) > 50 else value)
        return (True, display)
    return (False, "NOT SET" + (" (REQUIRED)" if required else " (optional)"))


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_check(name: str, passed: bool, value: str = ""):
    """Print check result."""
    status = "✅" if passed else "❌"
    print(f"  {status} {name}: {value}")


async def check_database_connection():
    """Test database connection."""
    try:
        from app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # Check if URL is configured
        if "YOUR_" in settings.database_url:
            return False, "Database URL not configured"
        
        # Create engine without SSL args for testing
        connect_args = {}
        if "ssl=require" in settings.database_url:
            connect_args["ssl"] = "require"
            
        engine = create_async_engine(
            settings.database_url,
            pool_size=2,
            max_overflow=0,
            connect_args=connect_args if connect_args else {}
        )
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        
        await engine.dispose()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)[:80]


def check_package_installed(package_name: str) -> tuple:
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True, "Installed"
    except ImportError:
        return False, "NOT INSTALLED"


def check_module_imports():
    """Check if all app modules can be imported."""
    modules_to_check = [
        ("app.core.config", "Core Config"),
        ("app.core.database", "Core Database"),
        ("app.core.security", "Core Security"),
        ("app.auth.models", "Auth Models"),
        ("app.auth.api", "Auth API"),
        ("app.booking.models", "Booking Models"),
        ("app.booking.api", "Booking API"),
        ("app.search.api", "Search API"),
        ("app.admin.api", "Admin API"),
        ("app.tenant.api", "Tenant API"),
        ("app.markup.api", "Markup API"),
        ("app.payments.api", "Payments API"),
        ("app.api_keys.api", "API Keys API"),
    ]
    
    results = []
    for module, name in modules_to_check:
        try:
            __import__(module)
            results.append((name, True, "OK"))
        except Exception as e:
            results.append((name, False, str(e)[:50]))
    
    return results


async def main():
    print("\n" + "="*60)
    print("  TRAVEL BOOKING PLATFORM - SETUP VERIFICATION")
    print("="*60)
    
    all_passed = True
    
    # ================== PYTHON PACKAGES ==================
    print_section("PYTHON PACKAGES")
    
    packages = [
        "fastapi", "sqlalchemy", "asyncpg", "psycopg", "razorpay",
        "pydantic", "alembic", "redis", "celery", "httpx"
    ]
    
    for pkg in packages:
        passed, msg = check_package_installed(pkg)
        print_check(pkg, passed, msg)
        if not passed and pkg in ["fastapi", "sqlalchemy", "asyncpg", "razorpay"]:
            all_passed = False
    
    # ================== ENVIRONMENT VARIABLES ==================
    print_section("ENVIRONMENT VARIABLES")
    
    env_vars = [
        ("APP_NAME", False, False),
        ("ENVIRONMENT", True, False),
        ("DATABASE_URL", True, True),
        ("DATABASE_MIGRATION_URL", True, True),
        ("JWT_SECRET_KEY", True, True),
        ("RAZORPAY_KEY_ID", True, True),
        ("RAZORPAY_KEY_SECRET", True, True),
        ("RAZORPAY_WEBHOOK_SECRET", False, True),
        ("REDIS_URL", False, False),
        ("MAIL_SERVER", False, False),
        ("MAIL_FROM", False, False),
        ("XML_AGENCY_USERNAME", False, True),
    ]
    
    for name, required, secret in env_vars:
        passed, msg = check_env_variable(name, required, secret)
        print_check(name, passed, msg)
        if not passed and required:
            all_passed = False
    
    # ================== DATABASE CONNECTION ==================
    print_section("DATABASE CONNECTION")
    
    passed, msg = await check_database_connection()
    print_check("PostgreSQL Connection", passed, msg)
    if not passed:
        all_passed = False
    
    # ================== MODULE IMPORTS ==================
    print_section("MODULE IMPORTS")
    
    module_results = check_module_imports()
    for name, passed, msg in module_results:
        print_check(name, passed, msg)
        if not passed:
            all_passed = False
    
    # ================== FILES CHECK ==================
    print_section("REQUIRED FILES")
    
    required_files = [
        ".env",
        "requirements.txt",
        "alembic.ini",
        "app/main.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/payments/api.py",
        "migrations/versions/002_add_payment_system.py",
    ]
    
    for file in required_files:
        exists = Path(file).exists()
        print_check(file, exists, "Found" if exists else "MISSING")
        if not exists:
            all_passed = False
    
    # ================== SUMMARY ==================
    print_section("SUMMARY")
    
    if all_passed:
        print("\n  ✅ ALL CHECKS PASSED!")
        print("\n  You can now run:")
        print("    1. alembic upgrade head   # Run migrations")
        print("    2. uvicorn app.main:app --reload   # Start server")
    else:
        print("\n  ❌ SOME CHECKS FAILED")
        print("\n  Please fix the issues above before proceeding.")
        print("\n  Common fixes:")
        print("    - Database: Update .env with valid Supabase credentials")
        print("    - Packages: pip install -r requirements.txt")
        print("    - Razorpay: Get keys from dashboard.razorpay.com")
    
    print("\n")
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
