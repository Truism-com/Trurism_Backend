"""
Offline Hotel Schemas

Pydantic schemas for hotel API operations.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.hotels.models import HotelStatus, ContractStatus, BookingStatus, RateType


# =============================================================================
# HOTEL CATEGORY SCHEMAS
# =============================================================================

class HotelCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=120)
    star_rating: Optional[int] = Field(None, ge=1, le=5)
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: int = 0


class HotelCategoryCreate(HotelCategoryBase):
    pass


class HotelCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class HotelCategoryResponse(HotelCategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# AMENITY SCHEMAS
# =============================================================================

class AmenityBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=120)
    category: str = Field(default="general", max_length=50)
    icon: Optional[str] = None
    description: Optional[str] = None


class HotelAmenityCreate(AmenityBase):
    pass


class RoomAmenityCreate(AmenityBase):
    pass


class AmenityResponse(AmenityBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


# =============================================================================
# MEAL PLAN SCHEMAS
# =============================================================================

class MealPlanBase(BaseModel):
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    includes_breakfast: bool = False
    includes_lunch: bool = False
    includes_dinner: bool = False
    includes_all_meals: bool = False


class MealPlanCreate(MealPlanBase):
    pass


class MealPlanResponse(MealPlanBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


# =============================================================================
# ROOM TYPE SCHEMAS
# =============================================================================

class RoomTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=120)
    code: str = Field(..., max_length=20)
    description: Optional[str] = None
    default_occupancy: int = 2
    max_adults: int = 2
    max_children: int = 1
    max_occupancy: int = 3
    size_sqft: Optional[float] = None
    size_sqm: Optional[float] = None
    bed_type: Optional[str] = None


class RoomTypeCreate(RoomTypeBase):
    pass


class RoomTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_adults: Optional[int] = None
    max_children: Optional[int] = None
    max_occupancy: Optional[int] = None
    size_sqft: Optional[float] = None
    bed_type: Optional[str] = None
    is_active: Optional[bool] = None


class RoomTypeResponse(RoomTypeBase):
    id: int
    is_active: bool
    display_order: int
    
    class Config:
        from_attributes = True


# =============================================================================
# HOTEL SCHEMAS
# =============================================================================

class HotelBase(BaseModel):
    name: str = Field(..., max_length=300)
    slug: str = Field(..., max_length=320)
    code: str = Field(..., max_length=20)
    
    category_id: Optional[int] = None
    star_rating: Optional[int] = Field(None, ge=1, le=5)
    
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    highlights: Optional[str] = None
    
    address: Optional[str] = None
    city: str = Field(..., max_length=100)
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    check_in_time: Optional[str] = "14:00"
    check_out_time: Optional[str] = "12:00"
    
    cancellation_policy: Optional[str] = None
    child_policy: Optional[str] = None
    pet_policy: Optional[str] = None
    
    amenity_ids: Optional[List[int]] = None
    
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    
    starting_price: float = 0
    currency: str = "INR"


class HotelCreate(HotelBase):
    landmarks: Optional[List[Dict[str, Any]]] = None


class HotelUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[str] = None
    
    category_id: Optional[int] = None
    star_rating: Optional[int] = None
    
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    
    cancellation_policy: Optional[str] = None
    child_policy: Optional[str] = None
    
    amenity_ids: Optional[List[int]] = None
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    
    starting_price: Optional[float] = None
    
    status: Optional[HotelStatus] = None
    is_featured: Optional[bool] = None
    is_popular: Optional[bool] = None


class HotelResponse(BaseModel):
    id: int
    code: str
    name: str
    slug: str
    short_description: Optional[str]
    city: str
    state: Optional[str]
    country: str
    star_rating: Optional[int]
    thumbnail_url: Optional[str]
    starting_price: float
    currency: str
    status: HotelStatus
    is_featured: bool
    is_popular: bool
    
    class Config:
        from_attributes = True


class HotelDetail(HotelBase):
    id: int
    status: HotelStatus
    is_featured: bool
    is_popular: bool
    landmarks: Optional[List[Dict[str, Any]]] = None
    supplier_code: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Nested
    category: Optional[HotelCategoryResponse] = None
    rooms: List["HotelRoomResponse"] = []
    
    class Config:
        from_attributes = True


class HotelListResponse(BaseModel):
    items: List[HotelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HotelSearchParams(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    star_rating: Optional[int] = None
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    amenity_ids: Optional[List[int]] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    rooms: int = 1
    adults: int = 2
    children: int = 0
    query: Optional[str] = None  # Search by name


class HotelSearchResponse(BaseModel):
    hotels: List[HotelResponse]
    total: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any]


# =============================================================================
# HOTEL ROOM SCHEMAS
# =============================================================================

class HotelRoomBase(BaseModel):
    room_type_id: int
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=30)
    description: Optional[str] = None
    
    max_adults: int = 2
    max_children: int = 1
    max_occupancy: int = 3
    extra_bed_allowed: bool = False
    extra_bed_charge: float = 0
    
    size_sqft: Optional[float] = None
    view_type: Optional[str] = None
    
    amenity_ids: Optional[List[int]] = None
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    
    total_rooms: int = 1


class HotelRoomCreate(HotelRoomBase):
    pass


class HotelRoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_adults: Optional[int] = None
    max_children: Optional[int] = None
    max_occupancy: Optional[int] = None
    extra_bed_allowed: Optional[bool] = None
    extra_bed_charge: Optional[float] = None
    size_sqft: Optional[float] = None
    view_type: Optional[str] = None
    amenity_ids: Optional[List[int]] = None
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    total_rooms: Optional[int] = None
    is_active: Optional[bool] = None


class HotelRoomResponse(HotelRoomBase):
    id: int
    hotel_id: int
    is_active: bool
    display_order: int
    room_type: Optional[RoomTypeResponse] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# HOTEL RATE SCHEMAS
# =============================================================================

class HotelRateBase(BaseModel):
    name: str = Field(..., max_length=200)
    rate_type: RateType = RateType.RACK
    meal_plan_id: Optional[int] = None
    contract_id: Optional[int] = None
    
    valid_from: date
    valid_to: date
    applicable_days: Optional[List[int]] = None  # 0=Sun, 6=Sat
    
    single_rate: float = 0
    double_rate: float = 0
    triple_rate: Optional[float] = None
    quad_rate: Optional[float] = None
    
    extra_adult_rate: float = 0
    extra_child_rate: float = 0
    child_with_bed_rate: float = 0
    child_without_bed_rate: float = 0
    
    min_nights: int = 1
    currency: str = "INR"
    
    taxes_included: bool = False
    tax_percentage: float = 0


class HotelRateCreate(HotelRateBase):
    room_id: int


class HotelRateUpdate(BaseModel):
    name: Optional[str] = None
    rate_type: Optional[RateType] = None
    meal_plan_id: Optional[int] = None
    
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    
    single_rate: Optional[float] = None
    double_rate: Optional[float] = None
    triple_rate: Optional[float] = None
    extra_adult_rate: Optional[float] = None
    extra_child_rate: Optional[float] = None
    
    min_nights: Optional[int] = None
    taxes_included: Optional[bool] = None
    tax_percentage: Optional[float] = None
    is_active: Optional[bool] = None


class HotelRateResponse(HotelRateBase):
    id: int
    room_id: int
    is_active: bool
    meal_plan: Optional[MealPlanResponse] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# CONTRACT SCHEMAS
# =============================================================================

class HotelContractBase(BaseModel):
    contract_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    
    valid_from: date
    valid_to: date
    
    commission_percentage: float = 0
    payment_terms: Optional[str] = None
    cancellation_policy: Optional[str] = None
    special_terms: Optional[str] = None
    
    has_allotment: bool = False
    allotment_type: Optional[str] = None
    release_days: int = 7


class HotelContractCreate(HotelContractBase):
    hotel_id: int


class HotelContractUpdate(BaseModel):
    name: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    commission_percentage: Optional[float] = None
    payment_terms: Optional[str] = None
    cancellation_policy: Optional[str] = None
    special_terms: Optional[str] = None
    has_allotment: Optional[bool] = None
    release_days: Optional[int] = None
    status: Optional[ContractStatus] = None


class HotelContractResponse(HotelContractBase):
    id: int
    hotel_id: int
    status: ContractStatus
    document_urls: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# INVENTORY SCHEMAS
# =============================================================================

class RoomInventoryBase(BaseModel):
    inventory_date: date
    total_rooms: int = 0
    booked_rooms: int = 0
    blocked_rooms: int = 0
    stop_sale: bool = False
    stop_sale_reason: Optional[str] = None
    cutoff_days: int = 0
    rate_override: Optional[float] = None


class RoomInventoryUpdate(BaseModel):
    total_rooms: Optional[int] = None
    blocked_rooms: Optional[int] = None
    stop_sale: Optional[bool] = None
    stop_sale_reason: Optional[str] = None
    cutoff_days: Optional[int] = None
    rate_override: Optional[float] = None


class RoomInventoryResponse(RoomInventoryBase):
    id: int
    room_id: int
    available_rooms: int
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BulkInventoryUpdate(BaseModel):
    room_id: int
    start_date: date
    end_date: date
    total_rooms: Optional[int] = None
    blocked_rooms: Optional[int] = None
    stop_sale: Optional[bool] = None
    rate_override: Optional[float] = None


# =============================================================================
# ENQUIRY SCHEMAS
# =============================================================================

class HotelEnquiryBase(BaseModel):
    hotel_id: int
    guest_name: str = Field(..., max_length=200)
    guest_email: EmailStr
    guest_phone: str = Field(..., max_length=50)
    
    check_in_date: date
    check_out_date: date
    rooms_required: int = 1
    adults: int = 2
    children: int = 0
    
    room_type_preference: Optional[str] = None
    meal_plan_preference: Optional[str] = None
    special_requests: Optional[str] = None


class HotelEnquiryCreate(HotelEnquiryBase):
    pass


class HotelEnquiryUpdate(BaseModel):
    status: Optional[str] = None
    quoted_amount: Optional[float] = None
    quote_valid_until: Optional[date] = None
    admin_remarks: Optional[str] = None
    assigned_to_id: Optional[int] = None


class HotelEnquiryResponse(HotelEnquiryBase):
    id: int
    enquiry_number: str
    status: str
    quoted_amount: Optional[float] = None
    quote_valid_until: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class HotelEnquiryListResponse(BaseModel):
    items: List[HotelEnquiryResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# BOOKING SCHEMAS
# =============================================================================

class BookingBase(BaseModel):
    hotel_id: int
    room_id: int
    rate_id: Optional[int] = None
    
    guest_name: str = Field(..., max_length=200)
    guest_email: EmailStr
    guest_phone: str = Field(..., max_length=50)
    guest_nationality: Optional[str] = None
    guest_id_type: Optional[str] = None
    guest_id_number: Optional[str] = None
    
    check_in_date: date
    check_out_date: date
    rooms_booked: int = 1
    adults: int = 2
    children: int = 0
    
    meal_plan: Optional[str] = None
    special_requests: Optional[str] = None


class BookingCreate(BookingBase):
    enquiry_id: Optional[int] = None


class BookingUpdate(BaseModel):
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    special_requests: Optional[str] = None
    internal_remarks: Optional[str] = None
    hotel_confirmation_number: Optional[str] = None
    status: Optional[BookingStatus] = None
    amount_paid: Optional[float] = None
    payment_status: Optional[str] = None


class BookingCancellation(BaseModel):
    cancellation_reason: str
    cancellation_charges: float = 0
    refund_amount: float = 0


class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    hotel_id: int
    room_id: int
    
    guest_name: str
    guest_email: str
    guest_phone: str
    
    check_in_date: date
    check_out_date: date
    nights: int
    rooms_booked: int
    adults: int
    children: int
    
    meal_plan: Optional[str]
    
    room_rate: float
    total_room_charge: float
    taxes: float
    discount: float
    total_amount: float
    currency: str
    
    amount_paid: float
    payment_status: str
    status: BookingStatus
    
    hotel_confirmation_number: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookingDetail(BookingResponse):
    guest_nationality: Optional[str]
    guest_id_type: Optional[str]
    guest_id_number: Optional[str]
    
    extra_adult_charge: float
    extra_child_charge: float
    meal_charge: float
    
    special_requests: Optional[str]
    internal_remarks: Optional[str]
    
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    cancellation_charges: float
    refund_amount: float
    
    hotel: Optional[HotelResponse] = None
    room: Optional[HotelRoomResponse] = None
    
    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    items: List[BookingResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# AVAILABILITY CHECK
# =============================================================================

class AvailabilityRequest(BaseModel):
    hotel_id: int
    room_id: Optional[int] = None
    check_in: date
    check_out: date
    rooms: int = 1


class RoomAvailability(BaseModel):
    room_id: int
    room_name: str
    room_type: str
    available_rooms: int
    rate: float
    rate_type: str
    meal_plan: Optional[str] = None
    taxes: float
    total_per_night: float
    total_for_stay: float


class AvailabilityResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    check_in: date
    check_out: date
    nights: int
    rooms_available: List[RoomAvailability]


# Rebuild models with forward references
HotelDetail.model_rebuild()
