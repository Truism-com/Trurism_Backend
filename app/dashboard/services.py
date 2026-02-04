"""
Customer Dashboard Service Layer

Business logic for B2C customer dashboard.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc

from app.dashboard.models import (
    SocialAccount, AmendmentRequest, UserQuery, QueryResponse, ActivityLog,
    SocialProvider, AmendmentStatus, QueryStatus, ActivityType
)
from app.auth.models import User
from app.booking.models import FlightBooking, HotelBooking

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for customer dashboard operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # SOCIAL LOGIN MANAGEMENT
    # =========================================================================
    
    async def link_social_account(
        self,
        user_id: int,
        provider: SocialProvider,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        profile_data: Optional[Dict[str, Any]] = None
    ) -> SocialAccount:
        """Link a social account to user."""
        # Check if already linked
        stmt = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.provider == provider
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.provider_user_id = provider_user_id
            existing.provider_email = provider_email
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.token_expires_at = token_expires_at
            existing.profile_data = profile_data
            existing.last_used_at = datetime.utcnow()
            existing.is_active = True
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        # Create new
        account = SocialAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            profile_data=profile_data,
            profile_picture_url=profile_data.get('picture') if profile_data else None
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type=ActivityType.SOCIAL_LINK,
            description=f"Linked {provider.value} account",
            entity_type="social_account",
            entity_id=account.id
        )
        
        return account
    
    async def unlink_social_account(
        self,
        user_id: int,
        provider: SocialProvider
    ) -> bool:
        """Unlink a social account."""
        stmt = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.provider == provider
        )
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            return False
        
        account.is_active = False
        await self.db.commit()
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type=ActivityType.SOCIAL_UNLINK,
            description=f"Unlinked {provider.value} account"
        )
        
        return True
    
    async def get_linked_accounts(self, user_id: int) -> List[SocialAccount]:
        """Get all linked social accounts."""
        stmt = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def find_user_by_social(
        self,
        provider: SocialProvider,
        provider_user_id: str
    ) -> Optional[User]:
        """Find user by social account."""
        stmt = select(SocialAccount).where(
            SocialAccount.provider == provider,
            SocialAccount.provider_user_id == provider_user_id,
            SocialAccount.is_active == True
        )
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account:
            stmt = select(User).where(User.id == account.user_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        
        return None
    
    # =========================================================================
    # BOOKINGS MANAGEMENT
    # =========================================================================
    
    async def get_user_bookings(
        self,
        user_id: int,
        booking_type: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int, Dict[str, int]]:
        """Get user's booking history with aggregations."""
        bookings = []
        
        # Fetch flight bookings
        flight_stmt = select(FlightBooking).where(FlightBooking.user_id == user_id)
        if status:
            flight_stmt = flight_stmt.where(FlightBooking.status == status)
        result = await self.db.execute(flight_stmt)
        for fb in result.scalars().all():
            bookings.append({
                'id': fb.id,
                'booking_reference': fb.pnr,
                'booking_type': 'flight',
                'status': fb.status.value if hasattr(fb.status, 'value') else fb.status,
                'travel_date': fb.travel_date if hasattr(fb, 'travel_date') else None,
                'total_amount': float(fb.total_amount) if fb.total_amount else 0,
                'paid_amount': float(fb.total_amount) if fb.payment_status == 'paid' else 0,
                'created_at': fb.created_at,
                'summary': f"Flight Booking - {fb.pnr}"
            })
        
        # Fetch hotel bookings
        hotel_stmt = select(HotelBooking).where(HotelBooking.user_id == user_id)
        if status:
            hotel_stmt = hotel_stmt.where(HotelBooking.status == status)
        result = await self.db.execute(hotel_stmt)
        for hb in result.scalars().all():
            bookings.append({
                'id': hb.id,
                'booking_reference': hb.confirmation_number or f"HB{hb.id:06d}",
                'booking_type': 'hotel',
                'status': hb.status.value if hasattr(hb.status, 'value') else hb.status,
                'travel_date': hb.check_in,
                'total_amount': float(hb.total_amount) if hb.total_amount else 0,
                'paid_amount': float(hb.total_amount) if hb.payment_status == 'paid' else 0,
                'created_at': hb.created_at,
                'summary': f"Hotel - {hb.hotel_name}"
            })
        
        # Sort by created_at descending
        bookings.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Calculate counts
        counts = {
            'upcoming': len([b for b in bookings if b.get('travel_date') and b['travel_date'] > datetime.now().date()]),
            'completed': len([b for b in bookings if b['status'] == 'completed']),
            'cancelled': len([b for b in bookings if b['status'] == 'cancelled'])
        }
        
        total = len(bookings)
        
        # Paginate
        start = (page - 1) * page_size
        bookings = bookings[start:start + page_size]
        
        return bookings, total, counts
    
    async def get_booking_detail(
        self,
        user_id: int,
        booking_id: int,
        booking_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed booking information."""
        if booking_type == 'flight':
            stmt = select(FlightBooking).where(
                FlightBooking.id == booking_id,
                FlightBooking.user_id == user_id
            )
            result = await self.db.execute(stmt)
            booking = result.scalar_one_or_none()
            if booking:
                return {
                    'id': booking.id,
                    'booking_reference': booking.pnr,
                    'booking_type': 'flight',
                    'status': booking.status.value if hasattr(booking.status, 'value') else booking.status,
                    'payment_status': booking.payment_status.value if hasattr(booking.payment_status, 'value') else booking.payment_status,
                    'details': booking.booking_data if hasattr(booking, 'booking_data') else {},
                    'total_amount': float(booking.total_amount) if booking.total_amount else 0,
                    'can_cancel': booking.status not in ['cancelled', 'completed'],
                    'can_modify': booking.status == 'confirmed',
                    'created_at': booking.created_at
                }
        
        elif booking_type == 'hotel':
            stmt = select(HotelBooking).where(
                HotelBooking.id == booking_id,
                HotelBooking.user_id == user_id
            )
            result = await self.db.execute(stmt)
            booking = result.scalar_one_or_none()
            if booking:
                return {
                    'id': booking.id,
                    'booking_reference': booking.confirmation_number,
                    'booking_type': 'hotel',
                    'status': booking.status.value if hasattr(booking.status, 'value') else booking.status,
                    'payment_status': booking.payment_status.value if hasattr(booking.payment_status, 'value') else booking.payment_status,
                    'travel_date': booking.check_in,
                    'return_date': booking.check_out,
                    'details': {
                        'hotel_name': booking.hotel_name,
                        'hotel_id': booking.hotel_id,
                        'room_type': booking.room_type,
                        'guests': booking.guests
                    },
                    'total_amount': float(booking.total_amount) if booking.total_amount else 0,
                    'can_cancel': booking.status not in ['cancelled', 'completed'],
                    'can_modify': booking.status == 'confirmed',
                    'created_at': booking.created_at
                }
        
        return None
    
    # =========================================================================
    # AMENDMENT REQUESTS
    # =========================================================================
    
    async def create_amendment_request(
        self,
        user_id: int,
        booking_id: int,
        booking_type: str,
        amendment_type: str,
        reason: str,
        requested_changes: Optional[Dict[str, Any]] = None,
        documents: Optional[List[str]] = None
    ) -> AmendmentRequest:
        """Create an amendment request."""
        # Generate request number
        count_stmt = select(func.count(AmendmentRequest.id))
        result = await self.db.execute(count_stmt)
        count = result.scalar() or 0
        request_number = f"AMD{datetime.now().strftime('%Y%m')}{count + 1:05d}"
        
        # Get booking reference
        booking_reference = f"{booking_type.upper()}-{booking_id}"
        
        amendment = AmendmentRequest(
            request_number=request_number,
            user_id=user_id,
            booking_id=booking_id,
            booking_type=booking_type,
            booking_reference=booking_reference,
            amendment_type=amendment_type,
            reason=reason,
            requested_changes=requested_changes,
            documents=documents,
            status=AmendmentStatus.PENDING
        )
        self.db.add(amendment)
        await self.db.commit()
        await self.db.refresh(amendment)
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type=ActivityType.AMENDMENT_CREATED,
            description=f"Created {amendment_type} request for {booking_reference}",
            entity_type="amendment_request",
            entity_id=amendment.id
        )
        
        return amendment
    
    async def get_user_amendments(
        self,
        user_id: int,
        status: Optional[AmendmentStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AmendmentRequest], int]:
        """Get user's amendment requests."""
        stmt = select(AmendmentRequest).where(AmendmentRequest.user_id == user_id)
        
        if status:
            stmt = stmt.where(AmendmentRequest.status == status)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(desc(AmendmentRequest.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        amendments = list(result.scalars().all())
        
        return amendments, total
    
    async def get_amendment_by_id(
        self,
        amendment_id: int,
        user_id: Optional[int] = None
    ) -> Optional[AmendmentRequest]:
        """Get amendment request by ID."""
        stmt = select(AmendmentRequest).where(AmendmentRequest.id == amendment_id)
        if user_id:
            stmt = stmt.where(AmendmentRequest.user_id == user_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_amendment_status(
        self,
        amendment_id: int,
        status: AmendmentStatus,
        amendment_fee: Optional[float] = None,
        supplier_penalty: Optional[float] = None,
        refund_amount: Optional[float] = None,
        admin_remarks: Optional[str] = None,
        processed_by: Optional[int] = None
    ) -> Optional[AmendmentRequest]:
        """Update amendment request status (admin)."""
        amendment = await self.get_amendment_by_id(amendment_id)
        if not amendment:
            return None
        
        amendment.status = status
        if amendment_fee is not None:
            amendment.amendment_fee = amendment_fee
        if supplier_penalty is not None:
            amendment.supplier_penalty = supplier_penalty
        if refund_amount is not None:
            amendment.refund_amount = refund_amount
        if admin_remarks:
            amendment.admin_remarks = admin_remarks
        if processed_by:
            amendment.processed_by = processed_by
        
        if status in [AmendmentStatus.APPROVED, AmendmentStatus.REJECTED]:
            amendment.processed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(amendment)
        
        # Log activity for user
        await self.log_activity(
            user_id=amendment.user_id,
            activity_type=ActivityType.AMENDMENT_UPDATED,
            description=f"Amendment {amendment.request_number} status updated to {status.value}",
            entity_type="amendment_request",
            entity_id=amendment.id
        )
        
        return amendment
    
    # =========================================================================
    # USER QUERIES / SUPPORT TICKETS
    # =========================================================================
    
    async def create_user_query(
        self,
        user_id: int,
        query_type: str,
        subject: str,
        message: str,
        related_booking_id: Optional[int] = None,
        related_enquiry_id: Optional[int] = None,
        related_application_id: Optional[int] = None,
        attachments: Optional[List[str]] = None,
        priority: str = "normal"
    ) -> UserQuery:
        """Create a user query/support ticket."""
        # Generate ticket number
        count_stmt = select(func.count(UserQuery.id))
        result = await self.db.execute(count_stmt)
        count = result.scalar() or 0
        ticket_number = f"TKT{datetime.now().strftime('%Y%m')}{count + 1:06d}"
        
        query = UserQuery(
            ticket_number=ticket_number,
            user_id=user_id,
            query_type=query_type,
            subject=subject,
            message=message,
            related_booking_id=related_booking_id,
            related_enquiry_id=related_enquiry_id,
            related_application_id=related_application_id,
            attachments=attachments,
            priority=priority,
            status=QueryStatus.OPEN
        )
        self.db.add(query)
        await self.db.commit()
        await self.db.refresh(query)
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type=ActivityType.QUERY_SUBMITTED,
            description=f"Submitted support ticket: {subject}",
            entity_type="user_query",
            entity_id=query.id
        )
        
        return query
    
    async def get_user_queries(
        self,
        user_id: int,
        status: Optional[QueryStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[UserQuery], int, Dict[str, int]]:
        """Get user's queries with responses."""
        stmt = select(UserQuery).where(UserQuery.user_id == user_id)
        
        if status:
            stmt = stmt.where(UserQuery.status == status)
        
        # Count by status
        open_stmt = select(func.count()).where(
            UserQuery.user_id == user_id,
            UserQuery.status.in_([QueryStatus.OPEN, QueryStatus.IN_PROGRESS, QueryStatus.AWAITING_RESPONSE])
        )
        result = await self.db.execute(open_stmt)
        open_count = result.scalar() or 0
        
        resolved_stmt = select(func.count()).where(
            UserQuery.user_id == user_id,
            UserQuery.status.in_([QueryStatus.RESOLVED, QueryStatus.CLOSED])
        )
        result = await self.db.execute(resolved_stmt)
        resolved_count = result.scalar() or 0
        
        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(desc(UserQuery.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        queries = list(result.scalars().all())
        
        # Fetch responses for each query
        for query in queries:
            resp_stmt = select(QueryResponse).where(QueryResponse.query_id == query.id)
            resp_result = await self.db.execute(resp_stmt)
            query.responses = list(resp_result.scalars().all())
        
        return queries, total, {'open': open_count, 'resolved': resolved_count}
    
    async def get_query_by_id(
        self,
        query_id: int,
        user_id: Optional[int] = None
    ) -> Optional[UserQuery]:
        """Get query by ID with responses."""
        stmt = select(UserQuery).where(UserQuery.id == query_id)
        if user_id:
            stmt = stmt.where(UserQuery.user_id == user_id)
        
        result = await self.db.execute(stmt)
        query = result.scalar_one_or_none()
        
        if query:
            resp_stmt = select(QueryResponse).where(QueryResponse.query_id == query.id)
            resp_result = await self.db.execute(resp_stmt)
            query.responses = list(resp_result.scalars().all())
        
        return query
    
    async def add_query_response(
        self,
        query_id: int,
        responder_id: int,
        message: str,
        is_staff_response: bool = False,
        attachments: Optional[List[str]] = None
    ) -> QueryResponse:
        """Add a response to a query."""
        response = QueryResponse(
            query_id=query_id,
            responder_id=responder_id,
            is_staff_response=is_staff_response,
            message=message,
            attachments=attachments
        )
        self.db.add(response)
        
        # Update query status
        query = await self.get_query_by_id(query_id)
        if query:
            if is_staff_response:
                query.status = QueryStatus.AWAITING_RESPONSE
            else:
                query.status = QueryStatus.IN_PROGRESS
        
        await self.db.commit()
        await self.db.refresh(response)
        
        return response
    
    async def update_query_status(
        self,
        query_id: int,
        status: QueryStatus,
        resolution: Optional[str] = None,
        resolved_by: Optional[int] = None,
        priority: Optional[str] = None
    ) -> Optional[UserQuery]:
        """Update query status (admin)."""
        query = await self.get_query_by_id(query_id)
        if not query:
            return None
        
        query.status = status
        if resolution:
            query.resolution = resolution
        if resolved_by:
            query.resolved_by = resolved_by
        if priority:
            query.priority = priority
        
        if status == QueryStatus.RESOLVED:
            query.resolved_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(query)
        
        return query
    
    # =========================================================================
    # ACTIVITY LOGGING
    # =========================================================================
    
    async def log_activity(
        self,
        user_id: int,
        activity_type: ActivityType,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Log user activity."""
        log = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_user_activities(
        self,
        user_id: int,
        activity_type: Optional[ActivityType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ActivityLog], int]:
        """Get user's activity logs."""
        stmt = select(ActivityLog).where(ActivityLog.user_id == user_id)
        
        if activity_type:
            stmt = stmt.where(ActivityLog.activity_type == activity_type)
        if from_date:
            stmt = stmt.where(ActivityLog.created_at >= from_date)
        if to_date:
            stmt = stmt.where(ActivityLog.created_at <= to_date)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(desc(ActivityLog.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        logs = list(result.scalars().all())
        
        return logs, total
    
    # =========================================================================
    # DASHBOARD SUMMARY
    # =========================================================================
    
    async def get_dashboard_summary(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard summary for user."""
        # Get booking counts
        bookings, total_bookings, counts = await self.get_user_bookings(
            user_id=user_id,
            page=1,
            page_size=5
        )
        
        # Get pending amendments
        pending_stmt = select(func.count()).where(
            AmendmentRequest.user_id == user_id,
            AmendmentRequest.status.in_([AmendmentStatus.PENDING, AmendmentStatus.IN_REVIEW])
        )
        result = await self.db.execute(pending_stmt)
        pending_amendments = result.scalar() or 0
        
        # Get open queries
        open_stmt = select(func.count()).where(
            UserQuery.user_id == user_id,
            UserQuery.status.in_([QueryStatus.OPEN, QueryStatus.IN_PROGRESS])
        )
        result = await self.db.execute(open_stmt)
        open_queries = result.scalar() or 0
        
        # Recent activity
        activities, _ = await self.get_user_activities(
            user_id=user_id,
            page=1,
            page_size=10
        )
        
        # Pending queries
        queries, _, _ = await self.get_user_queries(
            user_id=user_id,
            status=QueryStatus.OPEN,
            page=1,
            page_size=5
        )
        
        return {
            'stats': {
                'total_bookings': total_bookings,
                'upcoming_trips': counts.get('upcoming', 0),
                'pending_payments': 0,  # Calculate from bookings
                'pending_amendments': pending_amendments,
                'open_queries': open_queries,
                'wallet_balance': 0  # Fetch from wallet module
            },
            'upcoming_bookings': bookings[:5],
            'recent_activity': activities,
            'pending_queries': queries
        }
