"""
Feedback Database Model

This module defines the database model for customer feedback:
- Public and authenticated submissions
- Rating and message storage
- Audit timestamp for tracking submissions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


class Feedback(Base):
    """
    Feedback model.

    Stores customer feedback including optional user reference,
    contact details, message, and rating.
    """
    __tablename__ = "feedback"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)

    # Optional user reference
    user_id = Column(Integer, nullable=True)

    # Contact details
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)

    # Feedback content
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Feedback(id={self.id}, email={self.email}, rating={self.rating})>"

    @property
    def is_positive(self) -> bool:
        """
        Check if feedback is positive (rating >= 4).
        """
        return self.rating >= 4

    def update_rating(self, new_rating: int):
        """
        Update feedback rating with validation.
        """
        if not (1 <= new_rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        self.rating = new_rating