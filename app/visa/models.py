"""
Visa Database Models

SQLAlchemy models for visa country, types, requirements, and applications.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Date, Enum, Index, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from typing import Optional, List
import enum

from app.core.database import Base


class ApplicationStatus(str, enum.Enum):
    """Visa application status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DOCUMENTS_PENDING = "documents_pending"
    UNDER_REVIEW = "under_review"
    ADDITIONAL_DOCS_REQUIRED = "additional_docs_required"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class VisaCountry(Base):
    """
    Countries for which visa services are offered.
    """
    __tablename__ = "visa_countries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Country info
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    code: Mapped[Optional[str]] = mapped_column(String(3))  # ISO 3166-1 alpha-2/3
    
    # Display
    flag_url: Mapped[Optional[str]] = mapped_column(String(500))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing info
    embassy_details: Mapped[Optional[str]] = mapped_column(Text)  # Address, contact info
    general_requirements: Mapped[Optional[str]] = mapped_column(Text)  # General info for all visas
    
    # Status
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    visa_types: Mapped[List["VisaType"]] = relationship("VisaType", back_populates="country", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_visa_country_slug', 'slug'),
        Index('idx_visa_country_active', 'is_active'),
    )


class VisaType(Base):
    """
    Types of visas available for each country.
    E.g., Tourist, Business, Student, Transit, etc.
    """
    __tablename__ = "visa_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country_id: Mapped[int] = mapped_column(Integer, ForeignKey("visa_countries.id"), nullable=False)
    
    # Type info
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Tourist Visa"
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20))  # Internal code
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "30 days", "90 days"
    validity: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "3 months from issue"
    entry_type: Mapped[Optional[str]] = mapped_column(String(50))  # Single, Multiple, Transit
    
    # Processing
    processing_time: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "5-7 business days"
    min_processing_days: Mapped[Optional[int]] = mapped_column(Integer)
    max_processing_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Pricing
    base_price: Mapped[float] = mapped_column(Float, default=0)  # Our service fee
    government_fee: Mapped[float] = mapped_column(Float, default=0)  # Embassy/Govt fee
    vfs_fee: Mapped[float] = mapped_column(Float, default=0)  # VFS/Processing center fee
    total_price: Mapped[float] = mapped_column(Float, default=0)  # Total to customer
    
    # Status
    is_express_available: Mapped[bool] = mapped_column(Boolean, default=False)
    express_price: Mapped[Optional[float]] = mapped_column(Float)  # Additional express fee
    express_processing_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    country: Mapped["VisaCountry"] = relationship("VisaCountry", back_populates="visa_types")
    requirements: Mapped[List["VisaRequirement"]] = relationship("VisaRequirement", back_populates="visa_type", cascade="all, delete-orphan")
    applications: Mapped[List["VisaApplication"]] = relationship("VisaApplication", back_populates="visa_type")
    
    __table_args__ = (
        Index('idx_visa_type_country', 'country_id'),
        Index('idx_visa_type_slug', 'slug'),
    )


class VisaRequirement(Base):
    """
    Document and other requirements for each visa type.
    """
    __tablename__ = "visa_requirements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visa_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("visa_types.id"), nullable=False)
    
    # Requirement details
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # documents, personal, financial
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Flags
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    applies_to: Mapped[Optional[str]] = mapped_column(String(50))  # all, employed, self_employed, student, etc.
    
    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    visa_type: Mapped["VisaType"] = relationship("VisaType", back_populates="requirements")
    
    __table_args__ = (
        Index('idx_visa_req_type', 'visa_type_id'),
    )


class VisaApplication(Base):
    """
    Customer visa applications.
    """
    __tablename__ = "visa_applications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Reference
    application_ref: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    
    # Visa info
    visa_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("visa_types.id"), nullable=False)
    
    # Applicant info
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Personal details
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Passport details
    passport_number: Mapped[Optional[str]] = mapped_column(String(50))
    passport_expiry: Mapped[Optional[date]] = mapped_column(Date)
    nationality: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    
    # Travel details
    travel_date: Mapped[Optional[date]] = mapped_column(Date)
    return_date: Mapped[Optional[date]] = mapped_column(Date)
    purpose_of_visit: Mapped[Optional[str]] = mapped_column(Text)
    
    # Documents (JSON list of uploaded document URLs/info)
    documents: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Application status
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.DRAFT
    )
    status_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing
    is_express: Mapped[bool] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Pricing
    base_amount: Mapped[float] = mapped_column(Float, default=0)
    express_fee: Mapped[float] = mapped_column(Float, default=0)
    taxes: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    
    # Payment
    payment_status: Mapped[Optional[str]] = mapped_column(String(20))  # pending, partial, paid
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Result
    visa_number: Mapped[Optional[str]] = mapped_column(String(100))  # Assigned visa number
    visa_issue_date: Mapped[Optional[date]] = mapped_column(Date)
    visa_expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Internal notes
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    visa_type: Mapped["VisaType"] = relationship("VisaType", back_populates="applications")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])
    
    __table_args__ = (
        Index('idx_visa_app_ref', 'application_ref'),
        Index('idx_visa_app_status', 'status'),
        Index('idx_visa_app_user', 'user_id'),
        Index('idx_visa_app_type', 'visa_type_id'),
    )


# Import User for relationship typing
from app.auth.models import User
