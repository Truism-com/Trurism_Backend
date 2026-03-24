import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.database import init_database, engine
from app.core.config import settings

async def main():
    print(f"Connecting to: {settings.database_url}")
    try:
        await init_database()
        print("Database initialization successful!")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
