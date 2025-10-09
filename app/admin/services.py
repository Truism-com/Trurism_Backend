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
from datetime import datetime, date, timedelta
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
    
    This service handles user oversight, agent approval workflow,
    and user status management for administrative purposes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role_filter: Optional[UserRole] = None,
        status_filter: Optional[bool] = None,
        approval_status_filter: Optional[AgentApprovalStatus] = None
    ) -> Tuple[List[User], int]:
        """
        Get all users with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role_filter: Filter by user role
            status_filter: Filter by active status
            approval_status_filter: Filter by agent approval status
            
        Returns:
            Tuple[List[User], int]: List of users and total count
        """
        query = select(User)
        
        # Apply filters
        if role_filter:
            query = query.where(User.role == role_filter)
        
        if status_filter is not None:
            query = query.where(User.is_active == status_filter)
        
        if approval_status_filter:
            query = query.where(User.approval_status == approval_status_filter)
        
        # Get total count
        count_query = select(func.count(User.id))
        for condition in query.whereclause.children if hasattr(query.whereclause, 'children') else []:
            count_query = count_query.where(condition)
        
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar()
        
        # Get paginated results
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
    
    async def get_user_booking_count(self, user_id: int) -> int:
        """Get total booking count for a user."""
        # Count flight bookings
        flight_count = await self.db.execute(
            select(func.count(FlightBooking.id)).where(FlightBooking.user_id == user_id)
        )
        flight_total = flight_count.scalar()
        
        # Count hotel bookings
        hotel_count = await self.db.execute(
            select(func.count(HotelBooking.id)).where(HotelBooking.user_id == user_id)
        )
        hotel_total = hotel_count.scalar()
        
        # Count bus bookings
        bus_count = await self.db.execute(
            select(func.count(BusBooking.id)).where(BusBooking.user_id == user_id)
        )
        bus_total = bus_count.scalar()
        
        return flight_total + hotel_total + bus_total


class AdminBookingService:
    """
    Admin service for booking management operations.
    
    This service handles booking oversight, status management,
    and booking analytics for administrative purposes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
        Get all bookings with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            booking_type_filter: Filter by booking type (flight, hotel, bus)
            status_filter: Filter by booking status
            payment_status_filter: Filter by payment status
            date_from: Filter bookings from date
            date_to: Filter bookings to date
            
        Returns:
            Tuple[List[Dict], int]: List of bookings and total count
        """
        all_bookings = []
        
        # Get flight bookings
        if not booking_type_filter or booking_type_filter == "flight":
            flight_query = select(FlightBooking, User).join(User).where(User.id == FlightBooking.user_id)
            
            if status_filter:
                flight_query = flight_query.where(FlightBooking.status == status_filter)
            if payment_status_filter:
                flight_query = flight_query.where(FlightBooking.payment_status == payment_status_filter)
            if date_from:
                flight_query = flight_query.where(FlightBooking.created_at >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                flight_query = flight_query.where(FlightBooking.created_at <= datetime.combine(date_to, datetime.max.time()))
            
            flight_result = await self.db.execute(flight_query)
            flight_bookings = flight_result.all()
            
            for booking, user in flight_bookings:
                all_bookings.append({
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                    "type": "flight",
                    "user_email": user.email,
                    "user_name": user.name,
                    "status": booking.status,
                    "payment_status": booking.payment_status,
                    "total_amount": booking.total_amount,
                    "currency": booking.currency,
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                    "details": {
                        "airline": booking.airline,
                        "flight_number": booking.flight_number,
                        "origin": booking.origin,
                        "destination": booking.destination,
                        "departure_time": booking.departure_time,
                        "arrival_time": booking.arrival_time,
                        "travel_class": booking.travel_class,
                        "passenger_count": booking.passenger_count
                    }
                })
        
        # Get hotel bookings
        if not booking_type_filter or booking_type_filter == "hotel":
            hotel_query = select(HotelBooking, User).join(User).where(User.id == HotelBooking.user_id)
            
            if status_filter:
                hotel_query = hotel_query.where(HotelBooking.status == status_filter)
            if payment_status_filter:
                hotel_query = hotel_query.where(HotelBooking.payment_status == payment_status_filter)
            if date_from:
                hotel_query = hotel_query.where(HotelBooking.created_at >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                hotel_query = hotel_query.where(HotelBooking.created_at <= datetime.combine(date_to, datetime.max.time()))
            
            hotel_result = await self.db.execute(hotel_query)
            hotel_bookings = hotel_result.all()
            
            for booking, user in hotel_bookings:
                all_bookings.append({
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                    "type": "hotel",
                    "user_email": user.email,
                    "user_name": user.name,
                    "status": booking.status,
                    "payment_status": booking.payment_status,
                    "total_amount": booking.total_amount,
                    "currency": booking.currency,
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                    "details": {
                        "hotel_name": booking.hotel_name,
                        "hotel_address": booking.hotel_address,
                        "city": booking.city,
                        "checkin_date": booking.checkin_date,
                        "checkout_date": booking.checkout_date,
                        "nights": booking.nights,
                        "rooms": booking.rooms,
                        "adults": booking.adults,
                        "children": booking.children
                    }
                })
        
        # Get bus bookings
        if not booking_type_filter or booking_type_filter == "bus":
            bus_query = select(BusBooking, User).join(User).where(User.id == BusBooking.user_id)
            
            if status_filter:
                bus_query = bus_query.where(BusBooking.status == status_filter)
            if payment_status_filter:
                bus_query = bus_query.where(BusBooking.payment_status == payment_status_filter)
            if date_from:
                bus_query = bus_query.where(BusBooking.created_at >= datetime.combine(date_from, datetime.min.time()))
            if date_to:
                bus_query = bus_query.where(BusBooking.created_at <= datetime.combine(date_to, datetime.max.time()))
            
            bus_result = await self.db.execute(bus_query)
            bus_bookings = bus_result.all()
            
            for booking, user in bus_bookings:
                all_bookings.append({
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                    "type": "bus",
                    "user_email": user.email,
                    "user_name": user.name,
                    "status": booking.status,
                    "payment_status": booking.payment_status,
                    "total_amount": booking.total_amount,
                    "currency": booking.currency,
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                    "details": {
                        "operator": booking.operator,
                        "bus_type": booking.bus_type,
                        "origin": booking.origin,
                        "destination": booking.destination,
                        "departure_time": booking.departure_time,
                        "arrival_time": booking.arrival_time,
                        "travel_date": booking.travel_date,
                        "passengers": booking.passengers
                    }
                })
        
        # Sort by creation date (most recent first)
        all_bookings.sort(key=lambda x: x["created_at"], reverse=True)
        
        total_count = len(all_bookings)
        paginated_bookings = all_bookings[skip:skip + limit]
        
        return paginated_bookings, total_count
    
    async def update_booking_status(
        self,
        booking_id: int,
        booking_type: str,
        status_request: BookingStatusUpdateRequest,
        admin_user: User
    ) -> bool:
        """
        Update booking status.
        
        Args:
            booking_id: Booking ID to update
            booking_type: Type of booking (flight, hotel, bus)
            status_request: Status update details
            admin_user: Admin user performing the action
            
        Returns:
            bool: True if update successful
            
        Raises:
            HTTPException: If booking not found
        """
        booking = None
        
        if booking_type == "flight":
            result = await self.db.execute(select(FlightBooking).where(FlightBooking.id == booking_id))
            booking = result.scalar_one_or_none()
        elif booking_type == "hotel":
            result = await self.db.execute(select(HotelBooking).where(HotelBooking.id == booking_id))
            booking = result.scalar_one_or_none()
        elif booking_type == "bus":
            result = await self.db.execute(select(BusBooking).where(BusBooking.id == booking_id))
            booking = result.scalar_one_or_none()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Update booking status
        booking.status = status_request.status
        
        await self.db.commit()
        
        # TODO: Log admin action
        # await self._log_admin_action(admin_user, "update_booking_status", booking_id, status_request.dict())
        
        return True


class AdminAnalyticsService:
    """
    Admin service for analytics and reporting operations.
    
    This service handles dashboard metrics calculation,
    booking analytics, and system reporting.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics and metrics.
        
        Returns:
            Dict[str, Any]: Dashboard statistics
        """
        # User statistics
        total_users = await self.db.execute(select(func.count(User.id)))
        total_users_count = total_users.scalar()
        
        active_users = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users_count = active_users.scalar()
        
        pending_agents = await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.role == UserRole.AGENT, User.approval_status == AgentApprovalStatus.PENDING)
            )
        )
        pending_agents_count = pending_agents.scalar()
        
        approved_agents = await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.role == UserRole.AGENT, User.approval_status == AgentApprovalStatus.APPROVED)
            )
        )
        approved_agents_count = approved_agents.scalar()
        
        # Booking statistics
        total_flight_bookings = await self.db.execute(select(func.count(FlightBooking.id)))
        total_hotel_bookings = await self.db.execute(select(func.count(HotelBooking.id)))
        total_bus_bookings = await self.db.execute(select(func.count(BusBooking.id)))
        
        total_bookings_count = (
            total_flight_bookings.scalar() +
            total_hotel_bookings.scalar() +
            total_bus_bookings.scalar()
        )
        
        # Revenue statistics
        flight_revenue = await self.db.execute(
            select(func.sum(FlightBooking.total_amount)).where(
                FlightBooking.payment_status == PaymentStatus.SUCCESS
            )
        )
        hotel_revenue = await self.db.execute(
            select(func.sum(HotelBooking.total_amount)).where(
                HotelBooking.payment_status == PaymentStatus.SUCCESS
            )
        )
        bus_revenue = await self.db.execute(
            select(func.sum(BusBooking.total_amount)).where(
                BusBooking.payment_status == PaymentStatus.SUCCESS
            )
        )
        
        total_revenue = (
            (flight_revenue.scalar() or 0) +
            (hotel_revenue.scalar() or 0) +
            (bus_revenue.scalar() or 0)
        )
        
        # Today's statistics
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        bookings_today = await self.db.execute(
            select(func.count(FlightBooking.id)).where(
                FlightBooking.created_at >= today_start,
                FlightBooking.created_at <= today_end
            )
        )
        
        # Calculate averages and rates
        average_booking_value = total_revenue / total_bookings_count if total_bookings_count > 0 else 0
        
        return {
            "total_users": total_users_count,
            "active_users": active_users_count,
            "pending_agents": pending_agents_count,
            "approved_agents": approved_agents_count,
            "total_bookings": total_bookings_count,
            "total_revenue": round(total_revenue, 2),
            "average_booking_value": round(average_booking_value, 2),
            "bookings_today": bookings_today.scalar() or 0,
            "revenue_today": 0,  # TODO: Calculate today's revenue
            "revenue_this_month": 0,  # TODO: Calculate monthly revenue
            "cancellations_today": 0,  # TODO: Calculate today's cancellations
            "new_users_today": 0,  # TODO: Calculate today's new users
            "agent_applications_today": 0,  # TODO: Calculate today's agent applications
            "booking_success_rate": 95.0,  # TODO: Calculate actual success rate
            "cancellation_rate": 5.0,  # TODO: Calculate actual cancellation rate
            "payment_success_rate": 98.0,  # TODO: Calculate actual payment success rate
            "confirmed_bookings": 0,  # TODO: Calculate confirmed bookings
            "cancelled_bookings": 0,  # TODO: Calculate cancelled bookings
            "pending_bookings": 0,  # TODO: Calculate pending bookings
        }
    
    async def get_booking_analytics(self, analytics_request: BookingAnalyticsRequest) -> Dict[str, Any]:
        """
        Get booking analytics for specified period and filters.
        
        Args:
            analytics_request: Analytics request parameters
            
        Returns:
            Dict[str, Any]: Analytics data
        """
        # TODO: Implement detailed booking analytics
        # This would include time-series data, revenue trends, booking patterns, etc.
        
        return {
            "period": f"{analytics_request.start_date} to {analytics_request.end_date}",
            "total_bookings": 0,
            "total_revenue": 0.0,
            "average_booking_value": 0.0,
            "data_points": []
        }
