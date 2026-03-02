"""
Customer Dashboard API Endpoints

B2C customer-facing API for profile, bookings, amendments, queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.dashboard.services import DashboardService
from app.dashboard.models import (
    SocialProvider, AmendmentType, AmendmentStatus,
    QueryType, QueryStatus, ActivityType
)
from app.dashboard.schemas import (
    UserProfileResponse, UserProfileUpdate, PasswordChangeRequest,
    SocialLoginRequest, SocialAccountResponse, LinkedAccountsResponse,
    BookingListResponse, BookingSummary, BookingDetailResponse,
    AmendmentRequestCreate, AmendmentRequestResponse, AmendmentListResponse, AmendmentStatusUpdate,
    UserQueryCreate, UserQueryResponse, UserQueryListResponse, QueryResponseCreate, QueryStatusUpdate,
    ActivityLogResponse, ActivityLogListResponse,
    DashboardSummary, DashboardStats
)

router = APIRouter(prefix="/dashboard", tags=["Customer Dashboard"])


# =============================================================================
# PROFILE MANAGEMENT
# =============================================================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name if hasattr(current_user, 'full_name') else None,
        phone=current_user.phone if hasattr(current_user, 'phone') else None,
        email_verified=current_user.is_verified if hasattr(current_user, 'is_verified') else False,
        created_at=current_user.created_at
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    if data.name:
        current_user.full_name = data.name
    if data.phone:
        current_user.phone = data.phone
    # Add other fields as needed
    
    await db.commit()
    await db.refresh(current_user)
    
    # Log activity
    service = DashboardService(db)
    await service.log_activity(
        user_id=current_user.id,
        activity_type=ActivityType.PROFILE_UPDATED,
        description="Profile updated"
    )
    
    return await get_user_profile(current_user)


@router.post("/profile/change-password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    from app.core.security import verify_password, hash_password
    
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.hashed_password = hash_password(data.new_password)
    await db.commit()
    
    # Log activity
    service = DashboardService(db)
    await service.log_activity(
        user_id=current_user.id,
        activity_type=ActivityType.PASSWORD_CHANGED,
        description="Password changed"
    )
    
    return {"message": "Password changed successfully"}


# =============================================================================
# SOCIAL LOGIN MANAGEMENT
# =============================================================================

@router.get("/social-accounts", response_model=LinkedAccountsResponse)
async def get_linked_social_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's linked social accounts."""
    service = DashboardService(db)
    accounts = await service.get_linked_accounts(current_user.id)
    return LinkedAccountsResponse(accounts=accounts)


@router.post("/social-accounts/link", response_model=SocialAccountResponse)
async def link_social_account(
    data: SocialLoginRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Link a social account to user."""
    # In production, verify the token with the provider
    # This is a simplified version
    
    service = DashboardService(db)
    
    # Mock provider verification - in production, call provider APIs
    provider_user_id = f"{data.provider.value}_{current_user.id}"  # Placeholder
    provider_email = current_user.email
    
    account = await service.link_social_account(
        user_id=current_user.id,
        provider=data.provider,
        provider_user_id=provider_user_id,
        provider_email=provider_email,
        access_token=data.access_token
    )
    
    return account


@router.delete("/social-accounts/{provider}")
async def unlink_social_account(
    provider: SocialProvider = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlink a social account."""
    service = DashboardService(db)
    success = await service.unlink_social_account(current_user.id, provider)
    
    if not success:
        raise HTTPException(status_code=404, detail="Social account not found")
    
    return {"message": f"{provider.value} account unlinked successfully"}


# =============================================================================
# BOOKINGS MANAGEMENT
# =============================================================================

@router.get("/bookings", response_model=BookingListResponse)
async def get_user_bookings(
    booking_type: Optional[str] = Query(None, description="Filter by booking type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's booking history."""
    service = DashboardService(db)
    bookings, total, counts = await service.get_user_bookings(
        user_id=current_user.id,
        booking_type=booking_type,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return BookingListResponse(
        items=[BookingSummary(**b) for b in bookings],
        total=total,
        upcoming_count=counts.get('upcoming', 0),
        completed_count=counts.get('completed', 0),
        cancelled_count=counts.get('cancelled', 0)
    )


@router.get("/bookings/{booking_type}/{booking_id}", response_model=BookingDetailResponse)
async def get_booking_detail(
    booking_type: str = Path(..., description="Type of booking (flight, hotel, etc.)"),
    booking_id: int = Path(..., description="Booking ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed booking information."""
    service = DashboardService(db)
    booking = await service.get_booking_detail(
        user_id=current_user.id,
        booking_id=booking_id,
        booking_type=booking_type
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return booking


@router.get("/bookings/{booking_type}/{booking_id}/ticket")
async def download_booking_ticket(
    booking_type: str = Path(...),
    booking_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get booking ticket PDF URL."""
    service = DashboardService(db)
    booking = await service.get_booking_detail(
        user_id=current_user.id,
        booking_id=booking_id,
        booking_type=booking_type
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # In production, generate or retrieve the PDF URL
    return {
        "ticket_url": f"/api/v1/documents/tickets/{booking_type}/{booking_id}/ticket.pdf",
        "invoice_url": f"/api/v1/documents/invoices/{booking_type}/{booking_id}/invoice.pdf"
    }


# =============================================================================
# AMENDMENT REQUESTS
# =============================================================================

@router.post("/amendments", response_model=AmendmentRequestResponse)
async def create_amendment_request(
    data: AmendmentRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an amendment/cancellation request."""
    service = DashboardService(db)
    
    # Verify user owns the booking
    booking = await service.get_booking_detail(
        user_id=current_user.id,
        booking_id=data.booking_id,
        booking_type=data.booking_type
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if not booking.get('can_cancel') and data.amendment_type == AmendmentType.CANCELLATION:
        raise HTTPException(status_code=400, detail="This booking cannot be cancelled")
    
    if not booking.get('can_modify') and data.amendment_type != AmendmentType.CANCELLATION:
        raise HTTPException(status_code=400, detail="This booking cannot be modified")
    
    amendment = await service.create_amendment_request(
        user_id=current_user.id,
        booking_id=data.booking_id,
        booking_type=data.booking_type,
        amendment_type=data.amendment_type.value,
        reason=data.reason,
        requested_changes=data.requested_changes,
        documents=data.documents
    )
    
    return amendment


@router.get("/amendments", response_model=AmendmentListResponse)
async def get_user_amendments(
    status: Optional[AmendmentStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's amendment requests."""
    service = DashboardService(db)
    amendments, total = await service.get_user_amendments(
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return AmendmentListResponse(items=amendments, total=total)


@router.get("/amendments/{amendment_id}", response_model=AmendmentRequestResponse)
async def get_amendment_detail(
    amendment_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get amendment request details."""
    service = DashboardService(db)
    amendment = await service.get_amendment_by_id(amendment_id, current_user.id)
    
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment request not found")
    
    return amendment


# =============================================================================
# USER QUERIES / SUPPORT TICKETS
# =============================================================================

@router.post("/queries", response_model=UserQueryResponse)
async def create_user_query(
    data: UserQueryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit a support query/ticket."""
    service = DashboardService(db)
    
    query = await service.create_user_query(
        user_id=current_user.id,
        query_type=data.query_type.value,
        subject=data.subject,
        message=data.message,
        related_booking_id=data.related_booking_id,
        related_enquiry_id=data.related_enquiry_id,
        related_application_id=data.related_application_id,
        attachments=data.attachments,
        priority=data.priority
    )
    
    return query


@router.get("/queries", response_model=UserQueryListResponse)
async def get_user_queries(
    status: Optional[QueryStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's support queries."""
    service = DashboardService(db)
    queries, total, counts = await service.get_user_queries(
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return UserQueryListResponse(
        items=queries,
        total=total,
        open_count=counts.get('open', 0),
        resolved_count=counts.get('resolved', 0)
    )


@router.get("/queries/{query_id}", response_model=UserQueryResponse)
async def get_query_detail(
    query_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get query details with responses."""
    service = DashboardService(db)
    query = await service.get_query_by_id(query_id, current_user.id)
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return query


@router.post("/queries/{query_id}/respond", response_model=UserQueryResponse)
async def respond_to_query(
    query_id: int = Path(...),
    data: QueryResponseCreate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a response to a query."""
    service = DashboardService(db)
    query = await service.get_query_by_id(query_id, current_user.id)
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    await service.add_query_response(
        query_id=query_id,
        responder_id=current_user.id,
        message=data.message,
        is_staff_response=False,
        attachments=data.attachments
    )
    
    # Refresh query with responses
    return await service.get_query_by_id(query_id, current_user.id)


# =============================================================================
# ACTIVITY LOGS
# =============================================================================

@router.get("/activities", response_model=ActivityLogListResponse)
async def get_user_activities(
    activity_type: Optional[ActivityType] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's activity logs."""
    service = DashboardService(db)
    activities, total = await service.get_user_activities(
        user_id=current_user.id,
        activity_type=activity_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    
    return ActivityLogListResponse(
        items=activities,
        total=total,
        page=page,
        page_size=page_size
    )


# =============================================================================
# DASHBOARD SUMMARY
# =============================================================================

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard summary with stats and recent activities."""
    service = DashboardService(db)
    summary = await service.get_dashboard_summary(current_user.id)
    
    return DashboardSummary(
        stats=DashboardStats(**summary['stats']),
        upcoming_bookings=[BookingSummary(**b) for b in summary['upcoming_bookings']],
        recent_activity=summary['recent_activity'],
        pending_queries=summary['pending_queries']
    )


# =============================================================================
# ADMIN ENDPOINTS FOR AMENDMENTS & QUERIES
# =============================================================================

admin_router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])


@admin_router.get("/amendments", response_model=AmendmentListResponse)
async def admin_get_amendments(
    status: Optional[AmendmentStatus] = Query(None),
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get all amendment requests."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = DashboardService(db)
    # Fetch without user filter for admin
    amendments, total = await service.get_user_amendments(
        user_id=user_id if user_id else 0,  # 0 means all users
        status=status,
        page=page,
        page_size=page_size
    )
    
    return AmendmentListResponse(items=amendments, total=total)


@admin_router.put("/amendments/{amendment_id}", response_model=AmendmentRequestResponse)
async def admin_update_amendment(
    amendment_id: int = Path(...),
    data: AmendmentStatusUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Update amendment status."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = DashboardService(db)
    amendment = await service.update_amendment_status(
        amendment_id=amendment_id,
        status=data.status,
        amendment_fee=data.amendment_fee,
        supplier_penalty=data.supplier_penalty,
        refund_amount=data.refund_amount,
        admin_remarks=data.admin_remarks,
        processed_by=current_user.id
    )
    
    if not amendment:
        raise HTTPException(status_code=404, detail="Amendment not found")
    
    return amendment


@admin_router.get("/queries", response_model=UserQueryListResponse)
async def admin_get_queries(
    status: Optional[QueryStatus] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get all user queries."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # For admin, get all queries
    from sqlalchemy import select, func, desc
    from app.dashboard.models import UserQuery
    
    stmt = select(UserQuery)
    if status:
        stmt = stmt.where(UserQuery.status == status)
    if priority:
        stmt = stmt.where(UserQuery.priority == priority)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar() or 0
    
    stmt = stmt.order_by(desc(UserQuery.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(stmt)
    queries = list(result.scalars().all())
    
    return UserQueryListResponse(
        items=queries,
        total=total,
        open_count=0,
        resolved_count=0
    )


@admin_router.put("/queries/{query_id}", response_model=UserQueryResponse)
async def admin_update_query(
    query_id: int = Path(...),
    data: QueryStatusUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Update query status."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = DashboardService(db)
    query = await service.update_query_status(
        query_id=query_id,
        status=data.status,
        resolution=data.resolution,
        resolved_by=current_user.id,
        priority=data.priority
    )
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return query


@admin_router.post("/queries/{query_id}/respond", response_model=UserQueryResponse)
async def admin_respond_to_query(
    query_id: int = Path(...),
    data: QueryResponseCreate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Add staff response to query."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = DashboardService(db)
    query = await service.get_query_by_id(query_id)
    
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    await service.add_query_response(
        query_id=query_id,
        responder_id=current_user.id,
        message=data.message,
        is_staff_response=True,
        attachments=data.attachments
    )
    
    return await service.get_query_by_id(query_id)
