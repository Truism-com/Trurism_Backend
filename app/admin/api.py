"""
Admin API Endpoints

This module defines FastAPI endpoints for administrative operations:
- User and agent management
- Booking oversight and management
- System analytics and reporting
- Agent approval workflow
- Dashboard metrics and statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.core.database import get_database_session
from app.auth.api import get_current_admin_user
from app.auth.models import User, UserRole, AgentApprovalStatus
from app.booking.models import BookingStatus, PaymentStatus
from app.admin.schemas import (
    UserManagementResponse, AgentApprovalRequest, UserStatusUpdateRequest,
    BookingManagementResponse, BookingStatusUpdateRequest, DashboardStatsResponse,
    BookingAnalyticsRequest, BookingAnalyticsResponse, UserListResponse,
    BookingListResponse
)
from app.admin.services import AdminUserService, AdminBookingService, AdminAnalyticsService

# Router for admin endpoints
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get dashboard statistics and metrics.
    
    This endpoint provides key metrics and statistics for the
    administrative dashboard including user counts, booking statistics,
    revenue information, and performance metrics.
    
    Args:
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        DashboardStatsResponse: Dashboard statistics and metrics
    """
    try:
        analytics_service = AdminAnalyticsService(db)
        stats = await analytics_service.get_dashboard_stats()
        return DashboardStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard statistics: {str(e)}"
        )


@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of users per page"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    approval_status: Optional[AgentApprovalStatus] = Query(None, description="Filter by approval status"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all users with filtering and pagination.
    
    This endpoint returns a paginated list of all users in the system
    with optional filtering by role, status, and approval status.
    
    Args:
        page: Page number for pagination
        size: Number of users per page
        role: Optional filter by user role
        is_active: Optional filter by active status
        approval_status: Optional filter by agent approval status
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        UserListResponse: Paginated list of users
    """
    try:
        skip = (page - 1) * size
        
        user_service = AdminUserService(db)
        users, total_count = await user_service.get_all_users(
            skip=skip,
            limit=size,
            role_filter=role,
            status_filter=is_active,
            approval_status_filter=approval_status
        )
        
        # Convert to response format
        user_responses = []
        for user in users:
            booking_count = await user_service.get_user_booking_count(user.id)
            user_responses.append(UserManagementResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                approval_status=user.approval_status,
                company_name=user.company_name,
                pan_number=user.pan_number,
                created_at=user.created_at,
                last_login=user.last_login,
                total_bookings=booking_count
            ))
        
        total_pages = (total_count + size - 1) // size
        
        return UserListResponse(
            total=total_count,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            items=user_responses
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserManagementResponse)
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get detailed information for a specific user.
    
    This endpoint returns comprehensive user information including
    booking history and account details for administrative review.
    
    Args:
        user_id: User ID to retrieve
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        UserManagementResponse: Detailed user information
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = AdminUserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        booking_count = await user_service.get_user_booking_count(user.id)
        
        return UserManagementResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            approval_status=user.approval_status,
            company_name=user.company_name,
            pan_number=user.pan_number,
            created_at=user.created_at,
            last_login=user.last_login,
            total_bookings=booking_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user details: {str(e)}"
        )


@router.put("/agents/{agent_id}/approve")
async def approve_agent(
    agent_id: int,
    approval_request: AgentApprovalRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Approve or reject an agent application.
    
    This endpoint allows admins to approve or reject agent applications
    with optional rejection reasons and admin notes.
    
    Args:
        agent_id: Agent user ID
        approval_request: Approval decision and details
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dict: Approval confirmation message
        
    Raises:
        HTTPException: If agent not found or not an agent
    """
    try:
        user_service = AdminUserService(db)
        updated_agent = await user_service.approve_agent(
            agent_id, approval_request, current_admin
        )
        
        status_text = "approved" if approval_request.approval_status == AgentApprovalStatus.APPROVED else "rejected"
        
        return {
            "message": f"Agent application {status_text} successfully",
            "agent_id": agent_id,
            "approval_status": updated_agent.approval_status,
            "agent_email": updated_agent.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process agent approval: {str(e)}"
        )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_request: UserStatusUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update user account status.
    
    This endpoint allows admins to activate/deactivate user accounts
    and manage account verification status.
    
    Args:
        user_id: User ID to update
        status_request: Status update details
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dict: Status update confirmation message
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_service = AdminUserService(db)
        updated_user = await user_service.update_user_status(
            user_id, status_request, current_admin
        )
        
        return {
            "message": "User status updated successfully",
            "user_id": user_id,
            "user_email": updated_user.email,
            "is_active": updated_user.is_active,
            "is_verified": updated_user.is_verified
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}"
        )


@router.get("/bookings", response_model=BookingListResponse)
async def get_all_bookings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of bookings per page"),
    booking_type: Optional[str] = Query(None, description="Filter by booking type"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all bookings with filtering and pagination.
    
    This endpoint returns a paginated list of all bookings in the system
    with optional filtering by type, status, payment status, and date range.
    
    Args:
        page: Page number for pagination
        size: Number of bookings per page
        booking_type: Optional filter by booking type (flight, hotel, bus)
        status: Optional filter by booking status
        payment_status: Optional filter by payment status
        date_from: Optional filter from date
        date_to: Optional filter to date
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        BookingListResponse: Paginated list of bookings
    """
    try:
        skip = (page - 1) * size
        
        # Parse dates
        from datetime import datetime
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        booking_service = AdminBookingService(db)
        bookings, total_count = await booking_service.get_all_bookings(
            skip=skip,
            limit=size,
            booking_type_filter=booking_type,
            status_filter=status,
            payment_status_filter=payment_status,
            date_from=date_from_obj,
            date_to=date_to_obj
        )
        
        # Convert to response format
        booking_responses = [
            BookingManagementResponse(**booking) for booking in bookings
        ]
        
        total_pages = (total_count + size - 1) // size
        
        return BookingListResponse(
            total=total_count,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            items=booking_responses
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bookings: {str(e)}"
        )


@router.put("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    status_request: BookingStatusUpdateRequest,
    booking_type: str = Query(..., description="Booking type (flight, hotel, bus)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update booking status.
    
    This endpoint allows admins to update booking status and
    manage booking lifecycle with optional admin notes.
    
    Args:
        booking_id: Booking ID to update
        booking_type: Type of booking (flight, hotel, bus)
        status_request: Status update details
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dict: Status update confirmation message
        
    Raises:
        HTTPException: If booking not found
    """
    try:
        booking_service = AdminBookingService(db)
        success = await booking_service.update_booking_status(
            booking_id, booking_type, status_request, current_admin
        )
        
        if success:
            return {
                "message": "Booking status updated successfully",
                "booking_id": booking_id,
                "booking_type": booking_type,
                "new_status": status_request.status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update booking status"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update booking status: {str(e)}"
        )


@router.get("/analytics/bookings", response_model=BookingAnalyticsResponse)
async def get_booking_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    booking_type: Optional[str] = Query(None, description="Filter by booking type"),
    status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    group_by: str = Query("day", description="Group results by (day, week, month)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get booking analytics for specified period and filters.
    
    This endpoint provides analytics data for bookings including
    time-series data, revenue trends, and booking patterns.
    
    Args:
        start_date: Optional start date for analytics
        end_date: Optional end date for analytics
        booking_type: Optional filter by booking type
        status: Optional filter by booking status
        payment_status: Optional filter by payment status
        group_by: Group results by time period
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        BookingAnalyticsResponse: Analytics data
    """
    try:
        # Parse dates
        from datetime import datetime, date
        
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        analytics_request = BookingAnalyticsRequest(
            start_date=start_date_obj,
            end_date=end_date_obj,
            booking_type=booking_type,
            status=status,
            payment_status=payment_status,
            group_by=group_by
        )
        
        analytics_service = AdminAnalyticsService(db)
        analytics_data = await analytics_service.get_booking_analytics(analytics_request)
        
        return BookingAnalyticsResponse(**analytics_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve booking analytics: {str(e)}"
        )


@router.get("/health")
async def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get system health status.
    
    This endpoint provides information about system components
    and their operational status for monitoring purposes.
    
    Args:
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dict: System health status
    """
    try:
        from app.core.database import check_database_health
        import redis
        from app.core.config import settings
        
        # Check database health
        db_healthy = await check_database_health()
        
        # Check Redis health
        redis_healthy = False
        try:
            if settings.redis_url and settings.redis_url.lower() != "none":
                redis_client = redis.from_url(settings.redis_url, decode_responses=True)
                redis_client.ping()
                redis_healthy = True
        except Exception:
            pass
        
        # Overall status
        overall_status = "healthy" if db_healthy and redis_healthy else "unhealthy"
        
        return {
            "database_status": "healthy" if db_healthy else "unhealthy",
            "redis_status": "healthy" if redis_healthy else "unhealthy",
            "external_apis_status": {
                "xml_agency": "not_configured"  # TODO: Check actual API status
            },
            "overall_status": overall_status,
            "response_time": 0.1,  # TODO: Calculate actual response time
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check system health: {str(e)}"
        )
