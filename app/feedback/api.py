"""
Feedback API Endpoints

This module defines FastAPI endpoints for feedback management:
- Public feedback submission
- Admin feedback management (list, view, delete)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User

from app.feedback.schemas import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackListResponse
)
from app.feedback.services import FeedbackService


# Routers
router = APIRouter(prefix="/feedback", tags=["Feedback"])
admin_router = APIRouter(prefix="/admin/feedback", tags=["Admin Feedback"])


# ✅ Public / Auth Feedback Submission
@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Submit feedback (public or authenticated).

    Allows both anonymous and logged-in users to submit feedback.
    """
    try:
        service = FeedbackService(db)

        user_id = current_user.id if current_user else None

        feedback = await service.create_feedback(
            data=feedback_data,
            user_id=user_id
        )

        return FeedbackResponse.model_validate(feedback)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# ✅ Admin: List Feedback (Paginated)
@admin_router.get("/", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get paginated list of feedback (admin only).
    """
    try:
        service = FeedbackService(db)

        total, items = await service.get_feedback_list(page, size)

        return FeedbackListResponse(
            total=total,
            page=page,
            size=size,
            items=[FeedbackResponse.model_validate(item) for item in items]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )


# ✅ Admin: Get Feedback by ID
@admin_router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get feedback details by ID (admin only).
    """
    try:
        service = FeedbackService(db)

        feedback = await service.get_feedback_by_id(feedback_id)

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )

        return FeedbackResponse.model_validate(feedback)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )


# ✅ Admin: Delete Feedback
@admin_router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete feedback (admin only).
    """
    try:
        service = FeedbackService(db)

        success = await service.delete_feedback(feedback_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )

        return {
            "message": "Feedback deleted successfully",
            "feedback_id": feedback_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feedback: {str(e)}"
        )