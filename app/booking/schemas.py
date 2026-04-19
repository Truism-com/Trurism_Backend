"""
Booking Module Schemas

This module defines Pydantic schemas for booking operations:
- Booking request schemas for flights, hotels, and buses
- Booking response schemas with confirmation details
- Passenger and guest information schemas
- Payment processing schemas
- Booking status and cancellation schemas
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import re

from app.booking.models import BookingStatus, PaymentMethod, PaymentStatus, PassengerType


class PassengerSchema(BaseModel):
    """
    Schema for passenger information in bookings.
    
    Validates passenger details for flight, hotel, and bus bookings
    including personal information and travel preferences.
    """
    name: str = Field(..., min_length=2, max_length=255, description="Passenger full name")
    age: int = Field(..., ge=0, le=120, description="Passenger age")
    type: PassengerType = Field(..., description="Passenger type (ADT, CHD, INF)")
    passport_number: Optional[str] = Field(None, min_length=6, max_length=20, description="Passport number for international travel")
    nationality: Optional[str] = Field(None, min_length=2, max_length=3, description="ISO country code")
    phone: Optional[str] = Field(None, min_length=10, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate passenger name format."""
        if not v.replace(' ', '').replace('-', '').isalpha():
            raise ValueError('Name should contain only letters, spaces, and hyphens')
        return v.title()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v


class PaymentDetailsSchema(BaseModel):
    """
    Schema for payment information in bookings.
    
    Validates payment method and related details for processing
    bookings with different payment options.
    """
    method: PaymentMethod = Field(..., description="Payment method")
    card_number: Optional[str] = Field(None, description="Card number (masked)")
    card_expiry: Optional[str] = Field(None, description="Card expiry date (MM/YY)")
    card_cvv: Optional[str] = Field(None, min_length=3, max_length=4, description="Card CVV")
    upi_id: Optional[str] = Field(None, description="UPI ID for UPI payments")
    bank_name: Optional[str] = Field(None, description="Bank name for net banking")
    wallet_type: Optional[str] = Field(None, description="Wallet type for wallet payments")
    
    @field_validator('card_number')
    @classmethod
    def validate_card_number(cls, v: Optional[str], info) -> Optional[str]:
        """Validate card number format."""
        method = info.data.get('method')
        if method == PaymentMethod.CARD and not v:
            raise ValueError('Card number is required for card payments')
        if v and not v.replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Invalid card number format')
        return v
    
    @field_validator('upi_id')
    @classmethod
    def validate_upi_id(cls, v: Optional[str], info) -> Optional[str]:
        """Validate UPI ID format."""
        method = info.data.get('method')
        if method == PaymentMethod.UPI and not v:
            raise ValueError('UPI ID is required for UPI payments')
        if v and '@' not in v:
            raise ValueError('Invalid UPI ID format')
        return v


# ─── GST / Passport validators (reusable) ────────────────────────────────────

GST_PATTERN = re.compile(
    r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
)
PASSPORT_PATTERN = re.compile(
    r'^[A-PR-WY][1-9]\d\s?\d{4}[1-9]$'
)


def validate_gst_number(v: Optional[str]) -> Optional[str]:
    """
    Validate GST number format.
    Must be 15-character alphanumeric as per Indian GST standards.
    Example: 22AAAAA0000A1Z5
    """
    if v is None:
        return v
    v = v.strip().upper()
    if not GST_PATTERN.match(v):
        raise ValueError(
            'Invalid GST number. Must be 15-character alphanumeric '
            '(e.g., 22AAAAA0000A1Z5)'
        )
    return v


def validate_passport_number(v: Optional[str]) -> Optional[str]:
    """
    Validate passport number format.
    Indian passport: 1 letter + 7 digits (e.g., A1234567).
    International passports follow similar patterns.
    """
    if v is None:
        return v
    v = v.strip().upper()
    if not PASSPORT_PATTERN.match(v):
        raise ValueError(
            'Invalid passport number format '
            '(e.g., A1234567)'
        )
    return v


# ─── Flight Booking ───────────────────────────────────────────────────────────

class FlightBookingRequest(BaseModel):
    """
    Schema for flight booking requests.
    
    Validates flight booking data including passenger information,
    flight details, and payment information.
    """
    offer_id: str = Field(..., description="Flight offer ID from search results")
    passengers: List[PassengerSchema] = Field(..., min_items=1, max_items=9, description="List of passengers")
    payment_details: PaymentDetailsSchema = Field(..., description="Payment information")
    special_requests: Optional[str] = Field(None, max_length=500, description="Special requests or preferences")
    contact_email: str = Field(..., description="Contact email for booking confirmation")
    contact_phone: str = Field(..., min_length=10, max_length=20, description="Contact phone number")

    # ── Compliance fields ──────────────────────────────────────────────────
    gst_number: Optional[str] = Field(
        None,
        max_length=15,
        description="GST number for business bookings (15-char alphanumeric)"
    )
    gst_company_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Company name registered under GST"
    )
    passport_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Passport number of primary traveller (for international flights)"
    )
    passport_expiry: Optional[date] = Field(
        None,
        description="Passport expiry date of primary traveller"
    )

    @field_validator('passengers')
    @classmethod
    def validate_passengers(cls, v: List[PassengerSchema]) -> List[PassengerSchema]:
        """Validate passenger count and types."""
        if len(v) > 9:
            raise ValueError('Maximum 9 passengers allowed per booking')
        
        adult_count = sum(1 for p in v if p.type == PassengerType.ADULT)
        if adult_count == 0:
            raise ValueError('At least one adult passenger is required')
        
        infant_count = sum(1 for p in v if p.type == PassengerType.INFANT)
        if infant_count > adult_count:
            raise ValueError('Number of infants cannot exceed number of adults')
        
        return v

    @field_validator('gst_number')
    @classmethod
    def _validate_gst_number(cls, v: Optional[str]) -> Optional[str]:
        return validate_gst_number(v)

    @field_validator('passport_number')
    @classmethod
    def _validate_passport_number(cls, v: Optional[str]) -> Optional[str]:
        return validate_passport_number(v)


# ─── Hotel Booking ────────────────────────────────────────────────────────────

class HotelBookingRequest(BaseModel):
    """
    Schema for hotel booking requests.
    
    Validates hotel booking data including guest information,
    room details, and payment information.
    """
    hotel_id: str = Field(..., description="Hotel ID from search results")
    checkin_date: date = Field(..., description="Check-in date")
    checkout_date: date = Field(..., description="Check-out date")
    rooms: int = Field(..., ge=1, le=9, description="Number of rooms")
    adults: int = Field(..., ge=1, le=18, description="Number of adult guests")
    children: int = Field(0, ge=0, le=18, description="Number of child guests")
    guest_details: List[Dict[str, Any]] = Field(..., description="Guest information for each room")
    payment_details: PaymentDetailsSchema = Field(..., description="Payment information")
    special_requests: Optional[str] = Field(None, max_length=500, description="Special requests")
    contact_email: str = Field(..., description="Contact email for booking confirmation")
    contact_phone: str = Field(..., min_length=10, max_length=20, description="Contact phone number")

    # ── Compliance fields ──────────────────────────────────────────────────
    gst_number: Optional[str] = Field(
        None,
        max_length=15,
        description="GST number for business bookings (15-char alphanumeric)"
    )
    gst_company_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Company name registered under GST"
    )
    passport_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Passport number of primary guest"
    )
    passport_expiry: Optional[date] = Field(
        None,
        description="Passport expiry date of primary guest"
    )

    @field_validator('checkout_date')
    @classmethod
    def validate_checkout_date(cls, v: date, info) -> date:
        """Validate checkout date is after checkin date."""
        checkin_date = info.data.get('checkin_date')
        if checkin_date and v <= checkin_date:
            raise ValueError('Checkout date must be after checkin date')
        return v
    
    @field_validator('guest_details')
    @classmethod
    def validate_guest_details(cls, v: List[Dict[str, Any]], info) -> List[Dict[str, Any]]:
        """Validate guest details match room count."""
        rooms = info.data.get('rooms', 0)
        if len(v) != rooms:
            raise ValueError('Guest details must be provided for each room')
        return v

    @field_validator('gst_number')
    @classmethod
    def _validate_gst_number(cls, v: Optional[str]) -> Optional[str]:
        return validate_gst_number(v)

    @field_validator('passport_number')
    @classmethod
    def _validate_passport_number(cls, v: Optional[str]) -> Optional[str]:
        return validate_passport_number(v)


# ─── Bus Booking ──────────────────────────────────────────────────────────────

class BusBookingRequest(BaseModel):
    """
    Schema for bus booking requests.
    
    Validates bus booking data including passenger information,
    journey details, and payment information.
    """
    bus_id: str = Field(..., description="Bus ID from search results")
    travel_date: date = Field(..., description="Travel date")
    passengers: int = Field(..., ge=1, le=9, description="Number of passengers")
    passenger_details: List[PassengerSchema] = Field(..., description="Passenger information")
    payment_details: PaymentDetailsSchema = Field(..., description="Payment information")
    boarding_point: Optional[str] = Field(None, description="Preferred boarding point")
    dropping_point: Optional[str] = Field(None, description="Preferred dropping point")
    special_requests: Optional[str] = Field(None, max_length=500, description="Special requests")
    contact_email: str = Field(..., description="Contact email for booking confirmation")
    contact_phone: str = Field(..., min_length=10, max_length=20, description="Contact phone number")

    # ── Compliance fields ──────────────────────────────────────────────────
    gst_number: Optional[str] = Field(
        None,
        max_length=15,
        description="GST number for business bookings (15-char alphanumeric)"
    )
    gst_company_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Company name registered under GST"
    )
    passport_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Passport number of primary passenger"
    )
    passport_expiry: Optional[date] = Field(
        None,
        description="Passport expiry date of primary passenger"
    )

    @field_validator('passenger_details')
    @classmethod
    def validate_passenger_details(cls, v: List[PassengerSchema], info) -> List[PassengerSchema]:
        """Validate passenger details match passenger count."""
        passengers = info.data.get('passengers', 0)
        if len(v) != passengers:
            raise ValueError('Passenger details must match passenger count')
        return v

    @field_validator('gst_number')
    @classmethod
    def _validate_gst_number(cls, v: Optional[str]) -> Optional[str]:
        return validate_gst_number(v)

    @field_validator('passport_number')
    @classmethod
    def _validate_passport_number(cls, v: Optional[str]) -> Optional[str]:
        return validate_passport_number(v)


# ─── Response Schemas (unchanged) ─────────────────────────────────────────────

class BookingResponse(BaseModel):
    """
    Schema for booking confirmation responses.
    
    Returns booking confirmation details including reference numbers,
    status, and payment information.
    """
    booking_id: int = Field(..., description="Unique booking ID")
    booking_reference: str = Field(..., description="Booking reference number")
    status: BookingStatus = Field(..., description="Current booking status")
    confirmation_number: Optional[str] = Field(None, description="Confirmation number from provider")
    total_amount: float = Field(..., ge=0, description="Total booking amount")
    currency: str = Field(..., description="Currency code")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    expires_at: Optional[datetime] = Field(None, description="Booking expiry time")
    created_at: datetime = Field(..., description="Booking creation time")
    
    model_config = ConfigDict(from_attributes=True)


class FlightBookingResponse(BookingResponse):
    """Schema for flight booking confirmation responses."""
    airline: str = Field(..., description="Airline name")
    flight_number: str = Field(..., description="Flight number")
    origin: str = Field(..., description="Origin airport code")
    destination: str = Field(..., description="Destination airport code")
    departure_time: datetime = Field(..., description="Departure time")
    arrival_time: datetime = Field(..., description="Arrival time")
    travel_class: str = Field(..., description="Travel class")
    passenger_count: int = Field(..., description="Number of passengers")


class HotelBookingResponse(BookingResponse):
    """Schema for hotel booking confirmation responses."""
    hotel_name: str = Field(..., description="Hotel name")
    hotel_address: str = Field(..., description="Hotel address")
    city: str = Field(..., description="City name")
    checkin_date: datetime = Field(..., description="Check-in date")
    checkout_date: datetime = Field(..., description="Check-out date")
    nights: int = Field(..., description="Number of nights")
    rooms: int = Field(..., description="Number of rooms")
    adults: int = Field(..., description="Number of adults")
    children: int = Field(..., description="Number of children")


class BusBookingResponse(BookingResponse):
    """Schema for bus booking confirmation responses."""
    operator: str = Field(..., description="Bus operator name")
    bus_type: str = Field(..., description="Bus type")
    origin: str = Field(..., description="Origin location")
    destination: str = Field(..., description="Destination location")
    departure_time: datetime = Field(..., description="Departure time")
    arrival_time: datetime = Field(..., description="Arrival time")
    travel_date: datetime = Field(..., description="Travel date")
    passengers: int = Field(..., description="Number of passengers")


class BookingListResponse(BaseModel):
    """Schema for paginated booking list responses."""
    total: int = Field(..., ge=0, description="Total number of bookings")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Number of bookings per page")
    bookings: List[Dict[str, Any]] = Field(..., description="List of bookings")


class BookingDetailsResponse(BaseModel):
    """Schema for detailed booking information responses."""
    booking_id: int = Field(..., description="Unique booking ID")
    booking_reference: str = Field(..., description="Booking reference number")
    type: str = Field(..., description="Booking type (flight, hotel, bus)")
    status: BookingStatus = Field(..., description="Current booking status")
    total_amount: float = Field(..., ge=0, description="Total booking amount")
    currency: str = Field(..., description="Currency code")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    details: Dict[str, Any] = Field(..., description="Booking-specific details")
    passenger_details: List[Dict[str, Any]] = Field(..., description="Passenger information")
    created_at: datetime = Field(..., description="Booking creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class CancelBookingRequest(BaseModel):
    """Schema for booking cancellation requests."""
    reason: str = Field(..., min_length=10, max_length=500, description="Cancellation reason")
    refund_preference: Optional[str] = Field(None, description="Refund method preference")
    contact_for_refund: Optional[bool] = Field(True, description="Whether to contact for refund processing")


class CancelBookingResponse(BaseModel):
    """Schema for booking cancellation responses."""
    booking_id: int = Field(..., description="Booking ID that was cancelled")
    status: BookingStatus = Field(..., description="Updated booking status")
    refund_amount: Optional[float] = Field(None, ge=0, description="Refund amount")
    currency: str = Field(..., description="Currency code")
    refund_processing_time: Optional[str] = Field(None, description="Expected refund processing time")
    cancellation_fee: Optional[float] = Field(None, ge=0, description="Cancellation fee applied")
    message: str = Field(..., description="Cancellation confirmation message")