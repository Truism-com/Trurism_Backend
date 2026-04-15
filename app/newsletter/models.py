"""
Newsletter Subscriber Database Model

This module defines the database model for newsletter subscribers:
- Email-based subscription management
- Subscription status tracking
- Audit fields for lifecycle management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


class NewsletterSubscriber(Base):
    """
    Newsletter Subscriber model.
    
    Stores subscriber email addresses along with subscription status
    and timestamps for tracking lifecycle events.
    """
    __tablename__ = "newsletter_subscribers"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Subscription state
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<NewsletterSubscriber(id={self.id}, email={self.email})>"

    @property
    def is_subscribed(self) -> bool:
        """
        Check if subscriber is currently active.
        """
        return self.is_active and self.unsubscribed_at is None

    def unsubscribe(self):
        """
        Mark subscriber as unsubscribed (soft delete).
        """
        self.is_active = False
        self.unsubscribed_at = datetime.utcnow()