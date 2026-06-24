"""
Admin Services

This module contains business logic for administrative operations:
- User and agent management
- Booking oversight and management
- System analytics and reporting
- Agent approval workflow
- Dashboard metrics calculation
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.auth.models import User, UserRole, AgentApprovalStatus
from app.booking.models import FlightBooking, HotelBooking, BusBooking, BookingStatus, PaymentStatus
from app.admin.schemas import (
    AgentApprovalRequest, UserStatusUpdateRequest, BookingStatusUpdateRequest,
    BookingAnalyticsRequest
)


class AdminUserService:
    """
    Admin service for user management operations.

    Supports tenant-scoped queries for tenant admins and
    global queries for superadmins.
    """

    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role_filter: Optional[UserRole] = None,
        status_filter: Optional[bool] = None,
        approval_status_filter: Optional[AgentApprovalStatus] = None
    ) -> Tuple[List[User], int]:
        """Get all users with filtering, pagination, and tenant scoping."""
        conditions = []

        if self.tenant_id is not None:
            conditions.append(User.tenant_id == self.tenant_id)

        if role_filter:
            conditions.append(User.role == role_filter)

        if status_filter is not None:
            conditions.append(User.is_active == status_filter)

        if approval_status_filter:
            conditions.append(User.approval_status == approval_status_filter)

        count_query = select(func.count(User.id))
        for cond in conditions:
            count_query = count_query.where(cond)

        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()

        query = select(User)
        for cond in conditions:
            query = query.where(cond)
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        users = result.scalars().all()

        return users, total_count
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def approve_agent(
        self,
        agent_id: int,
        approval_request: AgentApprovalRequest,
        admin_user: User
    ) -> User:
        """
        Approve or reject an agent application.
        
        Args:
            agent_id: Agent user ID
            approval_request: Approval decision and details
            admin_user: Admin user performing the action
            
        Returns:
            User: Updated agent user
            
        Raises:
            HTTPException: If agent not found or not an agent
        """
        agent = await self.get_user_by_id(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if agent.role != UserRole.AGENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an agent"
            )
        
        # Update approval status
        agent.approval_status = approval_request.approval_status
        
        # If rejected, add rejection reason (could be stored in a separate table)
        if approval_request.approval_status == AgentApprovalStatus.REJECTED:
            # TODO: Store rejection reason in agent_rejections table
            pass
        
        await self.db.commit()
        await self.db.refresh(agent)
        
        # TODO: Log admin action
        # await self._log_admin_action(admin_user, "approve_agent", agent_id, approval_request.dict())
        
        return agent
    
    async def update_user_status(
        self,
        user_id: int,
        status_request: UserStatusUpdateRequest,
        admin_user: User
    ) -> User:
        """
        Update user account status.
        
        Args:
            user_id: User ID to update
            status_request: Status update details
            admin_user: Admin user performing the action
            
        Returns:
            User: Updated user
            
        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update status fields
        if status_request.is_active is not None:
            user.is_active = status_request.is_active
        
        if status_request.is_verified is not None:
            user.is_verified = status_request.is_verified
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # TODO: Log admin action
        # await self._log_admin_action(admin_user, "update_user_status", user_id, status_request.dict())
        
        return user
    
    async def get_user_booking_count_batch(self, user_ids: List[int]) -> Dict[int, int]:
        """
        Batch-fetch booking counts for a list of user_ids.
        Single pass: 3 COUNT queries (one per booking type) instead of 3*N.
        Returns {user_id: total_booking_count}.
        """
        counts: Dict[int, int] = {user_id: 0 for user_id in user_ids}

        for model in (FlightBooking, HotelBooking, BusBooking):
            result = await self.db.execute(
                select(model.user_id, func.count(model.id).label("cnt"))
                .where(model.user_id.in_(user_ids))
                .group_by(model.user_id)
            )
            for row in result.all():
                counts[row.user_id] = counts.get(row.user_id, 0) + row.cnt

        return counts

    async def get_user_booking_count(self, user_id: int) -> int:
        """Get total booking count for a single user (used in single-user detail view)."""
        total = 0
        for model in (FlightBooking, HotelBooking, BusBooking):
            result = await self.db.execute(
                select(func.count(model.id)).where(model.user_id == user_id)
            )
            total += result.scalar()
        return total


class AdminBookingService:
    """Admin service for booking management with tenant scoping."""

    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id

    def _apply_tenant_filter(self, query, model):
        if self.tenant_id is not None:
            query = query.where(model.tenant_id == self.tenant_id)
        return query


    async def get_all_bookings(
        self,
        skip: int = 0,
        limit: int = 50,
        booking_type_filter: Optional[str] = None,
        status_filter: Optional[BookingStatus] = None,
        payment_status_filter: Optional[PaymentStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get bookings with filtering, DB-level pagination, and tenant scoping.

        Fetches total count and paginated rows using DB LIMIT/OFFSET per type.
        No full-table loads into Python memory.
        """
        type_configs = []
        if not booking_type_filter or booking_type_filter == "flight":
            type_configs.append(("flight", FlightBooking))
        if not booking_type_filter or booking_type_filter == "hotel":
            type_configs.append(("hotel", HotelBooking))
        if not booking_type_filter or booking_type_filter == "bus":
            type_configs.append(("bus", BusBooking))

        def _base_conditions(model):
            conds = []
            if self.tenant_id is not None:
                conds.append(model.tenant_id == self.tenant_id)
            if status_filter:
                conds.append(model.status == status_filter)
            if payment_status_filter:
                conds.append(model.payment_status == payment_status_filter)
            if date_from:
                conds.append(model.created_at >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                conds.append(model.created_at <= datetime.combine(date_to, datetime.max.time()))
            return conds

        # --- total count: 1 COUNT per active type ---
        total_count = 0
        for _btype, model in type_configs:
            conds = _base_conditions(model)
            q = select(func.count(model.id))
            if conds:
                q = q.where(*conds)
            total_count += (await self.db.execute(q)).scalar()

        # --- paginated rows: fetch skip+limit from each type, merge, re-sort, slice ---
        # We over-fetch (skip+limit per type) then do a final in-memory sort+slice.
        # This is bounded: at most 3 * (skip+limit) rows loaded — never the full table.
        candidate_bookings = []

        for btype, model in type_configs:
            conds = _base_conditions(model)
            q = (
                select(model, User)
                .join(User, User.id == model.user_id)
                .order_by(model.created_at.desc())
                .limit(skip + limit)
            )
            if conds:
                q = q.where(*conds)

            rows = (await self.db.execute(q)).all()
            for booking, user in rows:
                entry = {
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                    "type": btype,
                    "user_email": user.email,
                    "user_name": user.name,
                    "status": booking.status,
                    "payment_status": booking.payment_status,
                    "total_amount": booking.total_amount,
                    "currency": booking.currency,
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                }
                if btype == "flight":
                    entry["details"] = {
                        "airline": booking.airline, "flight_number": booking.flight_number,
                        "origin": booking.origin, "destination": booking.destination,
                        "departure_time": booking.departure_time, "arrival_time": booking.arrival_time,
                        "travel_class": booking.travel_class, "passenger_count": booking.passenger_count,
                    }
                elif btype == "hotel":
                    entry["details"] = {
                        "hotel_name": booking.hotel_name, "hotel_address": booking.hotel_address,
                        "city": booking.city, "checkin_date": booking.checkin_date,
                        "checkout_date": booking.checkout_date, "nights": booking.nights,
                        "rooms": booking.rooms, "adults": booking.adults, "children": booking.children,
                    }
                else:  # bus
                    entry["details"] = {
                        "operator": booking.operator, "bus_type": booking.bus_type,
                        "origin": booking.origin, "destination": booking.destination,
                        "departure_time": booking.departure_time, "arrival_time": booking.arrival_time,
                        "travel_date": booking.travel_date, "passengers": booking.passengers,
                    }
                candidate_bookings.append(entry)

        candidate_bookings.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)
        paginated = candidate_bookings[skip: skip + limit]

        return paginated, total_count
    
    async def update_booking_status(
        self,
        booking_id: int,
        booking_type: str,
        status_request: BookingStatusUpdateRequest,
        admin_user: User,
    ) -> bool:
        """Update booking status with tenant isolation."""
        model_map = {
            "flight": FlightBooking,
            "hotel": HotelBooking,
            "bus": BusBooking,
        }
        model = model_map.get(booking_type)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid booking type: {booking_type}",
            )

        query = select(model).where(model.id == booking_id)
        query = self._apply_tenant_filter(query, model)

        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        booking.status = status_request.status
        await self.db.commit()

        logger.info(
            "Booking %s/%d status updated to %s by admin %d",
            booking_type, booking_id, status_request.status, admin_user.id,
        )

        return True


class AdminAnalyticsService:
    """Admin analytics with tenant scoping and real metric calculations."""

    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id

    def _scoped_count(self, model, *extra_conditions):
        """Build a COUNT query with optional tenant scoping."""
        q = select(func.count(model.id))
        if self.tenant_id is not None and hasattr(model, "tenant_id"):
            q = q.where(model.tenant_id == self.tenant_id)
        for cond in extra_conditions:
            q = q.where(cond)
        return q

    def _scoped_sum(self, model, column, *extra_conditions):
        """Build a SUM query with optional tenant scoping."""
        q = select(func.coalesce(func.sum(column), 0))
        if self.tenant_id is not None and hasattr(model, "tenant_id"):
            q = q.where(model.tenant_id == self.tenant_id)
        for cond in extra_conditions:
            q = q.where(cond)
        return q

    def _user_count(self, *extra_conditions):
        """Build a user COUNT query with optional tenant scoping."""
        q = select(func.count(User.id))
        if self.tenant_id is not None:
            q = q.where(User.tenant_id == self.tenant_id)
        for cond in extra_conditions:
            q = q.where(cond)
        return q

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculate real dashboard statistics from database."""
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        month_start = datetime.combine(today.replace(day=1), datetime.min.time())

        booking_models = (FlightBooking, HotelBooking, BusBooking)

        total_users = (await self.db.execute(self._user_count())).scalar()
        active_users = (await self.db.execute(self._user_count(User.is_active == True))).scalar()

        pending_agents = (await self.db.execute(self._user_count(
            User.role == UserRole.AGENT,
            User.approval_status == AgentApprovalStatus.PENDING,
        ))).scalar()

        approved_agents = (await self.db.execute(self._user_count(
            User.role == UserRole.AGENT,
            User.approval_status == AgentApprovalStatus.APPROVED,
        ))).scalar()

        new_users_today = (await self.db.execute(self._user_count(
            User.created_at >= today_start,
            User.created_at <= today_end,
        ))).scalar()

        agent_apps_today = (await self.db.execute(self._user_count(
            User.role == UserRole.AGENT,
            User.approval_status == AgentApprovalStatus.PENDING,
            User.created_at >= today_start,
            User.created_at <= today_end,
        ))).scalar()

        total_bookings = sum([
            (await self.db.execute(self._scoped_count(m))).scalar()
            for m in booking_models
        ])

        confirmed_bookings = sum([
            (await self.db.execute(self._scoped_count(m, m.status == BookingStatus.CONFIRMED))).scalar()
            for m in booking_models
        ])
        cancelled_bookings = sum([
            (await self.db.execute(self._scoped_count(m, m.status == BookingStatus.CANCELLED))).scalar()
            for m in booking_models
        ])
        pending_bookings = sum([
            (await self.db.execute(self._scoped_count(m, m.status == BookingStatus.PENDING))).scalar()
            for m in booking_models
        ])

        total_revenue = sum([
            (await self.db.execute(self._scoped_sum(
                m, m.total_amount, m.payment_status == PaymentStatus.SUCCESS
            ))).scalar()
            for m in booking_models
        ])

        revenue_today = sum([
            (await self.db.execute(self._scoped_sum(
                m, m.total_amount, m.payment_status == PaymentStatus.SUCCESS,
                m.created_at >= today_start, m.created_at <= today_end,
            ))).scalar()
            for m in booking_models
        ])

        revenue_this_month = sum([
            (await self.db.execute(self._scoped_sum(
                m, m.total_amount, m.payment_status == PaymentStatus.SUCCESS,
                m.created_at >= month_start, m.created_at <= today_end,
            ))).scalar()
            for m in booking_models
        ])

        bookings_today = sum([
            (await self.db.execute(self._scoped_count(
                m, m.created_at >= today_start, m.created_at <= today_end
            ))).scalar()
            for m in booking_models
        ])

        cancellations_today = sum([
            (await self.db.execute(self._scoped_count(
                m, m.status == BookingStatus.CANCELLED,
                m.updated_at >= today_start, m.updated_at <= today_end,
            ))).scalar()
            for m in booking_models
        ])

        avg_booking = round(total_revenue / total_bookings, 2) if total_bookings > 0 else 0
        booking_success_rate = round((confirmed_bookings / total_bookings) * 100, 1) if total_bookings > 0 else 0
        cancellation_rate = round((cancelled_bookings / total_bookings) * 100, 1) if total_bookings > 0 else 0
        resolved = confirmed_bookings + cancelled_bookings
        payment_success_rate = round((confirmed_bookings / resolved) * 100, 1) if resolved > 0 else 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_agents": pending_agents,
            "approved_agents": approved_agents,
            "total_bookings": total_bookings,
            "total_revenue": round(total_revenue, 2),
            "average_booking_value": avg_booking,
            "bookings_today": bookings_today,
            "revenue_today": round(revenue_today, 2),
            "revenue_this_month": round(revenue_this_month, 2),
            "cancellations_today": cancellations_today,
            "new_users_today": new_users_today,
            "agent_applications_today": agent_apps_today,
            "booking_success_rate": booking_success_rate,
            "cancellation_rate": cancellation_rate,
            "payment_success_rate": payment_success_rate,
            "confirmed_bookings": confirmed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "pending_bookings": pending_bookings,
        }

    async def get_booking_analytics(self, analytics_request: BookingAnalyticsRequest) -> Dict[str, Any]:
        """Get booking analytics for specified period with tenant scoping."""
        start = datetime.combine(analytics_request.start_date, datetime.min.time())
        end = datetime.combine(analytics_request.end_date, datetime.max.time())

        booking_models = (FlightBooking, HotelBooking, BusBooking)

        total = sum([
            (await self.db.execute(self._scoped_count(
                m, m.created_at >= start, m.created_at <= end
            ))).scalar()
            for m in booking_models
        ])

        revenue = sum([
            (await self.db.execute(self._scoped_sum(
                m, m.total_amount, m.payment_status == PaymentStatus.SUCCESS,
                m.created_at >= start, m.created_at <= end,
            ))).scalar()
            for m in booking_models
        ])

        avg_value = round(revenue / total, 2) if total > 0 else 0

        return {
            "period": f"{analytics_request.start_date} to {analytics_request.end_date}",
            "total_bookings": total,
            "total_revenue": round(revenue, 2),
            "average_booking_value": avg_value,
            "data_points": [],
        }

