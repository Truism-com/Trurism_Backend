"""
Customer Dashboard Database Models

SQLAlchemy models for B2C customer dashboard features.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Date, Enum, Index, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List
import enum

from app.core.database import Base


class SocialProvider(str, enum.Enum):
    """Social login providers."""
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class AmendmentType(str, enum.Enum):
    """Amendment request types."""
    CANCELLATION = "cancellation"
    DATE_CHANGE = "date_change"
    NAME_CHANGE = "name_change"
    SEAT_CHANGE = "seat_change"
    MEAL_CHANGE = "meal_change"
    UPGRADE = "upgrade"
    OTHER = "other"


class AmendmentStatus(str, enum.Enum):
    """Amendment request status."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REFUND_INITIATED = "refund_initiated"
    REFUND_COMPLETED = "refund_completed"


class QueryType(str, enum.Enum):
    """User query types."""
    HOLIDAY_ENQUIRY = "holiday_enquiry"
    VISA_ENQUIRY = "visa_enquiry"
    ACTIVITY_ENQUIRY = "activity_enquiry"
    TRANSFER_ENQUIRY = "transfer_enquiry"
    GENERAL = "general"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"


class QueryStatus(str, enum.Enum):
    """User query status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_RESPONSE = "awaiting_response"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ActivityType(str, enum.Enum):
    """User activity types."""
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    PAYMENT_MADE = "payment_made"
    REFUND_RECEIVED = "refund_received"
    AMENDMENT_REQUESTED = "amendment_requested"
    QUERY_SUBMITTED = "query_submitted"
    DOCUMENT_UPLOADED = "document_uploaded"
    TICKET_DOWNLOADED = "ticket_downloaded"


class SocialAccount(Base):
    """
    Social login accounts linked to users.
    """
    __tablename__ = "social_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # User link
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Social provider info
    provider: Mapped[SocialProvider] = mapped_column(
        Enum(SocialProvider),
        nullable=False
    )
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Token storage (encrypted in production)
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Profile data from provider
    profile_data: Mapped[Optional[str]] = mapped_column(JSON)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    linked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="social_accounts")
    
    __table_args__ = (
        Index('idx_social_user', 'user_id'),
        Index('idx_social_provider', 'provider', 'provider_user_id', unique=True),
    )


class AmendmentRequest(Base):
    """
    Amendment/cancellation requests from customers.
    """
    __tablename__ = "amendment_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Request number
    request_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Booking reference
    booking_id: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_type: Mapped[str] = mapped_column(String(50), nullable=False)  # flight, hotel, etc.
    booking_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request details
    amendment_type: Mapped[AmendmentType] = mapped_column(
        Enum(AmendmentType),
        nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(Text)
    requested_changes: Mapped[Optional[str]] = mapped_column(JSON)  # Details of what to change
    
    # Supporting documents
    documents: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Status
    status: Mapped[AmendmentStatus] = mapped_column(
        Enum(AmendmentStatus),
        default=AmendmentStatus.PENDING
    )
    
    # Charges
    amendment_fee: Mapped[float] = mapped_column(Float, default=0)
    supplier_penalty: Mapped[float] = mapped_column(Float, default=0)
    refund_amount: Mapped[Optional[float]] = mapped_column(Float)
    
    # Processing
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    admin_remarks: Mapped[Optional[str]] = mapped_column(Text)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_amendment_booking', 'booking_id'),
        Index('idx_amendment_user', 'user_id'),
        Index('idx_amendment_status', 'status'),
    )


class UserQuery(Base):
    """
    User queries and support tickets.
    """
    __tablename__ = "user_queries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Ticket number
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Query details
    query_type: Mapped[QueryType] = mapped_column(
        Enum(QueryType),
        nullable=False
    )
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Related reference (optional)
    related_booking_id: Mapped[Optional[int]] = mapped_column(Integer)
    related_enquiry_id: Mapped[Optional[int]] = mapped_column(Integer)
    related_application_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Attachments
    attachments: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Status
    status: Mapped[QueryStatus] = mapped_column(
        Enum(QueryStatus),
        default=QueryStatus.OPEN
    )
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent
    
    # Processing
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Resolution
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    responses: Mapped[List["QueryResponse"]] = relationship("QueryResponse", back_populates="query")
    
    __table_args__ = (
        Index('idx_query_user', 'user_id'),
        Index('idx_query_status', 'status'),
        Index('idx_query_type', 'query_type'),
    )


class QueryResponse(Base):
    """
    Responses to user queries.
    """
    __tablename__ = "query_responses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    query_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_queries.id", ondelete="CASCADE"), nullable=False)
    
    # Responder
    responder_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_staff_response: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Response
    message: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Internal note (only visible to staff)
    is_internal_note: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    query: Mapped["UserQuery"] = relationship("UserQuery", back_populates="responses")
    responder: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index('idx_response_query', 'query_id'),
    )


class ActivityLog(Base):
    """
    User activity/audit log.
    """
    __tablename__ = "activity_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Activity
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Related entity
    entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Extra data
    extra_data: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Request info
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    device_info: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_activity_user', 'user_id'),
        Index('idx_activity_type', 'activity_type'),
        Index('idx_activity_date', 'created_at'),
    )


# Import for type hints
from app.auth.models import User
