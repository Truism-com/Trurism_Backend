"""
Holiday Package Pydantic Schemas

Request and response schemas for holiday package operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# Re-export enums for API use
class PackageType(str, Enum):
    FIXED_DEPARTURE = "fixed_departure"
    CUSTOMIZABLE = "customizable"
    GROUP_TOUR = "group_tour"


class EnquiryStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUOTE_SENT = "quote_sent"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    CLOSED = "closed"


class PackageBookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIALLY_PAID = "partially_paid"
    FULLY_PAID = "fully_paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# =============================================================================
# Theme Schemas
# =============================================================================

class ThemeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class ThemeCreate(ThemeBase):
    slug: Optional[str] = None  # Auto-generated if not provided


class ThemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class ThemeResponse(ThemeBase):
    id: int
    slug: str
    created_at: datetime
    package_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# Destination Schemas
# =============================================================================

class DestinationBase(BaseModel):
    name: str = Field(..., max_length=200)
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_international: bool = False
    is_active: bool = True


class DestinationCreate(DestinationBase):
    slug: Optional[str] = None


class DestinationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_international: Optional[bool] = None
    is_active: Optional[bool] = None


class DestinationResponse(DestinationBase):
    id: int
    slug: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Itinerary Schemas
# =============================================================================

class ItineraryBase(BaseModel):
    day_number: int = Field(..., ge=1)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    meals_included: Optional[str] = None
    accommodation: Optional[str] = None
    activities: Optional[str] = None
    image_url: Optional[str] = None


class ItineraryCreate(ItineraryBase):
    pass


class ItineraryUpdate(BaseModel):
    day_number: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    meals_included: Optional[str] = None
    accommodation: Optional[str] = None
    activities: Optional[str] = None
    image_url: Optional[str] = None


class ItineraryResponse(ItineraryBase):
    id: int
    package_id: int
    
    class Config:
        from_attributes = True


# =============================================================================
# Inclusion Schemas
# =============================================================================

class InclusionBase(BaseModel):
    item: str = Field(..., max_length=300)
    is_included: bool = True
    category: Optional[str] = None
    display_order: int = 0


class InclusionCreate(InclusionBase):
    pass


class InclusionResponse(InclusionBase):
    id: int
    package_id: int
    
    class Config:
        from_attributes = True


# =============================================================================
# Image Schemas
# =============================================================================

class ImageBase(BaseModel):
    image_url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class ImageCreate(ImageBase):
    pass


class ImageResponse(ImageBase):
    id: int
    package_id: int
    
    class Config:
        from_attributes = True


# =============================================================================
# Package Schemas
# =============================================================================

class PackageBase(BaseModel):
    name: str = Field(..., max_length=300)
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    
    theme_id: Optional[int] = None
    destination_id: int
    origin_id: Optional[int] = None
    
    nights: int = Field(1, ge=1)
    days: int = Field(2, ge=1)
    
    base_price: float = Field(0.0, ge=0)
    discounted_price: Optional[float] = None
    child_price: Optional[float] = None
    infant_price: Optional[float] = None
    single_supplement: Optional[float] = None
    currency: str = "INR"
    
    package_type: PackageType = PackageType.CUSTOMIZABLE
    departure_dates: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    min_pax: int = 1
    max_pax: Optional[int] = None
    
    is_featured: bool = False
    is_bestseller: bool = False
    is_active: bool = True
    
    cover_image_url: Optional[str] = None
    
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    
    cancellation_policy: Optional[str] = None
    terms_conditions: Optional[str] = None


class PackageCreate(PackageBase):
    slug: Optional[str] = None
    code: Optional[str] = None
    itinerary: Optional[List[ItineraryCreate]] = None
    inclusions: Optional[List[InclusionCreate]] = None
    images: Optional[List[ImageCreate]] = None


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    theme_id: Optional[int] = None
    destination_id: Optional[int] = None
    origin_id: Optional[int] = None
    nights: Optional[int] = None
    days: Optional[int] = None
    base_price: Optional[float] = None
    discounted_price: Optional[float] = None
    child_price: Optional[float] = None
    infant_price: Optional[float] = None
    single_supplement: Optional[float] = None
    package_type: Optional[PackageType] = None
    departure_dates: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    min_pax: Optional[int] = None
    max_pax: Optional[int] = None
    is_featured: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    is_active: Optional[bool] = None
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    cancellation_policy: Optional[str] = None
    terms_conditions: Optional[str] = None


class PackageListItem(BaseModel):
    """Brief package info for list views."""
    id: int
    name: str
    slug: str
    code: str
    short_description: Optional[str]
    destination_name: Optional[str] = None
    theme_name: Optional[str] = None
    nights: int
    days: int
    base_price: float
    discounted_price: Optional[float]
    effective_price: float
    discount_percentage: Optional[float]
    star_rating: float
    review_count: int
    is_featured: bool
    is_bestseller: bool
    cover_image_url: Optional[str]
    package_type: PackageType
    
    class Config:
        from_attributes = True


class PackageDetail(PackageBase):
    """Full package details."""
    id: int
    slug: str
    code: str
    star_rating: float
    review_count: int
    display_order: int
    effective_price: float
    discount_percentage: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    theme: Optional[ThemeResponse] = None
    destination: Optional[DestinationResponse] = None
    origin: Optional[DestinationResponse] = None
    itinerary: List[ItineraryResponse] = []
    inclusions: List[InclusionResponse] = []
    images: List[ImageResponse] = []
    
    class Config:
        from_attributes = True


# =============================================================================
# Enquiry Schemas
# =============================================================================

class EnquiryBase(BaseModel):
    name: str = Field(..., max_length=200)
    email: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    
    travel_date: Optional[date] = None
    return_date: Optional[date] = None
    adults: int = Field(1, ge=1)
    children: int = Field(0, ge=0)
    infants: int = Field(0, ge=0)
    
    preferred_budget: Optional[float] = None
    special_requirements: Optional[str] = None
    message: Optional[str] = None


class EnquiryCreate(EnquiryBase):
    package_id: Optional[int] = None


class EnquiryUpdate(BaseModel):
    status: Optional[EnquiryStatus] = None
    quoted_price: Optional[float] = None
    quote_valid_until: Optional[date] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None


class EnquiryResponse(EnquiryBase):
    id: int
    enquiry_ref: str
    package_id: Optional[int]
    user_id: Optional[int]
    status: EnquiryStatus
    quoted_price: Optional[float]
    quote_valid_until: Optional[date]
    assigned_to_id: Optional[int]
    last_contact_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    package_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class EnquiryListResponse(BaseModel):
    enquiries: List[EnquiryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Booking Schemas
# =============================================================================

class TravelerInfo(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None


class BookingCreate(BaseModel):
    package_id: int
    enquiry_id: Optional[int] = None
    
    lead_traveler_name: str
    lead_traveler_email: str
    lead_traveler_phone: str
    travelers: Optional[List[TravelerInfo]] = None
    
    travel_date: date
    return_date: Optional[date] = None
    adults: int = Field(1, ge=1)
    children: int = Field(0, ge=0)
    infants: int = Field(0, ge=0)
    
    special_requests: Optional[str] = None
    payment_mode: Optional[str] = None


class BookingUpdate(BaseModel):
    status: Optional[PackageBookingStatus] = None
    amount_paid: Optional[float] = None
    payment_mode: Optional[str] = None
    payment_reference: Optional[str] = None
    special_requests: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    booking_ref: str
    package_id: int
    user_id: Optional[int]
    
    lead_traveler_name: str
    lead_traveler_email: str
    lead_traveler_phone: str
    
    travel_date: date
    return_date: Optional[date]
    adults: int
    children: int
    infants: int
    
    base_amount: float
    taxes: float
    discount: float
    total_amount: float
    amount_paid: float
    balance_due: float
    currency: str
    
    status: PackageBookingStatus
    payment_mode: Optional[str]
    
    special_requests: Optional[str]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    refund_amount: Optional[float]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    package_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    bookings: List[BookingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Search & Filter Schemas
# =============================================================================

class PackageSearchParams(BaseModel):
    """Search parameters for packages."""
    query: Optional[str] = None
    theme_id: Optional[int] = None
    destination_id: Optional[int] = None
    origin_id: Optional[int] = None
    min_nights: Optional[int] = None
    max_nights: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    package_type: Optional[PackageType] = None
    is_featured: Optional[bool] = None
    travel_date: Optional[date] = None
    sort_by: str = "display_order"  # price_asc, price_desc, rating, newest
    page: int = 1
    page_size: int = 20


class PackageSearchResponse(BaseModel):
    packages: List[PackageListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    filters: dict = {}  # Available filter options
