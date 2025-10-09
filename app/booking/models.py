"""
Booking Database Models

This module defines the database models for booking operations:
- Flight booking model with passenger information
- Hotel booking model with room and guest details
- Bus booking model with seat and journey information
- Booking status tracking and audit fields
- Payment and transaction models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base


class BookingStatus(str, enum.Enum):
    """
    Booking status enumeration for tracking booking lifecycle.
    
    - PENDING: Booking created but payment not confirmed
    - CONFIRMED: Booking confirmed and payment successful
    - CANCELLED: Booking cancelled by user or system
    - REFUNDED: Booking cancelled and refund processed
    - EXPIRED: Booking expired due to timeout
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
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
    """
    CARD = "card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    CASH = "cash"


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


class PassengerInfo(Base):
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
    
    # Relationships
    flight_bookings = relationship("FlightBooking", back_populates="passengers")


class FlightBooking(Base):
    """
    Flight booking model for managing flight reservations.
    
    This model stores flight booking information including passenger details,
    flight details, pricing, and booking status.
    """
    __tablename__ = "flight_bookings"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, index=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="flight_bookings")
    
    # Flight details
    offer_id = Column(String(50), nullable=False)  # From search results
    airline = Column(String(100), nullable=False)
    flight_number = Column(String(20), nullable=False)
    origin = Column(String(3), nullable=False)      # IATA code
    destination = Column(String(3), nullable=False) # IATA code
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    travel_class = Column(String(20), nullable=False)
    
    # Passenger information
    passenger_count = Column(Integer, nullable=False)
    passenger_details = Column(JSON, nullable=False)  # Store passenger info as JSON
    
    # Pricing and payment
    base_fare = Column(Float, nullable=False)
    taxes = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Booking status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    confirmation_number = Column(String(50), nullable=True)  # From airline
    
    # Additional information
    special_requests = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Float, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Booking expiry time
    
    # Relationships
    passengers = relationship("PassengerInfo", secondary="flight_booking_passengers")


class HotelBooking(Base):
    """
    Hotel booking model for managing hotel reservations.
    
    This model stores hotel booking information including guest details,
    room information, pricing, and booking status.
    """
    __tablename__ = "hotel_bookings"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, index=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="hotel_bookings")
    
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
    room_rate = Column(Float, nullable=False)  # Rate per night
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Booking status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    confirmation_number = Column(String(50), nullable=True)  # From hotel
    
    # Additional information
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Float, nullable=True)
    cancellation_policy = Column(String(100), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Booking expiry time


class BusBooking(Base):
    """
    Bus booking model for managing bus reservations.
    
    This model stores bus booking information including passenger details,
    journey information, pricing, and booking status.
    """
    __tablename__ = "bus_bookings"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, index=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="bus_bookings")
    
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
    fare_per_passenger = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Booking status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    confirmation_number = Column(String(50), nullable=True)  # From bus operator
    
    # Additional information
    boarding_point = Column(String(255), nullable=True)
    dropping_point = Column(String(255), nullable=True)
    special_requests = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Float, nullable=True)
    
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
