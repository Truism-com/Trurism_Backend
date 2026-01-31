"""
Transfer Pydantic Schemas

Request/Response schemas for transfer operations.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time

from app.transfers.models import TransferBookingStatus


# =============================================================================
# Car Type Schemas
# =============================================================================

class CarTypeBase(BaseModel):
    """Base schema for car type."""
    name: str
    slug: Optional[str] = None
    category: str = "sedan"
    seating_capacity: int = 4
    luggage_capacity: int = 2
    description: Optional[str] = None
    features: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0


class CarTypeCreate(CarTypeBase):
    """Schema for creating a car type."""
    base_price_per_km: float = 0
    driver_allowance_per_day: float = 0
    night_charges: float = 0


class CarTypeUpdate(BaseModel):
    """Schema for updating a car type."""
    name: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    seating_capacity: Optional[int] = None
    luggage_capacity: Optional[int] = None
    description: Optional[str] = None
    features: Optional[str] = None
    image_url: Optional[str] = None
    base_price_per_km: Optional[float] = None
    driver_allowance_per_day: Optional[float] = None
    night_charges: Optional[float] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class CarTypeResponse(CarTypeBase):
    """Response schema for car type."""
    id: int
    base_price_per_km: float
    driver_allowance_per_day: float
    night_charges: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Route Schemas
# =============================================================================

class RouteBase(BaseModel):
    """Base schema for transfer route."""
    name: str
    slug: Optional[str] = None
    origin_city: str
    origin_state: Optional[str] = None
    origin_type: Optional[str] = None
    origin_details: Optional[str] = None
    destination_city: str
    destination_state: Optional[str] = None
    destination_type: Optional[str] = None
    destination_details: Optional[str] = None
    distance_km: float = 0
    duration_hours: float = 0
    duration_text: Optional[str] = None
    display_order: int = 0


class RouteCreate(RouteBase):
    """Schema for creating a route."""
    car_type_id: int
    base_price: float = 0
    round_trip_price: Optional[float] = None
    toll_charges: float = 0
    state_tax: float = 0
    parking_charges: float = 0
    extra_km_charge: float = 0
    extra_hour_charge: float = 0
    included_km: float = 0
    included_hours: float = 0
    is_popular: bool = False


class RouteUpdate(BaseModel):
    """Schema for updating a route."""
    name: Optional[str] = None
    slug: Optional[str] = None
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    origin_type: Optional[str] = None
    origin_details: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    destination_type: Optional[str] = None
    destination_details: Optional[str] = None
    distance_km: Optional[float] = None
    duration_hours: Optional[float] = None
    duration_text: Optional[str] = None
    base_price: Optional[float] = None
    round_trip_price: Optional[float] = None
    toll_charges: Optional[float] = None
    state_tax: Optional[float] = None
    parking_charges: Optional[float] = None
    extra_km_charge: Optional[float] = None
    extra_hour_charge: Optional[float] = None
    included_km: Optional[float] = None
    included_hours: Optional[float] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class RouteResponse(RouteBase):
    """Response schema for route."""
    id: int
    car_type_id: int
    base_price: float
    round_trip_price: Optional[float] = None
    toll_charges: float
    state_tax: float
    parking_charges: float
    extra_km_charge: float
    extra_hour_charge: float
    included_km: float
    included_hours: float
    is_popular: bool
    is_active: bool
    created_at: datetime
    car_type: Optional[CarTypeResponse] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# Booking Schemas
# =============================================================================

class BookingCreate(BaseModel):
    """Schema for creating a transfer booking."""
    route_id: Optional[int] = None
    car_type_id: int
    trip_type: str = "one_way"  # one_way, round_trip, hourly
    
    # Custom route (if not using predefined)
    custom_pickup: Optional[str] = None
    custom_dropoff: Optional[str] = None
    custom_distance_km: Optional[float] = None
    
    # Passenger info
    passenger_name: str
    passenger_email: EmailStr
    passenger_phone: str
    num_passengers: int = 1
    
    # Travel details
    pickup_date: date
    pickup_time: time
    pickup_address: str
    dropoff_address: str
    
    # Return (for round trip)
    return_date: Optional[date] = None
    return_time: Optional[time] = None
    
    # Flight/Train details
    flight_train_number: Optional[str] = None
    arrival_departure_time: Optional[str] = None
    
    special_requests: Optional[str] = None


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""
    status: Optional[TransferBookingStatus] = None
    
    # Driver assignment
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_vehicle_number: Optional[str] = None
    
    # Trip tracking
    actual_km: Optional[float] = None
    
    # Extra charges
    extra_charges: Optional[float] = None
    extra_charges_reason: Optional[str] = None
    
    # Payment
    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_mode: Optional[str] = None
    amount_paid: Optional[float] = None
    
    admin_notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Response schema for booking."""
    id: int
    booking_ref: str
    route_id: Optional[int] = None
    car_type_id: int
    trip_type: str
    user_id: Optional[int] = None
    
    passenger_name: str
    passenger_email: str
    passenger_phone: str
    num_passengers: int
    
    pickup_date: date
    pickup_time: time
    pickup_address: str
    dropoff_address: str
    
    return_date: Optional[date] = None
    return_time: Optional[time] = None
    
    flight_train_number: Optional[str] = None
    
    base_fare: float
    toll_charges: float
    state_tax: float
    parking_charges: float
    driver_allowance: float
    night_charges: float
    extra_charges: float
    discount: float
    taxes: float
    total_amount: float
    amount_paid: float
    
    status: TransferBookingStatus
    payment_status: Optional[str] = None
    
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_vehicle_number: Optional[str] = None
    
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookingDetail(BookingResponse):
    """Detailed booking with route and car info."""
    route: Optional[RouteResponse] = None
    car_type: Optional[CarTypeResponse] = None
    custom_pickup: Optional[str] = None
    custom_dropoff: Optional[str] = None
    custom_distance_km: Optional[float] = None
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
# Search/Filter Schemas
# =============================================================================

class RouteSearchParams(BaseModel):
    """Parameters for route search."""
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    car_type_id: Optional[int] = None
    is_popular: Optional[bool] = None
    page: int = 1
    page_size: int = 20


class PriceEstimateRequest(BaseModel):
    """Request for price estimation."""
    route_id: Optional[int] = None
    car_type_id: int
    trip_type: str = "one_way"
    pickup_date: date
    pickup_time: time
    return_date: Optional[date] = None
    custom_distance_km: Optional[float] = None


class PriceEstimateResponse(BaseModel):
    """Response for price estimation."""
    car_type: CarTypeResponse
    base_fare: float
    toll_charges: float
    state_tax: float
    driver_allowance: float
    night_charges: float
    taxes: float
    total_amount: float
    included_km: float
    included_hours: float
    extra_km_charge: float
    extra_hour_charge: float
