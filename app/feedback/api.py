from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.feedback.schemas import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackListResponse
)
from app.feedback import services

router = APIRouter()


# 🔓 Public
@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    return await services.create_feedback(db, data)


# 🔐 Admin
@router.get("/admin/feedback", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1),
    size: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    total, data = await services.get_feedback_list(db, skip, size)

    return {
        "total": total,
        "page": page,
        "size": size,
        "data": data
    }


@router.get("/admin/feedback/{id}", response_model=FeedbackResponse)
async def get_feedback(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    feedback = await services.get_feedback_by_id(db, id)

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return feedback


@router.delete("/admin/feedback/{id}")
async def delete_feedback(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    feedback = await services.delete_feedback(db, id)

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {"message": "Deleted successfully"}