"""
Feedback Pydantic Schemas

This module defines request/response schemas for feedback management:
- Public feedback submission
- Admin feedback retrieval
- Pagination support
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


class FeedbackCreate(BaseModel):
    """
    Schema for creating feedback.
    
    Validates user-submitted feedback including contact details,
    message content, and rating constraints.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")

    subject: Optional[str] = Field(None, max_length=255, description="Feedback subject")
    message: str = Field(..., min_length=5, description="Feedback message")

    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Basic phone validation."""
        if v and not v.replace("+", "").replace("-", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v


class FeedbackResponse(BaseModel):
    """
    Schema for feedback response.
    
    Returns full feedback details including optional user reference.
    """
    id: int = Field(..., description="Feedback ID")
    user_id: Optional[int] = Field(None, description="User ID (if authenticated)")

    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")

    subject: Optional[str] = Field(None, description="Feedback subject")
    message: str = Field(..., description="Feedback message")
    rating: int = Field(..., description="Rating (1-5)")

    created_at: datetime = Field(..., description="Submission timestamp")

    model_config = ConfigDict(from_attributes=True)


class FeedbackListItem(BaseModel):
    """
    Schema for listing feedback (admin view).
    
    Optimized version without heavy fields if needed.
    """
    id: int
    name: str
    email: str
    rating: int
    subject: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    """
    Schema for paginated feedback list.
    
    Includes metadata for pagination.
    """
    total: int = Field(..., description="Total feedback count")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    items: List[FeedbackListItem] = Field(..., description="List of feedback items")


class FeedbackUpdate(BaseModel):
    """
    Schema for updating feedback (admin use).
    
    Allows partial updates if required.
    """
    subject: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = Field(None, min_length=5)
    rating: Optional[int] = Field(None, ge=1, le=5)


class FeedbackStats(BaseModel):
    """
    Schema for feedback statistics.
    
    Provides analytics similar to API key usage stats.
    """
    total_feedbacks: int
    average_rating: float
    positive_feedbacks: int
    negative_feedbacks: int
    latest_feedback_at: Optional[datetime]