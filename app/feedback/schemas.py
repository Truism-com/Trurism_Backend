from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class FeedbackCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    rating: int = Field(..., ge=1, le=5)


class FeedbackResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    subject: Optional[str]
    message: str
    rating: int
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    total: int
    page: int
    size: int
    data: List[FeedbackResponse]