from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.booking.models import BookingStatus, PaymentMethod, PaymentStatus, PassengerType


class PassengerSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    age: int = Field(..., ge=0, le=120)
    type: PassengerType
    passport_number: Optional[str] = Field(None, min_length=6, max_length=20)
    nationality: Optional[str] = Field(None, min_length=2, max_length=3)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace(' ', '').replace('-', '').isalpha():
            raise ValueError('Name should contain only letters, spaces, and hyphens')
        return v.title()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v


class PaymentDetailsSchema(BaseModel):
    method: PaymentMethod
    card_number: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = Field(None, min_length=3, max_length=4)
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None
    wallet_type: Optional[str] = None

    @field_validator('card_number')
    @classmethod
    def validate_card_number(cls, v: Optional[str], info) -> Optional[str]:
        method = info.data.get('method')
        if method == PaymentMethod.CARD and not v:
            raise ValueError('Card number is required for card payments')
        if v and not v.replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Invalid card number format')
        return v

    @field_validator('upi_id')
    @classmethod
    def validate_upi_id(cls, v: Optional[str], info) -> Optional[str]:
        method = info.data.get('method')
        if method == PaymentMethod.UPI and not v:
            raise ValueError('UPI ID is required for UPI payments')
        if v and '@' not in v:
            raise ValueError('Invalid UPI ID format')
        return v


class FlightBookingRequest(BaseModel):
    offer_id: str
    passengers: List[PassengerSchema]
    payment_details: PaymentDetailsSchema
    special_requests: Optional[str] = None
    contact_email: str
    contact_phone: str

    @field_validator('passengers')
    @classmethod
    def validate_passengers(cls, v: List[PassengerSchema]) -> List[PassengerSchema]:
        if len(v) > 9:
            raise ValueError('Maximum 9 passengers allowed')

        adult_count = sum(1 for p in v if p.type == PassengerType.ADULT)
        if adult_count == 0:
            raise ValueError('At least one adult required')

        return v


class HotelBookingRequest(BaseModel):
    hotel_id: str
    checkin_date: date
    checkout_date: date
    rooms: int
    adults: int
    children: int = 0
    guest_details: List[Dict[str, Any]]
    payment_details: PaymentDetailsSchema
    special_requests: Optional[str] = None
    contact_email: str
    contact_phone: str

    @field_validator('checkout_date')
    @classmethod
    def validate_checkout_date(cls, v: date, info) -> date:
        checkin_date = info.data.get('checkin_date')
        if checkin_date and v <= checkin_date:
            raise ValueError('Checkout must be after checkin')
        return v


class BusBookingRequest(BaseModel):
    bus_id: str
    travel_date: date
    passengers: int
    passenger_details: List[PassengerSchema]
    payment_details: PaymentDetailsSchema

    selected_seats: List[str] = Field(..., description="Selected seat numbers")  # ✅ ADDED

    boarding_point: Optional[str] = None
    dropping_point: Optional[str] = None
    special_requests: Optional[str] = None
    contact_email: str
    contact_phone: str

    @field_validator('passenger_details')
    @classmethod
    def validate_passenger_details(cls, v: List[PassengerSchema], info) -> List[PassengerSchema]:
        passengers = info.data.get('passengers', 0)

        if len(v) != passengers:
            raise ValueError('Passenger details must match passenger count')

        selected_seats = info.data.get('selected_seats')
        if selected_seats and len(selected_seats) != passengers:
            raise ValueError('Selected seats must match passenger count')

        return v


# ✅ NEW SCHEMA
class SeatLayoutResponse(BaseModel):
    rows: int
    columns: int
    available_seats: List[str]
    booked_seats: List[str]


class BookingResponse(BaseModel):
    booking_id: int
    booking_reference: str
    status: BookingStatus
    confirmation_number: Optional[str] = None
    total_amount: float
    currency: str
    payment_status: PaymentStatus
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BusBookingResponse(BookingResponse):
    operator: str
    bus_type: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    travel_date: datetime
    passengers: int

class AirportCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3)
    name: str
    city: str
    country: str


class AirportResponse(BaseModel):
    id: int
    code: str
    name: str
    city: str
    country: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class AirlineCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=2)
    name: str
    logo_url: Optional[str] = None


class AirlineResponse(BaseModel):
    id: int
    code: str
    name: str
    logo_url: Optional[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)        