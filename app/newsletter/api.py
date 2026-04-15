"""
Newsletter API Endpoints

This module defines FastAPI endpoints for newsletter management:
- Public subscription endpoint
- Admin subscriber management (list, unsubscribe)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_database_session
from app.auth.api import get_current_admin_user
from app.newsletter.schemas import (
    SubscribeRequest,
    SubscriberResponse,
    SubscriberListResponse,
    SubscriberListItem
)
from app.newsletter.services import NewsletterService


# Router for newsletter endpoints
router = APIRouter(tags=["Newsletter"])


# ========================
# PUBLIC ENDPOINT
# ========================
@router.post(
    "/newsletter/subscribe",
    response_model=SubscriberResponse,
    status_code=status.HTTP_201_CREATED
)
async def subscribe_newsletter(
    request: SubscribeRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Subscribe to newsletter.
    
    This endpoint allows users to subscribe to the newsletter
    using their email address.
    
    Args:
        request: Subscription request data
        db: Database session
        
    Returns:
        SubscriberResponse: Created subscriber
        
    Raises:
        HTTPException: If email already exists
    """
    try:
        service = NewsletterService(db)
        subscriber = await service.create_subscriber(request.email)
        
        return SubscriberResponse.model_validate(subscriber)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to subscribe: {str(e)}"
        )


# ========================
# ADMIN ENDPOINTS
# ========================
@router.get(
    "/admin/newsletter/subscribers",
    response_model=SubscriberListResponse
)
async def list_subscribers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    admin=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get paginated list of newsletter subscribers (Admin only).
    
    Args:
        page: Page number
        size: Page size
        admin: Admin user
        db: Database session
        
    Returns:
        SubscriberListResponse: Paginated subscriber list
    """
    try:
        service = NewsletterService(db)
        total, subscribers = await service.get_subscribers(page, size)

        return SubscriberListResponse(
            total=total,
            page=page,
            size=size,
            items=[SubscriberListItem.model_validate(s) for s in subscribers]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscribers: {str(e)}"
        )


@router.delete("/admin/newsletter/subscribers/{subscriber_id}")
async def unsubscribe_user(
    subscriber_id: int,
    admin=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Unsubscribe a user (Admin only).
    
    Args:
        subscriber_id: Subscriber ID
        admin: Admin user
        db: Database session
        
    Returns:
        Dict: Confirmation message
    """
    try:
        service = NewsletterService(db)
        success = await service.unsubscribe(subscriber_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscriber not found"
            )

        return {
            "message": "Subscriber unsubscribed successfully",
            "subscriber_id": subscriber_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe: {str(e)}"
        )