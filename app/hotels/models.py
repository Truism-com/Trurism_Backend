"""
Offline Hotel Database Models

SQLAlchemy models for offline hotel inventory management.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Date, Enum, Index, JSON, Numeric, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from typing import Optional, List
import enum

from app.core.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class HotelStatus(str, enum.Enum):
    """Hotel status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMING_SOON = "coming_soon"
    UNDER_RENOVATION = "under_renovation"


class ContractStatus(str, enum.Enum):
    """Contract status."""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class BookingStatus(str, enum.Enum):
    """Offline hotel booking status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    NO_SHOW = "no_show"


class RateType(str, enum.Enum):
    """Rate types."""
    RACK = "rack"  # Standard published rate
    CONTRACT = "contract"  # Contracted rate
    PROMOTIONAL = "promotional"  # Special promo rate
    SEASONAL = "seasonal"  # Seasonal rate
    WEEKEND = "weekend"  # Weekend rate
    LONG_STAY = "long_stay"  # Extended stay discount


# =============================================================================
# HOTEL CATEGORY
# =============================================================================

class HotelCategory(Base):
    """Hotel categories/star ratings."""
    __tablename__ = "offline_hotel_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    star_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 stars
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    hotels: Mapped[List["Hotel"]] = relationship("Hotel", back_populates="category")


# =============================================================================
# AMENITIES
# =============================================================================

class HotelAmenity(Base):
    """Hotel-level amenities (pool, gym, spa, etc.)."""
    __tablename__ = "offline_hotel_amenities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), default="general")  # general, recreation, business, wellness
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RoomAmenity(Base):
    """Room-level amenities (AC, TV, minibar, etc.)."""
    __tablename__ = "offline_room_amenities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), default="general")  # general, bathroom, entertainment, comfort
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# =============================================================================
# MEAL PLANS
# =============================================================================

class MealPlan(Base):
    """Meal plans (EP, CP, MAP, AP)."""
    __tablename__ = "offline_meal_plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # EP, CP, MAP, AP
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # European Plan, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)
    includes_breakfast: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_lunch: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_dinner: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_all_meals: Mapped[bool] = mapped_column(Boolean, default=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# =============================================================================
# ROOM TYPES
# =============================================================================

class RoomType(Base):
    """Room types (Standard, Deluxe, Suite, etc.)."""
    __tablename__ = "offline_room_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)  # STD, DLX, STE
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Default capacity
    default_occupancy: Mapped[int] = mapped_column(Integer, default=2)
    max_adults: Mapped[int] = mapped_column(Integer, default=2)
    max_children: Mapped[int] = mapped_column(Integer, default=1)
    max_occupancy: Mapped[int] = mapped_column(Integer, default=3)
    
    # Size
    size_sqft: Mapped[Optional[float]] = mapped_column(Float)
    size_sqm: Mapped[Optional[float]] = mapped_column(Float)
    
    # Bedding
    bed_type: Mapped[Optional[str]] = mapped_column(String(100))  # King, Queen, Twin
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    rooms: Mapped[List["HotelRoom"]] = relationship("HotelRoom", back_populates="room_type")


# =============================================================================
# HOTEL
# =============================================================================

class Hotel(Base):
    """Main hotel entity."""
    __tablename__ = "offline_hotels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # HT001
    
    # Category
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("offline_hotel_categories.id"))
    star_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    
    # Description
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    highlights: Mapped[Optional[str]] = mapped_column(Text)  # JSON array or bullet points
    
    # Location
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="India")
    pincode: Mapped[Optional[str]] = mapped_column(String(20))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    
    # Nearby landmarks
    landmarks: Mapped[Optional[str]] = mapped_column(JSON)  # [{name, distance, type}]
    
    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    website: Mapped[Optional[str]] = mapped_column(String(300))
    
    # Check-in/out times
    check_in_time: Mapped[Optional[str]] = mapped_column(String(20), default="14:00")
    check_out_time: Mapped[Optional[str]] = mapped_column(String(20), default="12:00")
    
    # Policies
    cancellation_policy: Mapped[Optional[str]] = mapped_column(Text)
    child_policy: Mapped[Optional[str]] = mapped_column(Text)
    pet_policy: Mapped[Optional[str]] = mapped_column(Text)
    
    # Amenities (JSON array of amenity IDs)
    amenity_ids: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Media
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    gallery: Mapped[Optional[str]] = mapped_column(JSON)  # List of image URLs
    
    # Pricing info (base reference)
    starting_price: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Status
    status: Mapped[HotelStatus] = mapped_column(Enum(HotelStatus), default=HotelStatus.ACTIVE)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Supplier/Source
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50))
    supplier_hotel_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category: Mapped[Optional["HotelCategory"]] = relationship("HotelCategory", back_populates="hotels")
    rooms: Mapped[List["HotelRoom"]] = relationship("HotelRoom", back_populates="hotel", cascade="all, delete-orphan")
    contracts: Mapped[List["HotelContract"]] = relationship("HotelContract", back_populates="hotel", cascade="all, delete-orphan")
    images: Mapped[List["HotelImage"]] = relationship("HotelImage", back_populates="hotel", cascade="all, delete-orphan")
    enquiries: Mapped[List["HotelEnquiry"]] = relationship("HotelEnquiry", back_populates="hotel")
    bookings: Mapped[List["OfflineHotelBooking"]] = relationship("OfflineHotelBooking", back_populates="hotel")
    
    __table_args__ = (
        Index('idx_offline_hotel_city', 'city'),
        Index('idx_offline_hotel_status', 'status'),
        Index('idx_offline_hotel_tenant', 'tenant_id'),
    )


# =============================================================================
# HOTEL ROOM
# =============================================================================

class HotelRoom(Base):
    """Rooms within a hotel."""
    __tablename__ = "offline_hotel_rooms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hotel_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotels.id"), nullable=False)
    room_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_room_types.id"), nullable=False)
    
    # Room identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # "Deluxe Sea View"
    code: Mapped[str] = mapped_column(String(30), nullable=False)  # For this hotel
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Capacity (override room type defaults)
    max_adults: Mapped[int] = mapped_column(Integer, default=2)
    max_children: Mapped[int] = mapped_column(Integer, default=1)
    max_occupancy: Mapped[int] = mapped_column(Integer, default=3)
    extra_bed_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_bed_charge: Mapped[float] = mapped_column(Float, default=0)
    
    # Size
    size_sqft: Mapped[Optional[float]] = mapped_column(Float)
    
    # View type
    view_type: Mapped[Optional[str]] = mapped_column(String(100))  # Sea view, City view, Garden view
    
    # Amenities (JSON array of amenity IDs)
    amenity_ids: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Media
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    gallery: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Total rooms of this type
    total_rooms: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="rooms")
    room_type: Mapped["RoomType"] = relationship("RoomType", back_populates="rooms")
    rates: Mapped[List["HotelRate"]] = relationship("HotelRate", back_populates="room", cascade="all, delete-orphan")
    inventory: Mapped[List["RoomInventory"]] = relationship("RoomInventory", back_populates="room", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('hotel_id', 'code', name='uq_hotel_room_code'),
        Index('idx_hotel_room_hotel', 'hotel_id'),
    )


# =============================================================================
# HOTEL RATES
# =============================================================================

class HotelRate(Base):
    """Room rates with date ranges and meal plans."""
    __tablename__ = "offline_hotel_rates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotel_rooms.id"), nullable=False)
    contract_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("offline_hotel_contracts.id"))
    meal_plan_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("offline_meal_plans.id"))
    
    # Rate identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rate_type: Mapped[RateType] = mapped_column(Enum(RateType), default=RateType.RACK)
    
    # Validity
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Day of week (optional - for weekend rates)
    applicable_days: Mapped[Optional[str]] = mapped_column(JSON)  # [0,1,2,3,4,5,6] Sun=0
    
    # Pricing
    single_rate: Mapped[float] = mapped_column(Float, default=0)  # 1 adult
    double_rate: Mapped[float] = mapped_column(Float, default=0)  # 2 adults
    triple_rate: Mapped[Optional[float]] = mapped_column(Float)  # 3 adults
    quad_rate: Mapped[Optional[float]] = mapped_column(Float)  # 4 adults
    
    extra_adult_rate: Mapped[float] = mapped_column(Float, default=0)
    extra_child_rate: Mapped[float] = mapped_column(Float, default=0)
    child_with_bed_rate: Mapped[float] = mapped_column(Float, default=0)
    child_without_bed_rate: Mapped[float] = mapped_column(Float, default=0)
    
    # Minimum stay
    min_nights: Mapped[int] = mapped_column(Integer, default=1)
    
    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Taxes
    taxes_included: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_percentage: Mapped[float] = mapped_column(Float, default=0)  # GST, etc.
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room: Mapped["HotelRoom"] = relationship("HotelRoom", back_populates="rates")
    contract: Mapped[Optional["HotelContract"]] = relationship("HotelContract", back_populates="rates")
    meal_plan: Mapped[Optional["MealPlan"]] = relationship("MealPlan")
    
    __table_args__ = (
        Index('idx_rate_room', 'room_id'),
        Index('idx_rate_dates', 'valid_from', 'valid_to'),
    )


# =============================================================================
# HOTEL CONTRACT
# =============================================================================

class HotelContract(Base):
    """Contracts with hotels (allotments, net rates)."""
    __tablename__ = "offline_hotel_contracts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hotel_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotels.id"), nullable=False)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Contract identification
    contract_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Validity
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Terms
    commission_percentage: Mapped[float] = mapped_column(Float, default=0)  # Hotel's commission
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100))  # Net 30, Prepaid, etc.
    cancellation_policy: Mapped[Optional[str]] = mapped_column(Text)
    special_terms: Mapped[Optional[str]] = mapped_column(Text)
    
    # Allotment type
    has_allotment: Mapped[bool] = mapped_column(Boolean, default=False)
    allotment_type: Mapped[Optional[str]] = mapped_column(String(50))  # soft, hard
    release_days: Mapped[int] = mapped_column(Integer, default=7)  # Days before to release
    
    # Status
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    
    # Documents
    document_urls: Mapped[Optional[str]] = mapped_column(JSON)  # Contract PDFs
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="contracts")
    rates: Mapped[List["HotelRate"]] = relationship("HotelRate", back_populates="contract")
    
    __table_args__ = (
        Index('idx_contract_hotel', 'hotel_id'),
        Index('idx_contract_dates', 'valid_from', 'valid_to'),
    )


# =============================================================================
# ROOM INVENTORY
# =============================================================================

class RoomInventory(Base):
    """Daily room inventory and availability."""
    __tablename__ = "offline_room_inventory"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotel_rooms.id"), nullable=False)
    
    # Date
    inventory_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Availability
    total_rooms: Mapped[int] = mapped_column(Integer, default=0)
    booked_rooms: Mapped[int] = mapped_column(Integer, default=0)
    blocked_rooms: Mapped[int] = mapped_column(Integer, default=0)  # Maintenance, etc.
    
    @property
    def available_rooms(self) -> int:
        return self.total_rooms - self.booked_rooms - self.blocked_rooms
    
    # Stop sale
    stop_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    stop_sale_reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Cutoff
    cutoff_days: Mapped[int] = mapped_column(Integer, default=0)  # Days before which no booking
    
    # Dynamic pricing override
    rate_override: Mapped[Optional[float]] = mapped_column(Float)  # Override base rate
    
    # Audit
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Relationships
    room: Mapped["HotelRoom"] = relationship("HotelRoom", back_populates="inventory")
    
    __table_args__ = (
        UniqueConstraint('room_id', 'inventory_date', name='uq_room_inventory_date'),
        Index('idx_inventory_date', 'inventory_date'),
        Index('idx_inventory_room', 'room_id'),
    )


# =============================================================================
# HOTEL IMAGES
# =============================================================================

class HotelImage(Base):
    """Hotel and room images."""
    __tablename__ = "offline_hotel_images"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hotel_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotels.id"), nullable=False)
    room_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("offline_hotel_rooms.id"))
    
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    title: Mapped[Optional[str]] = mapped_column(String(200))
    alt_text: Mapped[Optional[str]] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(50), default="general")  # exterior, lobby, room, restaurant, pool
    
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="images")


# =============================================================================
# HOTEL ENQUIRY
# =============================================================================

class HotelEnquiry(Base):
    """Customer enquiries for hotels."""
    __tablename__ = "offline_hotel_enquiries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enquiry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    hotel_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotels.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Guest info
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_email: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Stay details
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    rooms_required: Mapped[int] = mapped_column(Integer, default=1)
    adults: Mapped[int] = mapped_column(Integer, default=2)
    children: Mapped[int] = mapped_column(Integer, default=0)
    
    # Room preference
    room_type_preference: Mapped[Optional[str]] = mapped_column(String(200))
    meal_plan_preference: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Special requests
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    
    # Quote
    quoted_amount: Mapped[Optional[float]] = mapped_column(Float)
    quote_valid_until: Mapped[Optional[date]] = mapped_column(Date)
    
    # Status
    status: Mapped[str] = mapped_column(String(30), default="new")  # new, contacted, quoted, converted, closed
    
    # Remarks
    admin_remarks: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="enquiries")
    
    __table_args__ = (
        Index('idx_hotel_enquiry_status', 'status'),
    )


# =============================================================================
# OFFLINE HOTEL BOOKING
# =============================================================================
class OfflineHotelBooking(Base):
    """Offline hotel bookings."""
    __tablename__ = "offline_hotel_bookings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    hotel_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotels.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("offline_hotel_rooms.id"), nullable=False)
    rate_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("offline_hotel_rates.id"))
    
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    enquiry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("offline_hotel_enquiries.id"))
    
    # Guest info
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_email: Mapped[str] = mapped_column(String(200), nullable=False)
    guest_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    guest_nationality: Mapped[Optional[str]] = mapped_column(String(100))
    guest_id_type: Mapped[Optional[str]] = mapped_column(String(50))  # passport, aadhar, etc.
    guest_id_number: Mapped[Optional[str]] = mapped_column(String(100))

    # ✅ NEW: GST Details
    gst_number: Mapped[Optional[str]] = mapped_column(String(15))
    gst_company_name: Mapped[Optional[str]] = mapped_column(String(255))

    # ✅ NEW: Passport Details
    passport_number: Mapped[Optional[str]] = mapped_column(String(20))
    passport_expiry: Mapped[Optional[date]] = mapped_column(Date)
    
    # Stay details
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)
    rooms_booked: Mapped[int] = mapped_column(Integer, default=1)
    adults: Mapped[int] = mapped_column(Integer, default=2)
    children: Mapped[int] = mapped_column(Integer, default=0)
    
    # Meal plan
    meal_plan: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Pricing
    room_rate: Mapped[float] = mapped_column(Float, nullable=False)
    total_room_charge: Mapped[float] = mapped_column(Float, nullable=False)
    extra_adult_charge: Mapped[float] = mapped_column(Float, default=0)
    extra_child_charge: Mapped[float] = mapped_column(Float, default=0)
    meal_charge: Mapped[float] = mapped_column(Float, default=0)
    taxes: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Payment
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    payment_status: Mapped[str] = mapped_column(String(30), default="pending")
    
    # Booking status
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING)
    
    # Hotel confirmation
    hotel_confirmation_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Special requests
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    
    # Remarks
    internal_remarks: Mapped[Optional[str]] = mapped_column(Text)
    
    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    cancellation_charges: Mapped[float] = mapped_column(Float, default=0)
    refund_amount: Mapped[float] = mapped_column(Float, default=0)
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="bookings")
    
    __table_args__ = (
        Index('idx_offline_booking_status', 'status'),
        Index('idx_offline_booking_dates', 'check_in_date', 'check_out_date'),
        Index('idx_offline_booking_user', 'user_id'),
    )