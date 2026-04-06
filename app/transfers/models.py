"""
Transfer Database Models

SQLAlchemy models for transfer/cab services.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Date, Time, Enum, Index, JSON
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date, time
from typing import Optional, List
import enum

from app.core.database import Base


class TransferBookingStatus(str, enum.Enum):
    """Transfer booking status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DRIVER_ASSIGNED = "driver_assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class CarType(Base):
    """
    Types of cars available for transfer.
    E.g., Sedan, SUV, Tempo Traveller, Luxury, etc.
    """
    __tablename__ = "car_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Car info
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), default="sedan")  # sedan, suv, luxury, tempo
    
    # Capacity
    seating_capacity: Mapped[int] = mapped_column(Integer, default=4)
    luggage_capacity: Mapped[int] = mapped_column(Integer, default=2)  # Number of bags
    
    # Features
    description: Mapped[Optional[str]] = mapped_column(Text)
    features: Mapped[Optional[str]] = mapped_column(Text)  # AC, Music, etc.
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Base pricing (per km or per trip can be route-specific)
    base_price_per_km: Mapped[float] = mapped_column(Float, default=0)
    driver_allowance_per_day: Mapped[float] = mapped_column(Float, default=0)
    night_charges: Mapped[float] = mapped_column(Float, default=0)  # Per night halt
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    routes: Mapped[List["TransferRoute"]] = relationship("TransferRoute", back_populates="car_type")
    bookings: Mapped[List["TransferBooking"]] = relationship("TransferBooking", back_populates="car_type")
    
    __table_args__ = (
        Index('idx_car_type_slug', 'slug'),
        Index('idx_car_type_category', 'category'),
    )


class TransferRoute(Base):
    """
    Pre-defined routes with fixed pricing.
    E.g., Delhi to Agra, Mumbai Airport to City, etc.
    """
    __tablename__ = "transfer_routes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Route info
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    
    # Origin
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_state: Mapped[Optional[str]] = mapped_column(String(100))
    origin_type: Mapped[Optional[str]] = mapped_column(String(50))  # airport, railway, hotel, city
    origin_details: Mapped[Optional[str]] = mapped_column(Text)  # Address, pickup point
    
    # Destination
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_state: Mapped[Optional[str]] = mapped_column(String(100))
    destination_type: Mapped[Optional[str]] = mapped_column(String(50))
    destination_details: Mapped[Optional[str]] = mapped_column(Text)
    
    # Distance and duration
    distance_km: Mapped[float] = mapped_column(Float, default=0)
    duration_hours: Mapped[float] = mapped_column(Float, default=0)
    duration_text: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., "3-4 hours"
    
    # Car type specific pricing
    car_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("car_types.id"), nullable=False)
    
    # Fixed pricing for this route
    base_price: Mapped[float] = mapped_column(Float, default=0)  # One-way base
    round_trip_price: Mapped[Optional[float]] = mapped_column(Float)
    
    # Additional charges
    toll_charges: Mapped[float] = mapped_column(Float, default=0)
    state_tax: Mapped[float] = mapped_column(Float, default=0)
    parking_charges: Mapped[float] = mapped_column(Float, default=0)
    
    # Extra km/hr charges
    extra_km_charge: Mapped[float] = mapped_column(Float, default=0)
    extra_hour_charge: Mapped[float] = mapped_column(Float, default=0)
    
    # Included km/hrs
    included_km: Mapped[float] = mapped_column(Float, default=0)
    included_hours: Mapped[float] = mapped_column(Float, default=0)
    
    # Status
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    car_type: Mapped["CarType"] = relationship("CarType", back_populates="routes")
    bookings: Mapped[List["TransferBooking"]] = relationship("TransferBooking", back_populates="route")
    
    __table_args__ = (
        Index('idx_route_slug', 'slug'),
        Index('idx_route_origin', 'origin_city'),
        Index('idx_route_destination', 'destination_city'),
        Index('idx_route_car', 'car_type_id'),
    )


class TransferBooking(Base):
    """
    Customer transfer bookings.
    """
    __tablename__ = "transfer_bookings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Reference
    booking_ref: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # Route and car
    route_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transfer_routes.id"))
    car_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("car_types.id"), nullable=False)
    
    # Custom route (if not using predefined route)
    custom_pickup: Mapped[Optional[str]] = mapped_column(Text)
    custom_dropoff: Mapped[Optional[str]] = mapped_column(Text)
    custom_distance_km: Mapped[Optional[float]] = mapped_column(Float)
    
    # Trip type
    trip_type: Mapped[str] = mapped_column(String(20), default="one_way")  # one_way, round_trip, hourly
    
    # Who booked
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Passenger info
    passenger_name: Mapped[str] = mapped_column(String(200), nullable=False)
    passenger_email: Mapped[str] = mapped_column(String(255), nullable=False)
    passenger_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    num_passengers: Mapped[int] = mapped_column(Integer, default=1)
    
    # Travel details
    pickup_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_time: Mapped[time] = mapped_column(Time, nullable=False)
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    dropoff_address: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Return trip (for round trip)
    return_date: Mapped[Optional[date]] = mapped_column(Date)
    return_time: Mapped[Optional[time]] = mapped_column(Time)
    
    # Flight/Train details (for airport/railway transfers)
    flight_train_number: Mapped[Optional[str]] = mapped_column(String(50))
    arrival_departure_time: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Pricing
    base_fare: Mapped[float] = mapped_column(Float, default=0)
    toll_charges: Mapped[float] = mapped_column(Float, default=0)
    state_tax: Mapped[float] = mapped_column(Float, default=0)
    parking_charges: Mapped[float] = mapped_column(Float, default=0)
    driver_allowance: Mapped[float] = mapped_column(Float, default=0)
    night_charges: Mapped[float] = mapped_column(Float, default=0)
    extra_charges: Mapped[float] = mapped_column(Float, default=0)
    extra_charges_reason: Mapped[Optional[str]] = mapped_column(String(200))
    discount: Mapped[float] = mapped_column(Float, default=0)
    taxes: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    
    # Status
    status: Mapped[TransferBookingStatus] = mapped_column(
        Enum(TransferBookingStatus),
        default=TransferBookingStatus.PENDING
    )
    
    # Payment
    payment_status: Mapped[Optional[str]] = mapped_column(String(20))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    payment_mode: Mapped[Optional[str]] = mapped_column(String(20))  # online, cash
    
    # Driver assignment
    driver_name: Mapped[Optional[str]] = mapped_column(String(200))
    driver_phone: Mapped[Optional[str]] = mapped_column(String(20))
    driver_vehicle_number: Mapped[Optional[str]] = mapped_column(String(20))
    driver_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Trip tracking
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_km: Mapped[Optional[float]] = mapped_column(Float)
    
    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    refund_amount: Mapped[Optional[float]] = mapped_column(Float)
    
    # Notes
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit
    booked_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    route: Mapped[Optional["TransferRoute"]] = relationship("TransferRoute", back_populates="bookings")
    car_type: Mapped["CarType"] = relationship("CarType", back_populates="bookings")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    booked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[booked_by_id])
    
    __table_args__ = (
        Index('idx_transfer_ref', 'booking_ref'),
        Index('idx_transfer_route', 'route_id'),
        Index('idx_transfer_car', 'car_type_id'),
        Index('idx_transfer_user', 'user_id'),
        Index('idx_transfer_date', 'pickup_date'),
        Index('idx_transfer_status', 'status'),
    )


# Import for type hints
from app.auth.models import User
