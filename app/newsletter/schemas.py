"""
Newsletter Subscriber Schemas

This module defines request/response schemas for newsletter subscription:
- Subscribe requests
- Subscriber response data
- Paginated subscriber listing
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class SubscribeRequest(BaseModel):
    """
    Schema for subscribing to the newsletter.
    
    Validates email input for new subscribers.
    """
    email: EmailStr = Field(..., description="Subscriber email address")


class SubscriberResponse(BaseModel):
    """
    Schema for newsletter subscriber response.
    
    Returns subscriber details after creation or retrieval.
    """
    id: int = Field(..., description="Subscriber ID")
    email: EmailStr = Field(..., description="Subscriber email")
    subscribed_at: datetime = Field(..., description="Subscription timestamp")
    is_active: bool = Field(..., description="Subscription status")
    unsubscribed_at: Optional[datetime] = Field(None, description="Unsubscribe timestamp")

    model_config = ConfigDict(from_attributes=True)


class SubscriberListItem(BaseModel):
    """
    Schema for a single subscriber in list view.
    
    Used in paginated responses (no extra sensitive data).
    """
    id: int
    email: EmailStr
    is_active: bool
    subscribed_at: datetime
    unsubscribed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SubscriberListResponse(BaseModel):
    """
    Schema for paginated subscriber list.
    
    Returns pagination metadata along with subscriber list.
    """
    total: int = Field(..., description="Total number of subscribers")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    items: List[SubscriberListItem] = Field(..., description="List of subscribers")