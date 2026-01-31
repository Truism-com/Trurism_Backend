"""
Holiday Package Database Models

Models for holiday/tour package management including:
- Packages with themes and destinations
- Day-wise itineraries
- Inclusions/Exclusions
- Customer enquiries and bookings
"""

from sqlalchemy import String, Text, ForeignKey, Index, Boolean, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
import enum
from datetime import datetime, date

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User


class PackageType(str, enum.Enum):
    """Type of holiday package."""
    FIXED_DEPARTURE = "fixed_departure"  # Fixed dates, fixed price
    CUSTOMIZABLE = "customizable"  # Can be customized per customer
    GROUP_TOUR = "group_tour"  # Group departures


class EnquiryStatus(str, enum.Enum):
    """Status of package enquiry."""
    NEW = "new"
    CONTACTED = "contacted"
    QUOTE_SENT = "quote_sent"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    CLOSED = "closed"


class PackageBookingStatus(str, enum.Enum):
    """Status of package booking."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PARTIALLY_PAID = "partially_paid"
    FULLY_PAID = "fully_paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PackageTheme(Base):
    """
    Holiday package themes/categories.
    
    Examples: Wildlife, Religious, Honeymoon, Adventure, Beach, etc.
    """
    __tablename__ = "package_themes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Icon class or URL
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(default=0)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    packages: Mapped[List["HolidayPackage"]] = relationship("HolidayPackage", back_populates="theme")
    
    def __repr__(self):
        return f"<PackageTheme(id={self.id}, name={self.name})>"


class PackageDestination(Base):
    """
    Destinations for holiday packages.
    
    Can be used for both origin cities and destination locations.
    """
    __tablename__ = "package_destinations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_international: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    packages_as_destination: Mapped[List["HolidayPackage"]] = relationship(
        "HolidayPackage", 
        back_populates="destination",
        foreign_keys="HolidayPackage.destination_id"
    )
    packages_as_origin: Mapped[List["HolidayPackage"]] = relationship(
        "HolidayPackage",
        back_populates="origin",
        foreign_keys="HolidayPackage.origin_id"
    )
    
    def __repr__(self):
        return f"<PackageDestination(id={self.id}, name={self.name})>"


class HolidayPackage(Base):
    """
    Main holiday/tour package model.
    
    Contains all package details including pricing, duration,
    and metadata for search and display.
    """
    __tablename__ = "holiday_packages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # Package code like PKG001
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Categorization
    theme_id: Mapped[Optional[int]] = mapped_column(ForeignKey("package_themes.id"), nullable=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("package_destinations.id"))
    origin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("package_destinations.id"), nullable=True)
    
    # Duration
    nights: Mapped[int] = mapped_column(default=1)
    days: Mapped[int] = mapped_column(default=2)
    
    # Pricing
    base_price: Mapped[float] = mapped_column(default=0.0)  # Per person price
    discounted_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    child_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    infant_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    single_supplement: Mapped[Optional[float]] = mapped_column(nullable=True)  # Extra for single occupancy
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Type and availability
    package_type: Mapped[PackageType] = mapped_column(default=PackageType.CUSTOMIZABLE)
    departure_dates: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of dates for fixed departures
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    min_pax: Mapped[int] = mapped_column(default=1)
    max_pax: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Rating and reviews
    star_rating: Mapped[float] = mapped_column(default=0.0)  # Average rating
    review_count: Mapped[int] = mapped_column(default=0)
    
    # Display settings
    is_featured: Mapped[bool] = mapped_column(default=False)
    is_bestseller: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(default=0)
    
    # Cover image
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Policies (stored as JSON or Text)
    cancellation_policy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    terms_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    theme: Mapped[Optional["PackageTheme"]] = relationship("PackageTheme", back_populates="packages")
    destination: Mapped["PackageDestination"] = relationship(
        "PackageDestination", 
        back_populates="packages_as_destination",
        foreign_keys=[destination_id]
    )
    origin: Mapped[Optional["PackageDestination"]] = relationship(
        "PackageDestination",
        back_populates="packages_as_origin", 
        foreign_keys=[origin_id]
    )
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    
    itinerary: Mapped[List["PackageItinerary"]] = relationship(
        "PackageItinerary", 
        back_populates="package",
        order_by="PackageItinerary.day_number"
    )
    inclusions: Mapped[List["PackageInclusion"]] = relationship(
        "PackageInclusion",
        back_populates="package"
    )
    images: Mapped[List["PackageImage"]] = relationship(
        "PackageImage",
        back_populates="package",
        order_by="PackageImage.display_order"
    )
    enquiries: Mapped[List["PackageEnquiry"]] = relationship("PackageEnquiry", back_populates="package")
    bookings: Mapped[List["PackageBooking"]] = relationship("PackageBooking", back_populates="package")
    
    @property
    def effective_price(self) -> float:
        """Get the effective price (discounted or base)."""
        return self.discounted_price if self.discounted_price else self.base_price
    
    @property
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage if applicable."""
        if self.discounted_price and self.base_price > 0:
            return round((1 - self.discounted_price / self.base_price) * 100, 1)
        return None
    
    def __repr__(self):
        return f"<HolidayPackage(id={self.id}, name={self.name})>"


class PackageItinerary(Base):
    """
    Day-wise itinerary for holiday packages.
    """
    __tablename__ = "package_itineraries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("holiday_packages.id", ondelete="CASCADE"))
    
    day_number: Mapped[int] = mapped_column()  # Day 1, Day 2, etc.
    title: Mapped[str] = mapped_column(String(200))  # e.g., "Arrival in Goa"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Optional details
    meals_included: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # B, L, D or combinations
    accommodation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    activities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of activities
    
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    package: Mapped["HolidayPackage"] = relationship("HolidayPackage", back_populates="itinerary")
    
    def __repr__(self):
        return f"<PackageItinerary(package_id={self.package_id}, day={self.day_number})>"


class PackageInclusion(Base):
    """
    Inclusions and exclusions for holiday packages.
    """
    __tablename__ = "package_inclusions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("holiday_packages.id", ondelete="CASCADE"))
    
    item: Mapped[str] = mapped_column(String(300))
    is_included: Mapped[bool] = mapped_column(default=True)  # True = Inclusion, False = Exclusion
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # meals, transport, etc.
    display_order: Mapped[int] = mapped_column(default=0)
    
    # Relationships
    package: Mapped["HolidayPackage"] = relationship("HolidayPackage", back_populates="inclusions")
    
    def __repr__(self):
        return f"<PackageInclusion(item={self.item}, included={self.is_included})>"


class PackageImage(Base):
    """
    Image gallery for holiday packages.
    """
    __tablename__ = "package_images"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("holiday_packages.id", ondelete="CASCADE"))
    
    image_url: Mapped[str] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    alt_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    package: Mapped["HolidayPackage"] = relationship("HolidayPackage", back_populates="images")
    
    def __repr__(self):
        return f"<PackageImage(package_id={self.package_id}, url={self.image_url})>"


class PackageEnquiry(Base):
    """
    Customer enquiries for holiday packages.
    """
    __tablename__ = "package_enquiries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    enquiry_ref: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    
    # Package reference (optional - can be general enquiry)
    package_id: Mapped[Optional[int]] = mapped_column(ForeignKey("holiday_packages.id"), nullable=True)
    
    # Customer details
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # If logged in
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    
    # Enquiry details
    travel_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    adults: Mapped[int] = mapped_column(default=1)
    children: Mapped[int] = mapped_column(default=0)
    infants: Mapped[int] = mapped_column(default=0)
    
    # Customization preferences
    preferred_budget: Mapped[Optional[float]] = mapped_column(nullable=True)
    special_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[EnquiryStatus] = mapped_column(default=EnquiryStatus.NEW)
    
    # Quoted price (after discussion)
    quoted_price: Mapped[Optional[float]] = mapped_column(nullable=True)
    quote_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Follow-up
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Internal notes
    last_contact_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    package: Mapped[Optional["HolidayPackage"]] = relationship("HolidayPackage", back_populates="enquiries")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])
    
    def __repr__(self):
        return f"<PackageEnquiry(ref={self.enquiry_ref}, status={self.status})>"


class PackageBooking(Base):
    """
    Confirmed bookings for holiday packages.
    """
    __tablename__ = "package_bookings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    booking_ref: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    
    # References
    package_id: Mapped[int] = mapped_column(ForeignKey("holiday_packages.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    enquiry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("package_enquiries.id"), nullable=True)
    
    # Traveler details
    lead_traveler_name: Mapped[str] = mapped_column(String(200))
    lead_traveler_email: Mapped[str] = mapped_column(String(255))
    lead_traveler_phone: Mapped[str] = mapped_column(String(20))
    travelers_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of all travelers
    
    # Booking details
    travel_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    adults: Mapped[int] = mapped_column(default=1)
    children: Mapped[int] = mapped_column(default=0)
    infants: Mapped[int] = mapped_column(default=0)
    
    # Pricing
    base_amount: Mapped[float] = mapped_column()
    taxes: Mapped[float] = mapped_column(default=0.0)
    discount: Mapped[float] = mapped_column(default=0.0)
    total_amount: Mapped[float] = mapped_column()
    amount_paid: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Status
    status: Mapped[PackageBookingStatus] = mapped_column(default=PackageBookingStatus.PENDING)
    
    # Payment tracking
    payment_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Special requests
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Audit
    booked_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    package: Mapped["HolidayPackage"] = relationship("HolidayPackage", back_populates="bookings")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    enquiry: Mapped[Optional["PackageEnquiry"]] = relationship("PackageEnquiry")
    booked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[booked_by_id])
    
    @property
    def balance_due(self) -> float:
        """Calculate remaining balance."""
        return max(0, self.total_amount - self.amount_paid)
    
    def __repr__(self):
        return f"<PackageBooking(ref={self.booking_ref}, status={self.status})>"


# Indexes for better query performance
Index('ix_holiday_packages_theme_destination', HolidayPackage.theme_id, HolidayPackage.destination_id)
Index('ix_holiday_packages_featured', HolidayPackage.is_featured, HolidayPackage.is_active)
Index('ix_package_enquiries_status', PackageEnquiry.status)
Index('ix_package_bookings_status', PackageBooking.status)
