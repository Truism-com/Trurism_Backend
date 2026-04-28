import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

async def promote_user(email: str):
    print(f"Connecting to database to promote {email}...")
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Check if user exists
            result = await session.execute(
                text("SELECT id, role FROM users WHERE email = :email"), 
                {"email": email}
            )
            user = result.fetchone()
            
            if not user:
                print(f"Error: No user found with email '{email}'")
                return
                
            if user[1] == 'superadmin':
                print(f"User {email} is already a superadmin.")
                return

            # Update role
            await session.execute(
                text("UPDATE users SET role = 'superadmin' WHERE email = :email"),
                {"email": email}
            )
            await session.commit()
            print(f"Success! '{email}' has been promoted to superadmin.")
            
        except Exception as e:
            await session.rollback()
            print(f"Database error occurred: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_superadmin.py <user_email>")
        sys.exit(1)
        
    target_email = sys.argv[1]
    asyncio.run(promote_user(target_email))
