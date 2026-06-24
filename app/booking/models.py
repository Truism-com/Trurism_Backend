"""
Booking Database Models

This module defines the database models for booking operations:
- Flight booking model with passenger information
- Hotel booking model with room and guest details
- Bus booking model with seat and journey information
- Booking status tracking and audit fields
- Payment and transaction models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, JSON, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from decimal import Decimal

from app.core.database import Base
from app.core.mixins import TenantMixin


class BookingStatus(str, enum.Enum):
    """
    Booking status enumeration for tracking booking lifecycle.
    
    - PENDING: Booking created but payment not confirmed
    - CONFIRMED: Booking confirmed, payment successful, and ticket issued
    - TICKETING_FAILED: Payment captured but airline ticketing failed; requires manual intervention
    - CANCELLED: Booking cancelled by user or system
    - REFUNDED: Booking cancelled and refund processed
    - EXPIRED: Booking expired due to timeout
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    TICKETING_FAILED = "ticketing_failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentStatus(str, enum.Enum):
    """
    Payment status enumeration for tracking payment lifecycle.
    
    - PENDING: Payment initiated but not completed
    - SUCCESS: Payment completed successfully
    - FAILED: Payment failed or declined
    - REFUNDED: Payment refunded
    - PARTIAL_REFUND: Partial refund processed
    """
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"


class PaymentMethod(str, enum.Enum):
    """
    Payment method enumeration for different payment options.
    
    - CARD: Credit/Debit card payment
    - UPI: UPI payment
    - NET_BANKING: Net banking
    - WALLET: Digital wallet payment
    - CASH: Cash payment (for offline bookings)
    - AGENT_CREDIT: Agent credit payment (for B2B agents)
    """
    CARD = "card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    CASH = "cash"
    AGENT_CREDIT = "agent_credit"


class PassengerType(str, enum.Enum):
    """
    Passenger type enumeration for pricing and booking calculations.
    
    - ADULT: Adult passenger
    - CHILD: Child passenger
    - INFANT: Infant passenger
    """
    ADULT = "ADT"
    CHILD = "CHD"
    INFANT = "INF"


class PassengerInfo(Base, TenantMixin):
    """
    Passenger information model for bookings.
    
    This model stores passenger details that can be shared across
    different booking types (flight, hotel, bus).
    """
    __tablename__ = "passengers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    type = Column(Enum(PassengerType), nullable=False)
    passport_number = Column(String(20), nullable=True)  # For international flights
    nationality = Column(String(3), nullable=True)       # ISO country code
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (via secondary table flight_booking_passengers)
    flight_bookings = relationship("FlightBooking", secondary="flight_booking_passengers", viewonly=True)


class FlightBooking(Base, TenantMixin):
    """
    Flight booking model for managing flight reservations.
    
    This model stores flight booking information including passenger details,
    flight details, pricing, and booking status.
    """
    __tablename__ = "flight_bookings"
    __table_args__ = (
        UniqueConstraint('booking_reference', 'tenant_id', name='uq_flight_booking_ref_tenant'),
        Index('ix_flight_bookings_tenant_id', 'tenant_id'),
    )

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), index=True, nullable=False)

    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="flight_bookings", foreign_keys=[user_id])
    
    # Salesperson/Agent tracking (who created this booking)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Flight details
    offer_id = Column(String(50), nullable=False)  # From search results
    airline = Column(String(100), nullable=False)
    flight_number = Column(String(20), nullable=False)
    origin = Column(String(3), nullable=False)      # IATA code
    destination = Column(String(3), nullable=False) # IATA code
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    travel_class = Column(String(20), nullable=False)
    search_guid = Column(String(100), nullable=True)  # Reserved for future use
    
    # Passenger information
    passenger_count = Column(Integer, nullable=False)
    passenger_details = Column(JSON, nullable=False)  # Store passenger info as JSON
    
    # Pricing and payment
    base_fare = Column(Numeric(14, 2), nullable=False)
    taxes = Column(Numeric(14, 2), nullable=False)
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Booking status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    confirmation_number = Column(String(50), nullable=True)  # From airline
    pnr = Column(String(10), nullable=True)  # Passenger Name Record from airline
    airiq_booking_id = Column(String(100), nullable=True)  # AIR IQ booking_id from POST /book
    celery_task_id = Column(String(100), nullable=True)  # Celery task ID for async ticket issuance
    
    # Additional information
    special_requests = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Numeric(14, 2), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Booking expiry time
    
    # Relationships
    passengers = relationship("PassengerInfo", secondary="flight_booking_passengers")


class HotelBooking(Base, TenantMixin):
    """
    Hotel booking model for managing hotel reservations.
    
    This model stores hotel booking information including guest details,
    room information, pricing, and booking status.
    """
    __tablename__ = "hotel_bookings"
    __table_args__ = (
        UniqueConstraint('booking_reference', 'tenant_id', name='uq_hotel_booking_ref_tenant'),
        Index('ix_hotel_bookings_tenant_id', 'tenant_id'),
    )
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), index=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="hotel_bookings", foreign_keys=[user_id])
    
    # Salesperson/Agent tracking (who created this booking)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Hotel details
    hotel_id = Column(String(50), nullable=False)  # From search results
    hotel_name = Column(String(255), nullable=False)
    hotel_address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    
    # Booking details
    checkin_date = Column(DateTime(timezone=True), nullable=False)
    checkout_date = Column(DateTime(timezone=True), nullable=False)
    nights = Column(Integer, nullable=False)
    rooms = Column(Integer, nullable=False)
    adults = Column(Integer, nullable=False)
    children = Column(Integer, nullable=False)
    
    # Guest information
    guest_details = Column(JSON, nullable=False)  # Store guest info as JSON
    special_requests = Column(Text, nullable=True)
    
    # Pricing and payment
    room_rate = Column(Numeric(14, 2), nullable=False)  # Rate per night
    base_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    taxes = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Booking status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    confirmation_number = Column(String(50), nullable=True)  # From hotel
    
    # Additional information
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Numeric(14, 2), nullable=True)
    cancellation_policy = Column(String(100), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Booking expiry time


class BusBooking(Base, TenantMixin):
    """
    Bus booking model for managing bus reservations.
    
    This model stores bus booking information including passenger details,
    journey information, pricing, and booking status.
    """
    __tablename__ = "bus_bookings"
    __table_args__ = (
        UniqueConstraint('booking_reference', 'tenant_id', name='uq_bus_booking_ref_tenant'),
        Index('ix_bus_bookings_tenant_id', 'tenant_id'),
    )
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), index=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="bus_bookings", foreign_keys=[user_id])
    
    # Salesperson/Agent tracking (who created this booking)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Bus details
    bus_id = Column(String(50), nullable=False)  # From search results
    operator = Column(String(100), nullable=False)
    bus_type = Column(String(50), nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    
    # Booking details
    travel_date = Column(DateTime(timezone=True), nullable=False)
    passengers = Column(Integer, nullable=False)
    seat_numbers = Column(JSON, nullable=True)  # Store seat numbers as JSON array
    
    # Passenger information
    passenger_details = Column(JSON, nullable=False)  # Store passenger info as JSON
    
    # Pricing and payment
    fare_per_passenger = Column(Numeric(14, 2), nullable=False)
    base_amount = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    taxes = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Booking status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    confirmation_number = Column(String(50), nullable=True)  # From bus operator
    ticket_number = Column(String(20), nullable=True)  # Unique ticket identifier
    
    # Additional information
    boarding_point = Column(String(255), nullable=True)
    dropping_point = Column(String(255), nullable=True)
    special_requests = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Numeric(14, 2), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Booking expiry time


# Association table for flight booking passengers
class FlightBookingPassenger(Base):
    """
    Association table for linking flight bookings with passenger information.
    
    This table creates a many-to-many relationship between flight bookings
    and passenger information.
    """
    __tablename__ = "flight_booking_passengers"
    
    booking_id = Column(Integer, ForeignKey("flight_bookings.id"), primary_key=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id"), primary_key=True)
    
    # Additional booking-specific passenger info
    seat_number = Column(String(10), nullable=True)
    meal_preference = Column(String(50), nullable=True)
    special_assistance = Column(Text, nullable=True)
