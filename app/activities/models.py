"""
Activity Database Models

SQLAlchemy models for activities, tours, and experiences.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Date, Time, Enum, Index, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date, time
from typing import Optional, List
import enum

from app.core.database import Base


class ActivityStatus(str, enum.Enum):
    """Activity availability status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD_OUT = "sold_out"
    COMING_SOON = "coming_soon"


class BookingStatus(str, enum.Enum):
    """Activity booking status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    REFUNDED = "refunded"


class ActivityCategory(Base):
    """
    Categories for activities.
    E.g., Adventure, Cultural, Water Sports, Wildlife Safari, etc.
    """
    __tablename__ = "activity_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="category")
    
    __table_args__ = (
        Index('idx_activity_cat_slug', 'slug'),
    )


class ActivityLocation(Base):
    """
    Locations where activities are offered.
    """
    __tablename__ = "activity_locations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True)
    
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="India")
    
    address: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="location")
    
    __table_args__ = (
        Index('idx_activity_loc_slug', 'slug'),
        Index('idx_activity_loc_city', 'city'),
    )


class Activity(Base):
    """
    Main activity/experience model.
    """
    __tablename__ = "activities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # Categorization
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("activity_categories.id"))
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("activity_locations.id"), nullable=False)
    
    # Description
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    highlights: Mapped[Optional[str]] = mapped_column(Text)  # JSON or bullet points
    inclusions: Mapped[Optional[str]] = mapped_column(Text)
    exclusions: Mapped[Optional[str]] = mapped_column(Text)
    important_info: Mapped[Optional[str]] = mapped_column(Text)  # What to bring, know
    
    # Duration
    duration_hours: Mapped[Optional[float]] = mapped_column(Float)  # e.g., 2.5 hours
    duration_text: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "2-3 hours"
    
    # Pricing (per person)
    adult_price: Mapped[float] = mapped_column(Float, default=0)
    child_price: Mapped[float] = mapped_column(Float, default=0)  # Age 5-12
    infant_price: Mapped[float] = mapped_column(Float, default=0)  # Below 5
    
    # Discounts
    discounted_adult_price: Mapped[Optional[float]] = mapped_column(Float)
    discount_percentage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Capacity
    min_participants: Mapped[int] = mapped_column(Integer, default=1)
    max_participants: Mapped[int] = mapped_column(Integer, default=50)
    
    # Media
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    gallery: Mapped[Optional[str]] = mapped_column(JSON)  # List of image URLs
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Ratings
    avg_rating: Mapped[float] = mapped_column(Float, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(ActivityStatus),
        default=ActivityStatus.ACTIVE
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_instant_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Booking settings
    advance_booking_days: Mapped[int] = mapped_column(Integer, default=1)  # Min days in advance
    cancellation_policy: Mapped[Optional[str]] = mapped_column(Text)
    refund_policy: Mapped[Optional[str]] = mapped_column(Text)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    category: Mapped[Optional["ActivityCategory"]] = relationship("ActivityCategory", back_populates="activities")
    location: Mapped["ActivityLocation"] = relationship("ActivityLocation", back_populates="activities")
    slots: Mapped[List["ActivitySlot"]] = relationship("ActivitySlot", back_populates="activity", cascade="all, delete-orphan")
    bookings: Mapped[List["ActivityBooking"]] = relationship("ActivityBooking", back_populates="activity")
    
    __table_args__ = (
        Index('idx_activity_slug', 'slug'),
        Index('idx_activity_code', 'code'),
        Index('idx_activity_category', 'category_id'),
        Index('idx_activity_location', 'location_id'),
        Index('idx_activity_status', 'status'),
    )


class ActivitySlot(Base):
    """
    Available time slots for activities.
    Can be recurring or specific dates.
    """
    __tablename__ = "activity_slots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"), nullable=False)
    
    # Date/Time
    slot_date: Mapped[Optional[date]] = mapped_column(Date)  # Null for recurring slots
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    
    # Recurring pattern (if slot_date is null)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    days_of_week: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., "1,2,3,4,5" for Mon-Fri
    
    # Availability
    max_capacity: Mapped[int] = mapped_column(Integer, default=50)
    available_spots: Mapped[int] = mapped_column(Integer, default=50)
    
    # Pricing override (optional)
    price_override: Mapped[Optional[float]] = mapped_column(Float)  # Override activity price
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # Manually blocked
    block_reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    activity: Mapped["Activity"] = relationship("Activity", back_populates="slots")
    
    __table_args__ = (
        Index('idx_slot_activity', 'activity_id'),
        Index('idx_slot_date', 'slot_date'),
    )


class ActivityBooking(Base):
    """
    Customer bookings for activities.
    """
    __tablename__ = "activity_bookings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Reference
    booking_ref: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # What was booked
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"), nullable=False)
    slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("activity_slots.id"))
    
    # Who booked
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Contact details
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Booking details
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)  # Activity date
    booking_time: Mapped[Optional[time]] = mapped_column(Time)
    
    adults: Mapped[int] = mapped_column(Integer, default=1)
    children: Mapped[int] = mapped_column(Integer, default=0)
    infants: Mapped[int] = mapped_column(Integer, default=0)
    
    # Participants details (JSON)
    participants_data: Mapped[Optional[str]] = mapped_column(JSON)
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    
    # Pricing
    adult_rate: Mapped[float] = mapped_column(Float, default=0)
    child_rate: Mapped[float] = mapped_column(Float, default=0)
    infant_rate: Mapped[float] = mapped_column(Float, default=0)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    taxes: Mapped[float] = mapped_column(Float, default=0)
    convenience_fee: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    
    # Status
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.PENDING
    )
    
    # Payment
    payment_status: Mapped[Optional[str]] = mapped_column(String(20))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Confirmation
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    confirmation_code: Mapped[Optional[str]] = mapped_column(String(50))  # Voucher code
    
    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    refund_amount: Mapped[Optional[float]] = mapped_column(Float)
    
    # Admin
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    booked_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    activity: Mapped["Activity"] = relationship("Activity", back_populates="bookings")
    slot: Mapped[Optional["ActivitySlot"]] = relationship("ActivitySlot")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    booked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[booked_by_id])
    
    __table_args__ = (
        Index('idx_act_booking_ref', 'booking_ref'),
        Index('idx_act_booking_activity', 'activity_id'),
        Index('idx_act_booking_user', 'user_id'),
        Index('idx_act_booking_date', 'booking_date'),
        Index('idx_act_booking_status', 'status'),
    )


# Import for type hints
from app.auth.models import User
