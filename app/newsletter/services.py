"""
Newsletter Services

This module contains business logic for newsletter management:
- Subscriber creation
- Duplicate email validation
- Pagination support
- Unsubscribe (soft delete)
"""

from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.newsletter.models import NewsletterSubscriber


class NewsletterService:
    """
    Newsletter service for managing subscribers.
    
    Handles subscription, listing, and unsubscribe operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscriber(self, email: str) -> NewsletterSubscriber:
        """
        Create a new subscriber.
        
        Args:
            email: Subscriber email
            
        Returns:
            NewsletterSubscriber
            
        Raises:
            HTTPException: If email already exists
        """
        # Check duplicate
        result = await self.db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.email == email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already subscribed"
            )

        subscriber = NewsletterSubscriber(email=email)

        self.db.add(subscriber)
        await self.db.commit()
        await self.db.refresh(subscriber)

        return subscriber

    async def get_subscribers(
        self,
        page: int = 1,
        size: int = 10
    ) -> Tuple[int, List[NewsletterSubscriber]]:
        """
        Get paginated list of subscribers.
        
        Args:
            page: Page number
            size: Page size
            
        Returns:
            tuple: (total_count, subscribers_list)
        """
        # Total count
        total_result = await self.db.execute(
            select(func.count()).select_from(NewsletterSubscriber)
        )
        total = total_result.scalar()

        # Fetch paginated data
        result = await self.db.execute(
            select(NewsletterSubscriber)
            .order_by(NewsletterSubscriber.subscribed_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        subscribers = result.scalars().all()

        return total, subscribers

    async def unsubscribe(self, subscriber_id: int) -> bool:
        """
        Unsubscribe a user (soft delete).
        
        Args:
            subscriber_id: Subscriber ID
            
        Returns:
            bool: True if successful, False if not found
        """
        result = await self.db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.id == subscriber_id)
        )
        subscriber = result.scalar_one_or_none()

        if not subscriber:
            return False

        subscriber.is_active = False
        subscriber.unsubscribed_at = datetime.utcnow()

        await self.db.commit()

        return True

    async def get_by_email(self, email: str) -> Optional[NewsletterSubscriber]:
        """
        Get subscriber by email.
        
        Args:
            email: Subscriber email
            
        Returns:
            NewsletterSubscriber or None
        """
        result = await self.db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.email == email)
        )
        return result.scalar_one_or_none()