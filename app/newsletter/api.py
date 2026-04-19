from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.newsletter.schemas import (
    SubscribeRequest,
    SubscriberResponse,
    SubscriberListResponse
)
from app.newsletter import services

router = APIRouter()


# 🔓 Public
@router.post("/newsletter/subscribe", response_model=SubscriberResponse)
async def subscribe(
    data: SubscribeRequest,
    db: AsyncSession = Depends(get_db)
):
    subscriber = await services.create_subscriber(db, data.email)

    if not subscriber:
        raise HTTPException(status_code=400, detail="Email already subscribed")

    return subscriber


# 🔐 Admin
@router.get("/admin/newsletter/subscribers", response_model=SubscriberListResponse)
async def list_subscribers(
    page: int = Query(1, ge=1),
    size: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size

    total, data = await services.get_subscribers(db, skip, size)

    return {
        "total": total,
        "page": page,
        "size": size,
        "data": data
    }


@router.delete("/admin/newsletter/subscribers/{id}")
async def delete_subscriber(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    subscriber = await services.delete_subscriber(db, id)

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return {"message": "Deleted successfully"}