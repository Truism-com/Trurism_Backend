"""
Activity Pydantic Schemas

Request/Response schemas for activity operations.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime, date, time

from app.activities.models import ActivityStatus, BookingStatus


# =============================================================================
# Category Schemas
# =============================================================================

class CategoryBase(BaseModel):
    """Base schema for activity category."""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Response schema for category."""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Location Schemas
# =============================================================================

class LocationBase(BaseModel):
    """Base schema for activity location."""
    name: str
    slug: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_popular: bool = False
    display_order: int = 0


class LocationCreate(LocationBase):
    """Schema for creating a location."""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    name: Optional[str] = None
    slug: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class LocationResponse(LocationBase):
    """Response schema for location."""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Activity Slot Schemas
# =============================================================================

class SlotBase(BaseModel):
    """Base schema for activity slot."""
    start_time: time
    end_time: Optional[time] = None
    max_capacity: int = 50
    is_recurring: bool = False
    days_of_week: Optional[str] = None
    price_override: Optional[float] = None


class SlotCreate(SlotBase):
    """Schema for creating a slot."""
    slot_date: Optional[date] = None


class SlotUpdate(BaseModel):
    """Schema for updating a slot."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_capacity: Optional[int] = None
    available_spots: Optional[int] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    block_reason: Optional[str] = None
    price_override: Optional[float] = None


class SlotResponse(SlotBase):
    """Response schema for slot."""
    id: int
    activity_id: int
    slot_date: Optional[date] = None
    available_spots: int
    is_active: bool
    is_blocked: bool
    
    class Config:
        from_attributes = True


# =============================================================================
# Activity Schemas
# =============================================================================

class ActivityBase(BaseModel):
    """Base schema for activity."""
    name: str
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[str] = None
    inclusions: Optional[str] = None
    exclusions: Optional[str] = None
    important_info: Optional[str] = None
    duration_hours: Optional[float] = None
    duration_text: Optional[str] = None
    min_participants: int = 1
    max_participants: int = 50
    advance_booking_days: int = 1
    is_instant_confirmation: bool = True


class ActivityCreate(ActivityBase):
    """Schema for creating an activity."""
    category_id: Optional[int] = None
    location_id: int
    adult_price: float = 0
    child_price: float = 0
    infant_price: float = 0
    discounted_adult_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    video_url: Optional[str] = None
    cancellation_policy: Optional[str] = None
    refund_policy: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_featured: bool = False
    display_order: int = 0
    # Include slots when creating
    slots: Optional[List[SlotCreate]] = None


class ActivityUpdate(BaseModel):
    """Schema for updating an activity."""
    name: Optional[str] = None
    slug: Optional[str] = None
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[str] = None
    inclusions: Optional[str] = None
    exclusions: Optional[str] = None
    important_info: Optional[str] = None
    duration_hours: Optional[float] = None
    duration_text: Optional[str] = None
    adult_price: Optional[float] = None
    child_price: Optional[float] = None
    infant_price: Optional[float] = None
    discounted_adult_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    min_participants: Optional[int] = None
    max_participants: Optional[int] = None
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    video_url: Optional[str] = None
    status: Optional[ActivityStatus] = None
    is_featured: Optional[bool] = None
    is_instant_confirmation: Optional[bool] = None
    advance_booking_days: Optional[int] = None
    cancellation_policy: Optional[str] = None
    refund_policy: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    display_order: Optional[int] = None


class ActivityListItem(BaseModel):
    """Schema for activity in list view."""
    id: int
    name: str
    slug: str
    code: str
    short_description: Optional[str] = None
    duration_text: Optional[str] = None
    adult_price: float
    discounted_adult_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    thumbnail_url: Optional[str] = None
    avg_rating: float
    review_count: int
    status: ActivityStatus
    is_featured: bool
    is_instant_confirmation: bool
    category: Optional[CategoryResponse] = None
    location: Optional[LocationResponse] = None
    
    class Config:
        from_attributes = True


class ActivityDetail(ActivityListItem):
    """Detailed activity schema."""
    description: Optional[str] = None
    highlights: Optional[str] = None
    inclusions: Optional[str] = None
    exclusions: Optional[str] = None
    important_info: Optional[str] = None
    duration_hours: Optional[float] = None
    child_price: float
    infant_price: float
    min_participants: int
    max_participants: int
    advance_booking_days: int
    gallery: Optional[List[str]] = None
    video_url: Optional[str] = None
    cancellation_policy: Optional[str] = None
    refund_policy: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slots: List[SlotResponse] = []
    created_at: datetime


# =============================================================================
# Booking Schemas
# =============================================================================

class ParticipantInfo(BaseModel):
    """Info for a single participant."""
    name: str
    age: Optional[int] = None
    type: str = "adult"  # adult, child, infant


class BookingCreate(BaseModel):
    """Schema for creating a booking."""
    activity_id: int
    slot_id: Optional[int] = None
    booking_date: date
    booking_time: Optional[time] = None
    contact_name: str
    contact_email: EmailStr
    contact_phone: str
    adults: int = 1
    children: int = 0
    infants: int = 0
    participants: Optional[List[ParticipantInfo]] = None
    special_requests: Optional[str] = None


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    status: Optional[BookingStatus] = None
    is_confirmed: Optional[bool] = None
    confirmation_code: Optional[str] = None
    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None
    amount_paid: Optional[float] = None
    admin_notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Response schema for booking."""
    id: int
    booking_ref: str
    activity_id: int
    slot_id: Optional[int] = None
    user_id: Optional[int] = None
    
    contact_name: str
    contact_email: str
    contact_phone: str
    
    booking_date: date
    booking_time: Optional[time] = None
    
    adults: int
    children: int
    infants: int
    
    adult_rate: float
    child_rate: float
    infant_rate: float
    subtotal: float
    taxes: float
    convenience_fee: float
    discount: float
    total_amount: float
    amount_paid: float
    
    status: BookingStatus
    payment_status: Optional[str] = None
    is_confirmed: bool
    confirmation_code: Optional[str] = None
    
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookingDetail(BookingResponse):
    """Detailed booking with activity info."""
    activity: Optional[ActivityListItem] = None
    participants_data: Optional[List[dict]] = None
    special_requests: Optional[str] = None
    admin_notes: Optional[str] = None


class BookingListResponse(BaseModel):
    """Paginated list of bookings."""
    bookings: List[BookingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Search Schemas
# =============================================================================

class ActivitySearchParams(BaseModel):
    """Parameters for activity search."""
    query: Optional[str] = None
    category_id: Optional[int] = None
    location_id: Optional[int] = None
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    date: Optional[date] = None  # Filter activities with available slots
    is_featured: Optional[bool] = None
    sort_by: str = "display_order"  # price_asc, price_desc, rating, newest
    page: int = 1
    page_size: int = 20


class ActivitySearchResponse(BaseModel):
    """Paginated search results."""
    activities: List[ActivityListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
