"""
Booking Services

This module contains business logic for booking operations:
- Flight booking creation and management
- Hotel booking creation and management
- Bus booking creation and management
- Payment processing and validation
- Booking status updates and cancellations
"""

import uuid
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from fastapi import HTTPException, status

from app.booking.models import (
    FlightBooking, HotelBooking, BusBooking, PassengerInfo,
    BookingStatus, PaymentStatus, PaymentMethod
)
from app.booking.schemas import (
    FlightBookingRequest, HotelBookingRequest, BusBookingRequest,
    CancelBookingRequest
)
from app.auth.models import User
from app.core.config import settings


class BookingService:
    """
    Base booking service for common booking functionality.
    
    This service provides shared functionality for all booking types
    including reference generation, status management, and common utilities.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference number."""
        return f"BK{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
    
    def _calculate_expiry_time(self, hours: int = 24) -> datetime:
        """Calculate booking expiry time."""
        return datetime.utcnow() + timedelta(hours=hours)
    
    async def _process_payment(self, payment_details: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """
        Process payment for booking.
        
        This is a mock implementation. In production, this would integrate
        with actual payment gateways like Razorpay, PayU, etc.
        
        Args:
            payment_details: Payment method and details
            amount: Amount to be charged
            
        Returns:
            Dict: Payment processing result
        """
        # Simulate payment processing delay
        await asyncio.sleep(random.uniform(1, 3))
        
        # Mock payment processing - 90% success rate
        import random
        is_successful = random.random() > 0.1
        
        if is_successful:
            return {
                "status": PaymentStatus.SUCCESS,
                "transaction_id": f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",
                "gateway_response": "Payment successful",
                "processed_at": datetime.utcnow()
            }
        else:
            return {
                "status": PaymentStatus.FAILED,
                "transaction_id": None,
                "gateway_response": "Payment declined",
                "processed_at": datetime.utcnow()
            }


class FlightBookingService(BookingService):
    """
    Flight booking service for managing flight reservations.
    
    This service handles flight booking creation, payment processing,
    and booking management operations.
    """
    
    async def create_flight_booking(
        self, 
        user: User, 
        booking_request: FlightBookingRequest,
        flight_data: Dict[str, Any],
        created_by_user: Optional[User] = None
    ) -> FlightBooking:
        """
        Create a new flight booking.
        
        Args:
            user: User making the booking
            booking_request: Flight booking request data
            flight_data: Flight details from search results
            created_by_user: Optional user who created this booking (for B2B tracking)
            
        Returns:
            FlightBooking: Created flight booking
            
        Raises:
            HTTPException: If booking creation fails
        """
        try:
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            
            # Calculate pricing
            base_fare = flight_data.get('price', 0)
            taxes = base_fare * 0.18  # 18% taxes
            total_amount = base_fare + taxes
            
            # Create flight booking
            flight_booking = FlightBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                created_by_id=created_by_user.id if created_by_user else user.id,
                offer_id=booking_request.offer_id,
                airline=flight_data.get('airline', ''),
                flight_number=flight_data.get('flight_number', ''),
                origin=flight_data.get('origin', ''),
                destination=flight_data.get('destination', ''),
                departure_time=datetime.fromisoformat(flight_data.get('departure_time', '')),
                arrival_time=datetime.fromisoformat(flight_data.get('arrival_time', '')),
                travel_class=flight_data.get('travel_class', 'economy'),
                passenger_count=len(booking_request.passengers),
                passenger_details=[passenger.dict() for passenger in booking_request.passengers],
                base_fare=base_fare,
                taxes=taxes,
                total_amount=total_amount,
                payment_method=booking_request.payment_details.method,
                special_requests=booking_request.special_requests,
                expires_at=self._calculate_expiry_time()
            )
            
            self.db.add(flight_booking)
            await self.db.flush()  # Get the ID
            
            # Process payment
            payment_result = await self._process_payment(
                booking_request.payment_details.dict(),
                total_amount
            )
            
            # Update booking with payment status
            flight_booking.payment_status = payment_result['status']
            flight_booking.status = BookingStatus.CONFIRMED if payment_result['status'] == PaymentStatus.SUCCESS else BookingStatus.PENDING
            
            # Generate confirmation number if payment successful
            if payment_result['status'] == PaymentStatus.SUCCESS:
                flight_booking.confirmation_number = f"FL{flight_booking.id:06d}"
            
            await self.db.commit()
            await self.db.refresh(flight_booking)
            
            return flight_booking
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Flight booking creation failed: {str(e)}"
            )
    
    async def get_flight_booking(self, booking_id: int, user_id: int) -> Optional[FlightBooking]:
        """
        Get flight booking by ID for a specific user.
        
        Args:
            booking_id: Booking ID
            user_id: User ID
            
        Returns:
            Optional[FlightBooking]: Flight booking if found and belongs to user
        """
        result = await self.db.execute(
            select(FlightBooking).where(
                and_(FlightBooking.id == booking_id, FlightBooking.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_flight_bookings(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 10,
        status_filter: Optional[BookingStatus] = None
    ) -> List[FlightBooking]:
        """
        Get user's flight bookings with pagination and filtering.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Optional status filter
            
        Returns:
            List[FlightBooking]: User's flight bookings
        """
        query = select(FlightBooking).where(FlightBooking.user_id == user_id)
        
        if status_filter:
            query = query.where(FlightBooking.status == status_filter)
        
        query = query.order_by(FlightBooking.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def cancel_flight_booking(
        self, 
        booking_id: int, 
        user_id: int, 
        cancel_request: CancelBookingRequest
    ) -> FlightBooking:
        """
        Cancel a flight booking.
        
        Args:
            booking_id: Booking ID to cancel
            user_id: User ID (for authorization)
            cancel_request: Cancellation details
            
        Returns:
            FlightBooking: Updated flight booking
            
        Raises:
            HTTPException: If booking not found or cannot be cancelled
        """
        booking = await self.get_flight_booking(booking_id, user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight booking not found"
            )
        
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled or refunded"
            )
        
        # Calculate refund amount (mock logic)
        refund_amount = 0
        if booking.status == BookingStatus.CONFIRMED:
            # Calculate refund based on cancellation policy
            hours_until_departure = (booking.departure_time - datetime.utcnow()).total_seconds() / 3600
            
            if hours_until_departure > 24:
                refund_amount = booking.total_amount * 0.8  # 80% refund
            elif hours_until_departure > 2:
                refund_amount = booking.total_amount * 0.5  # 50% refund
            else:
                refund_amount = 0  # No refund for last-minute cancellations
        
        # Update booking status
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = cancel_request.reason
        booking.refund_amount = refund_amount
        booking.payment_status = PaymentStatus.REFUNDED if refund_amount > 0 else PaymentStatus.FAILED
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return booking


class HotelBookingService(BookingService):
    """
    Hotel booking service for managing hotel reservations.
    
    This service handles hotel booking creation, payment processing,
    and booking management operations.
    """
    
    async def create_hotel_booking(
        self, 
        user: User, 
        booking_request: HotelBookingRequest,
        hotel_data: Dict[str, Any]
    ) -> HotelBooking:
        """
        Create a new hotel booking.
        
        Args:
            user: User making the booking
            booking_request: Hotel booking request data
            hotel_data: Hotel details from search results
            
        Returns:
            HotelBooking: Created hotel booking
            
        Raises:
            HTTPException: If booking creation fails
        """
        try:
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            
            # Calculate nights and pricing
            checkin_datetime = datetime.combine(booking_request.checkin_date, datetime.min.time())
            checkout_datetime = datetime.combine(booking_request.checkout_date, datetime.min.time())
            nights = (checkout_datetime - checkin_datetime).days
            
            room_rate = hotel_data.get('price_per_night', 0)
            total_amount = room_rate * nights * booking_request.rooms
            
            # Create hotel booking
            hotel_booking = HotelBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                hotel_id=booking_request.hotel_id,
                hotel_name=hotel_data.get('name', ''),
                hotel_address=hotel_data.get('address', ''),
                city=hotel_data.get('city', ''),
                checkin_date=checkin_datetime,
                checkout_date=checkout_datetime,
                nights=nights,
                rooms=booking_request.rooms,
                adults=booking_request.adults,
                children=booking_request.children,
                guest_details=booking_request.guest_details,
                room_rate=room_rate,
                total_amount=total_amount,
                payment_method=booking_request.payment_details.method,
                special_requests=booking_request.special_requests,
                cancellation_policy=hotel_data.get('cancellation_policy', 'Standard cancellation policy'),
                expires_at=self._calculate_expiry_time()
            )
            
            self.db.add(hotel_booking)
            await self.db.flush()  # Get the ID
            
            # Process payment
            payment_result = await self._process_payment(
                booking_request.payment_details.dict(),
                total_amount
            )
            
            # Update booking with payment status
            hotel_booking.payment_status = payment_result['status']
            hotel_booking.status = BookingStatus.CONFIRMED if payment_result['status'] == PaymentStatus.SUCCESS else BookingStatus.PENDING
            
            # Generate confirmation number if payment successful
            if payment_result['status'] == PaymentStatus.SUCCESS:
                hotel_booking.confirmation_number = f"HTL{hotel_booking.id:06d}"
            
            await self.db.commit()
            await self.db.refresh(hotel_booking)
            
            return hotel_booking
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Hotel booking creation failed: {str(e)}"
            )
    
    async def get_hotel_booking(self, booking_id: int, user_id: int) -> Optional[HotelBooking]:
        """Get hotel booking by ID for a specific user."""
        result = await self.db.execute(
            select(HotelBooking).where(
                and_(HotelBooking.id == booking_id, HotelBooking.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def cancel_hotel_booking(
        self, 
        booking_id: int, 
        user_id: int, 
        cancel_request: CancelBookingRequest
    ) -> HotelBooking:
        """Cancel a hotel booking."""
        booking = await self.get_hotel_booking(booking_id, user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hotel booking not found"
            )
        
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled or refunded"
            )
        
        # Calculate refund amount based on cancellation policy
        refund_amount = 0
        if booking.status == BookingStatus.CONFIRMED:
            hours_until_checkin = (booking.checkin_date - datetime.utcnow()).total_seconds() / 3600
            
            if "free" in booking.cancellation_policy.lower():
                refund_amount = booking.total_amount
            elif hours_until_checkin > 24:
                refund_amount = booking.total_amount * 0.8
            elif hours_until_checkin > 2:
                refund_amount = booking.total_amount * 0.5
            else:
                refund_amount = 0
        
        # Update booking status
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = cancel_request.reason
        booking.refund_amount = refund_amount
        booking.payment_status = PaymentStatus.REFUNDED if refund_amount > 0 else PaymentStatus.FAILED
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return booking
    
    async def get_user_hotel_bookings(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 10,
        status_filter: Optional[BookingStatus] = None
    ) -> List[HotelBooking]:
        """Get user's hotel bookings with pagination and filtering."""
        query = select(HotelBooking).where(HotelBooking.user_id == user_id)
        
        if status_filter:
            query = query.where(HotelBooking.status == status_filter)
        
        query = query.order_by(HotelBooking.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()


class BusBookingService(BookingService):
    """
    Bus booking service for managing bus reservations.
    
    This service handles bus booking creation, payment processing,
    and booking management operations.
    """
    
    async def create_bus_booking(
        self, 
        user: User, 
        booking_request: BusBookingRequest,
        bus_data: Dict[str, Any]
    ) -> BusBooking:
        """
        Create a new bus booking.
        
        Args:
            user: User making the booking
            booking_request: Bus booking request data
            bus_data: Bus details from search results
            
        Returns:
            BusBooking: Created bus booking
            
        Raises:
            HTTPException: If booking creation fails
        """
        try:
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            
            # Calculate pricing
            fare_per_passenger = bus_data.get('price', 0)
            total_amount = fare_per_passenger * booking_request.passengers
            
            # Create bus booking
            bus_booking = BusBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                bus_id=booking_request.bus_id,
                operator=bus_data.get('operator', ''),
                bus_type=bus_data.get('bus_type', ''),
                origin=bus_data.get('origin', ''),
                destination=bus_data.get('destination', ''),
                departure_time=datetime.fromisoformat(bus_data.get('departure_time', '')),
                arrival_time=datetime.fromisoformat(bus_data.get('arrival_time', '')),
                travel_date=datetime.combine(booking_request.travel_date, datetime.min.time()),
                passengers=booking_request.passengers,
                passenger_details=[passenger.dict() for passenger in booking_request.passenger_details],
                fare_per_passenger=fare_per_passenger,
                total_amount=total_amount,
                payment_method=booking_request.payment_details.method,
                boarding_point=booking_request.boarding_point,
                dropping_point=booking_request.dropping_point,
                special_requests=booking_request.special_requests,
                expires_at=self._calculate_expiry_time()
            )
            
            self.db.add(bus_booking)
            await self.db.flush()  # Get the ID
            
            # Process payment
            payment_result = await self._process_payment(
                booking_request.payment_details.dict(),
                total_amount
            )
            
            # Update booking with payment status
            bus_booking.payment_status = payment_result['status']
            bus_booking.status = BookingStatus.CONFIRMED if payment_result['status'] == PaymentStatus.SUCCESS else BookingStatus.PENDING
            
            # Generate confirmation number if payment successful
            if payment_result['status'] == PaymentStatus.SUCCESS:
                bus_booking.confirmation_number = f"BUS{bus_booking.id:06d}"
            
            await self.db.commit()
            await self.db.refresh(bus_booking)
            
            return bus_booking
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bus booking creation failed: {str(e)}"
            )
    
    async def get_bus_booking(self, booking_id: int, user_id: int) -> Optional[BusBooking]:
        """Get bus booking by ID for a specific user."""
        result = await self.db.execute(
            select(BusBooking).where(
                and_(BusBooking.id == booking_id, BusBooking.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def cancel_bus_booking(
        self, 
        booking_id: int, 
        user_id: int, 
        cancel_request: CancelBookingRequest
    ) -> BusBooking:
        """Cancel a bus booking."""
        booking = await self.get_bus_booking(booking_id, user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus booking not found"
            )
        
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled or refunded"
            )
        
        # Calculate refund amount
        refund_amount = 0
        if booking.status == BookingStatus.CONFIRMED:
            hours_until_departure = (booking.departure_time - datetime.utcnow()).total_seconds() / 3600
            
            if hours_until_departure > 24:
                refund_amount = booking.total_amount * 0.8
            elif hours_until_departure > 2:
                refund_amount = booking.total_amount * 0.5
            else:
                refund_amount = 0
        
        # Update booking status
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = cancel_request.reason
        booking.refund_amount = refund_amount
        booking.payment_status = PaymentStatus.REFUNDED if refund_amount > 0 else PaymentStatus.FAILED
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return booking
    
    async def get_user_bus_bookings(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 10,
        status_filter: Optional[BookingStatus] = None
    ) -> List[BusBooking]:
        """Get user's bus bookings with pagination and filtering."""
        query = select(BusBooking).where(BusBooking.user_id == user_id)
        
        if status_filter:
            query = query.where(BusBooking.status == status_filter)
        
        query = query.order_by(BusBooking.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
