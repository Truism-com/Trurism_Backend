import asyncio
from app.services.email import email_service

async def main():
    print("Is configured:", email_service.is_configured)
    
    result = await email_service.send_welcome(
        to_email="kapoorhimanshu124@gmail.com",   # put your own email here
        user_name="Test User"
    )
    print("Welcome email sent:", result)

asyncio.run(main())