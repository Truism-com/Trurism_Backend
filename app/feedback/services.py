"""
Feedback Services

This module contains business logic for feedback management:
- Public feedback submission
- Admin feedback retrieval
- Pagination support
- Feedback deletion
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from fastapi import HTTPException, status

from app.feedback.models import Feedback
from app.feedback.schemas import FeedbackCreate, FeedbackUpdate


class FeedbackService:
    """
    Feedback service for managing customer feedback.
    
    Handles feedback creation, retrieval, and admin operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ✅ Create Feedback (Public / Auth)
    async def create_feedback(
        self,
        data: FeedbackCreate,
        user_id: Optional[int] = None
    ) -> Feedback:
        """
        Create new feedback entry.
        """
        feedback = Feedback(
            user_id=user_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            subject=data.subject,
            message=data.message,
            rating=data.rating
        )

        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)

        return feedback

    # ✅ Get Paginated Feedback (Admin)
    async def get_feedback_list(
        self,
        page: int = 1,
        size: int = 10
    ) -> Tuple[int, List[Feedback]]:
        """
        Get paginated feedback list.
        """
        # Total count
        total_result = await self.db.execute(
            select(func.count()).select_from(Feedback)
        )
        total = total_result.scalar_one()

        # Fetch items
        result = await self.db.execute(
            select(Feedback)
            .order_by(Feedback.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = result.scalars().all()

        return total, items

    # ✅ Get Feedback by ID
    async def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """
        Retrieve feedback by ID.
        """
        result = await self.db.execute(
            select(Feedback).where(Feedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    # ✅ Delete Feedback (Admin)
    async def delete_feedback(self, feedback_id: int) -> bool:
        """
        Delete feedback entry.
        """
        feedback = await self.get_feedback_by_id(feedback_id)

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )

        await self.db.delete(feedback)
        await self.db.commit()

        return True

    # ✅ Update Feedback (Optional Admin Feature)
    async def update_feedback(
        self,
        feedback_id: int,
        update_data: FeedbackUpdate
    ) -> Optional[Feedback]:
        """
        Update feedback fields.
        """
        feedback = await self.get_feedback_by_id(feedback_id)

        if not feedback:
            return None

        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(feedback, field, value)

        await self.db.commit()
        await self.db.refresh(feedback)

        return feedback