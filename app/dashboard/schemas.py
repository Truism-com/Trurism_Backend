"""
Customer Dashboard Pydantic Schemas

Schemas for B2C customer dashboard validation.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime, date

from app.dashboard.models import (
    SocialProvider, AmendmentType, AmendmentStatus,
    QueryType, QueryStatus, ActivityType
)


# =============================================================================
# PROFILE SCHEMAS
# =============================================================================

class UserProfileBase(BaseModel):
    """Base user profile schema."""
    name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    nationality: Optional[str] = Field(None, max_length=100)
    passport_number: Optional[str] = Field(None, max_length=50)
    passport_expiry: Optional[date] = None


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile."""
    pass


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    email_verified: bool = False
    phone_verified: bool = False
    profile_picture_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if info.data.get('new_password') and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


# =============================================================================
# SOCIAL LOGIN SCHEMAS
# =============================================================================

class SocialLoginRequest(BaseModel):
    """Social login request."""
    provider: SocialProvider
    access_token: str
    id_token: Optional[str] = None  # For Google


class SocialAccountResponse(BaseModel):
    """Social account response."""
    id: int
    provider: SocialProvider
    provider_email: Optional[str] = None
    profile_picture_url: Optional[str] = None
    linked_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class LinkedAccountsResponse(BaseModel):
    """User's linked social accounts."""
    accounts: List[SocialAccountResponse]


# =============================================================================
# BOOKING SCHEMAS (for dashboard view)
# =============================================================================

class BookingSummary(BaseModel):
    """Booking summary for dashboard."""
    id: int
    booking_reference: str
    booking_type: str  # flight, hotel, package, activity, transfer
    status: str
    travel_date: Optional[date] = None
    traveller_names: List[str] = []
    total_amount: float
    paid_amount: float
    created_at: datetime
    
    # Type-specific summary
    summary: str  # e.g., "DEL → BOM, 2 Adults"
    
    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """List of user bookings."""
    items: List[BookingSummary]
    total: int
    upcoming_count: int
    completed_count: int
    cancelled_count: int


class BookingDetailResponse(BaseModel):
    """Detailed booking response."""
    id: int
    booking_reference: str
    booking_type: str
    status: str
    payment_status: str
    
    # Travel details
    travel_date: Optional[date] = None
    return_date: Optional[date] = None
    
    # Travellers
    travellers: List[Dict[str, Any]] = []
    
    # Pricing
    base_amount: float
    tax_amount: float
    discount_amount: float
    convenience_fee: float
    total_amount: float
    paid_amount: float
    balance_due: float
    
    # Booking-specific details
    details: Dict[str, Any] = {}
    
    # Documents
    ticket_url: Optional[str] = None
    invoice_url: Optional[str] = None
    voucher_url: Optional[str] = None
    
    # Actions
    can_cancel: bool = False
    can_modify: bool = False
    cancellation_policy: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# AMENDMENT SCHEMAS
# =============================================================================

class AmendmentRequestCreate(BaseModel):
    """Schema for creating an amendment request."""
    booking_id: int
    amendment_type: AmendmentType
    reason: str = Field(..., min_length=10, max_length=2000)
    requested_changes: Optional[Dict[str, Any]] = None
    documents: Optional[List[str]] = None  # URLs of uploaded documents


class AmendmentRequestResponse(BaseModel):
    """Amendment request response."""
    id: int
    request_number: str
    booking_id: int
    booking_type: str
    booking_reference: str
    amendment_type: AmendmentType
    reason: Optional[str] = None
    requested_changes: Optional[Dict[str, Any]] = None
    documents: Optional[List[str]] = None
    status: AmendmentStatus
    amendment_fee: float
    supplier_penalty: float
    refund_amount: Optional[float] = None
    admin_remarks: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AmendmentListResponse(BaseModel):
    """List of amendment requests."""
    items: List[AmendmentRequestResponse]
    total: int


class AmendmentStatusUpdate(BaseModel):
    """Admin schema for updating amendment status."""
    status: AmendmentStatus
    amendment_fee: Optional[float] = Field(None, ge=0)
    supplier_penalty: Optional[float] = Field(None, ge=0)
    refund_amount: Optional[float] = Field(None, ge=0)
    admin_remarks: Optional[str] = None


# =============================================================================
# USER QUERY SCHEMAS
# =============================================================================

class UserQueryCreate(BaseModel):
    """Schema for creating a user query."""
    query_type: QueryType
    subject: str = Field(..., min_length=5, max_length=300)
    message: str = Field(..., min_length=20, max_length=5000)
    related_booking_id: Optional[int] = None
    related_enquiry_id: Optional[int] = None
    related_application_id: Optional[int] = None
    attachments: Optional[List[str]] = None
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")


class QueryResponseCreate(BaseModel):
    """Schema for creating a query response."""
    message: str = Field(..., min_length=1, max_length=5000)
    attachments: Optional[List[str]] = None


class QueryResponseItem(BaseModel):
    """Query response item."""
    id: int
    responder_id: int
    responder_name: Optional[str] = None
    is_staff_response: bool
    message: str
    attachments: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserQueryResponse(BaseModel):
    """User query response."""
    id: int
    ticket_number: str
    query_type: QueryType
    subject: str
    message: str
    related_booking_id: Optional[int] = None
    related_enquiry_id: Optional[int] = None
    related_application_id: Optional[int] = None
    attachments: Optional[List[str]] = None
    status: QueryStatus
    priority: str
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    responses: List[QueryResponseItem] = []
    
    class Config:
        from_attributes = True


class UserQueryListResponse(BaseModel):
    """List of user queries."""
    items: List[UserQueryResponse]
    total: int
    open_count: int
    resolved_count: int


class QueryStatusUpdate(BaseModel):
    """Admin schema for updating query status."""
    status: QueryStatus
    resolution: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")


# =============================================================================
# ACTIVITY LOG SCHEMAS
# =============================================================================

class ActivityLogResponse(BaseModel):
    """Activity log entry response."""
    id: int
    activity_type: ActivityType
    description: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityLogListResponse(BaseModel):
    """List of activity logs."""
    items: List[ActivityLogResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# DASHBOARD SUMMARY SCHEMAS
# =============================================================================

class DashboardStats(BaseModel):
    """User dashboard statistics."""
    total_bookings: int
    upcoming_trips: int
    pending_payments: float
    pending_amendments: int
    open_queries: int
    wallet_balance: float


class DashboardSummary(BaseModel):
    """User dashboard summary."""
    stats: DashboardStats
    upcoming_bookings: List[BookingSummary]
    recent_activity: List[ActivityLogResponse]
    pending_queries: List[UserQueryResponse]
