"""
Quick test script to verify database connection
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_connection():
    """Test PostgreSQL connection"""
    database_url = os.getenv('DATABASE_URL')
    
    print(f"Testing connection with URL: {database_url}")
    
    # Extract connection details from URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    url_parts = database_url.replace('postgresql+asyncpg://', '').replace('postgresql://', '')
    
    try:
        # Try connecting with asyncpg
        conn = await asyncpg.connect(database_url.replace('postgresql+asyncpg://', 'postgresql://'))
        
        # Test query
        result = await conn.fetchval('SELECT current_user')
        print(f"✅ Connection successful! Current user: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check if password in .env matches PostgreSQL")
        print(f"2. Try connecting manually: psql -U trurism_user -d trurism_db")
        print(f"3. Check for special characters that need escaping")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
