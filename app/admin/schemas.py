"""
Admin Module Schemas

This module defines Pydantic schemas for administrative operations:
- User management schemas
- Agent approval schemas
- Booking management schemas
- Dashboard and analytics schemas
- System configuration schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.auth.models import UserRole, AgentApprovalStatus
from app.booking.models import BookingStatus, PaymentStatus


class UserManagementResponse(BaseModel):
    """
    Schema for user management operations.
    
    Provides user information for administrative oversight
    including status, role, and activity details.
    """
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Account verification status")
    approval_status: Optional[AgentApprovalStatus] = Field(None, description="Agent approval status")
    company_name: Optional[str] = Field(None, description="Company name for agents")
    pan_number: Optional[str] = Field(None, description="PAN number for agents")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    total_bookings: int = Field(0, description="Total number of bookings made")
    
    model_config = ConfigDict(from_attributes=True)


class AgentApprovalRequest(BaseModel):
    """
    Schema for agent approval requests.
    
    Used by admins to approve or reject agent applications
    with optional rejection reasons.
    """
    approval_status: AgentApprovalStatus = Field(..., description="Approval decision")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Admin notes")


class UserStatusUpdateRequest(BaseModel):
    """
    Schema for updating user account status.
    
    Allows admins to activate/deactivate user accounts
    and manage account verification status.
    """
    is_active: Optional[bool] = Field(None, description="Account active status")
    is_verified: Optional[bool] = Field(None, description="Account verification status")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change")


class BookingManagementResponse(BaseModel):
    """
    Schema for booking management operations.
    
    Provides comprehensive booking information for
    administrative oversight and management.
    """
    booking_id: int = Field(..., description="Unique booking ID")
    booking_reference: str = Field(..., description="Booking reference number")
    type: str = Field(..., description="Booking type (flight, hotel, bus)")
    user_email: str = Field(..., description="User email who made the booking")
    user_name: str = Field(..., description="User name who made the booking")
    status: BookingStatus = Field(..., description="Current booking status")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    total_amount: float = Field(..., ge=0, description="Total booking amount")
    currency: str = Field(..., description="Currency code")
    created_at: datetime = Field(..., description="Booking creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    details: Dict[str, Any] = Field(..., description="Booking-specific details")
    
    model_config = ConfigDict(from_attributes=True)


class BookingStatusUpdateRequest(BaseModel):
    """
    Schema for updating booking status.
    
    Allows admins to update booking status and
    manage booking lifecycle.
    """
    status: BookingStatus = Field(..., description="New booking status")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for status change")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Admin notes")


class DashboardStatsResponse(BaseModel):
    """
    Schema for dashboard statistics.
    
    Provides key metrics and statistics for
    administrative dashboard display.
    """
    # User Statistics
    total_users: int = Field(..., ge=0, description="Total number of users")
    active_users: int = Field(..., ge=0, description="Number of active users")
    pending_agents: int = Field(..., ge=0, description="Number of pending agent approvals")
    approved_agents: int = Field(..., ge=0, description="Number of approved agents")
    
    # Booking Statistics
    total_bookings: int = Field(..., ge=0, description="Total number of bookings")
    confirmed_bookings: int = Field(..., ge=0, description="Number of confirmed bookings")
    cancelled_bookings: int = Field(..., ge=0, description="Number of cancelled bookings")
    pending_bookings: int = Field(..., ge=0, description="Number of pending bookings")
    
    # Revenue Statistics
    total_revenue: float = Field(..., ge=0, description="Total revenue generated")
    revenue_today: float = Field(..., ge=0, description="Revenue generated today")
    revenue_this_month: float = Field(..., ge=0, description="Revenue generated this month")
    average_booking_value: float = Field(..., ge=0, description="Average booking value")
    
    # Recent Activity
    bookings_today: int = Field(..., ge=0, description="Bookings created today")
    cancellations_today: int = Field(..., ge=0, description="Cancellations today")
    new_users_today: int = Field(..., ge=0, description="New user registrations today")
    agent_applications_today: int = Field(..., ge=0, description="New agent applications today")
    
    # Performance Metrics
    booking_success_rate: float = Field(..., ge=0, le=100, description="Booking success rate percentage")
    cancellation_rate: float = Field(..., ge=0, le=100, description="Booking cancellation rate percentage")
    payment_success_rate: float = Field(..., ge=0, le=100, description="Payment success rate percentage")


class BookingAnalyticsRequest(BaseModel):
    """
    Schema for booking analytics requests.
    
    Allows filtering analytics data by date range,
    booking type, and other criteria.
    """
    start_date: Optional[date] = Field(None, description="Start date for analytics")
    end_date: Optional[date] = Field(None, description="End date for analytics")
    booking_type: Optional[str] = Field(None, description="Filter by booking type")
    status: Optional[BookingStatus] = Field(None, description="Filter by booking status")
    payment_status: Optional[PaymentStatus] = Field(None, description="Filter by payment status")
    group_by: Optional[str] = Field("day", description="Group results by (day, week, month)")


class BookingAnalyticsResponse(BaseModel):
    """
    Schema for booking analytics responses.
    
    Provides analytics data grouped by specified
    criteria with counts and revenue information.
    """
    period: str = Field(..., description="Analytics period")
    total_bookings: int = Field(..., ge=0, description="Total bookings in period")
    total_revenue: float = Field(..., ge=0, description="Total revenue in period")
    average_booking_value: float = Field(..., ge=0, description="Average booking value")
    data_points: List[Dict[str, Any]] = Field(..., description="Detailed analytics data")
    
    model_config = ConfigDict(
        json_encoders={
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    )


class SystemHealthResponse(BaseModel):
    """
    Schema for system health check responses.
    
    Provides information about system components
    and their operational status.
    """
    database_status: str = Field(..., description="Database connection status")
    redis_status: str = Field(..., description="Redis cache status")
    external_apis_status: Dict[str, str] = Field(..., description="External API status")
    overall_status: str = Field(..., description="Overall system status")
    response_time: float = Field(..., description="Health check response time in seconds")
    timestamp: datetime = Field(..., description="Health check timestamp")


class AdminActionLog(BaseModel):
    """
    Schema for admin action logging.
    
    Tracks administrative actions for audit
    and compliance purposes.
    """
    id: int = Field(..., description="Log entry ID")
    admin_id: int = Field(..., description="Admin user ID")
    admin_email: str = Field(..., description="Admin email")
    action: str = Field(..., description="Action performed")
    target_type: str = Field(..., description="Type of target (user, booking, etc.)")
    target_id: int = Field(..., description="Target ID")
    details: Dict[str, Any] = Field(..., description="Action details")
    timestamp: datetime = Field(..., description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="Admin IP address")
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """
    Generic paginated response schema.
    
    Provides consistent pagination structure
    for list endpoints.
    """
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=1, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
    items: List[Dict[str, Any]] = Field(..., description="List of items")


class UserListResponse(PaginatedResponse):
    """Paginated response for user lists."""
    items: List[UserManagementResponse] = Field(..., description="List of users")


class BookingListResponse(PaginatedResponse):
    """Paginated response for booking lists."""
    items: List[BookingManagementResponse] = Field(..., description="List of bookings")
