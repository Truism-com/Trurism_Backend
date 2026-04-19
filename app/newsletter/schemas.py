from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List


class SubscribeRequest(BaseModel):
    email: EmailStr


class SubscriberResponse(BaseModel):
    id: int
    email: EmailStr
    subscribed_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class SubscriberListResponse(BaseModel):
    total: int
    page: int
    size: int
    data: List[SubscriberResponse]