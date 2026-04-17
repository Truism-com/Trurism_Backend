"""
Booking Services

This module contains business logic for booking operations:
- Flight booking creation and management
- Hotel booking creation and management
- Bus booking creation and management
- Payment processing and validation
- Booking status updates and cancellations
"""

import logging
import uuid
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from fastapi import HTTPException, logger, status

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

from app.services.email import email_service
logger = logging.getLogger(__name__)


class BaseBookingService:
    """
    Base booking service for common booking functionality.
    
    This service provides shared functionality for all booking types
    including reference generation, status management, and common utilities.
    """
    
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference number."""
        return f"BK{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
    
    def _calculate_expiry_time(self, hours: int = 24) -> datetime:
        """Calculate booking expiry time."""
        return datetime.utcnow() + timedelta(hours=hours)
    
    async def _process_payment(self, payment_details: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """
        Process payment for booking.
        
        This is a mock implementation without artificial delay.
        """
        # Mock payment processing - 95% success rate for production baseline
        is_successful = random.random() > 0.05
        
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


from app.booking.payment_processor import BookingPaymentProcessor, PaymentMode

class FlightBookingError(Exception):
    """Exception for flight booking errors."""
    pass


class FlightNotAvailableError(FlightBookingError):
    """Selected flight is not available."""
    pass


class FlightBookingService(BaseBookingService):
    """
    Flight booking service for managing flight reservations.
    
    This service handles flight booking creation, payment processing,
    and booking management operations with full tenant isolation.
    """
    
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, tenant_id)
        self.payment_processor = BookingPaymentProcessor(db)

    def _generate_pnr(self) -> str:
        """Generate PNR (Passenger Name Record)."""
        import string
        import random
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=6))
    
    async def create_flight_booking(
        self, 
        user: User, 
        booking_request: FlightBookingRequest,
        flight_data: Dict[str, Any],
        created_by_user: Optional[User] = None,
        payment_mode: PaymentMode = PaymentMode.WALLET,
        razorpay_details: Optional[Dict[str, Any]] = None
    ) -> FlightBooking:
        """
        Create a new flight booking with real payment integration.
        """
        try:
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            
            # Calculate pricing
            base_fare = flight_data.get('price', 0)
            taxes = round(base_fare * 0.18, 2)  # 18% taxes
            total_amount = round(base_fare + taxes, 2)
            
            # Create flight booking record
            flight_booking = FlightBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                tenant_id=self.tenant_id,
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
                payment_method=payment_mode.value,
                special_requests=booking_request.special_requests,
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                expires_at=self._calculate_expiry_time()
            )
            
            self.db.add(flight_booking)
            await self.db.flush()
            
            # Process payment using unified processor
            payment_result = await self.payment_processor.process_payment(
                user_id=user.id,
                amount=total_amount,
                payment_mode=payment_mode,
                booking_id=flight_booking.id,
                booking_type="flight",
                razorpay_payment_id=razorpay_details.get("payment_id") if razorpay_details else None,
                razorpay_order_id=razorpay_details.get("order_id") if razorpay_details else None,
                razorpay_signature=razorpay_details.get("signature") if razorpay_details else None,
                description=f"Flight booking {booking_reference}"
            )
            
            # Update booking based on payment result
            if payment_result['status'] == PaymentStatus.SUCCESS:
                flight_booking.payment_status = PaymentStatus.SUCCESS
                flight_booking.status = BookingStatus.CONFIRMED
                flight_booking.confirmation_number = f"FL{flight_booking.id:06d}"
                flight_booking.pnr = self._generate_pnr()
            else:
                flight_booking.payment_status = PaymentStatus.FAILED
                flight_booking.status = BookingStatus.PENDING
            
            # if BookingStatus.CONFIRMED:
            #   send_confirmation_email()
                
                
            
            await self.db.commit()
            await self.db.refresh(flight_booking)

            # Send booking confirmation email (non-blocking)
            if flight_booking.status == BookingStatus.CONFIRMED:
                try:
                    await email_service.send_booking_confirmation(
                        to_email=user.email,
                        booking_reference=booking_reference,
                        service_type="Flight",
                        travel_date=str(flight_booking.departure_time.date()),
                        amount=flight_booking.total_amount,
                        passenger_name=user.name,
                    )
                    logger.info(f"Flight booking email sent: {user.email}")
                except Exception as email_err:
                    logger.warning(f"Flight booking email failed: {email_err}")

            return flight_booking
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Flight booking creation failed: {str(e)}"
            )
    
    async def get_flight_booking(self, booking_id: int, user_id: int) -> Optional[FlightBooking]:
        """Get flight booking with tenant isolation."""
        query = select(FlightBooking).where(
            and_(FlightBooking.id == booking_id, FlightBooking.user_id == user_id)
        )
        if self.tenant_id:
            query = query.where(FlightBooking.tenant_id == self.tenant_id)
            
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_flight_bookings(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 10,
        status_filter: Optional[BookingStatus] = None
    ) -> List[FlightBooking]:
        """Get user flight bookings with tenant isolation."""
        query = select(FlightBooking).where(FlightBooking.user_id == user_id)
        
        if self.tenant_id:
            query = query.where(FlightBooking.tenant_id == self.tenant_id)
            
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
        """Cancel flight booking and process refund."""
        booking = await self.get_flight_booking(booking_id, user_id)
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise HTTPException(status_code=400, detail="Already cancelled")
        
        # Calculate refund (simplified)
        refund_amount = booking.total_amount * 0.8 if (booking.departure_time - datetime.utcnow()).total_seconds() > 86400 else 0
        
        # Process refund via processor
        if refund_amount > 0:
            await self.payment_processor.process_refund(
                user_id=user_id,
                amount=refund_amount,
                booking_id=booking_id,
                booking_type="flight",
                original_payment_method=booking.payment_method,
                reason=cancel_request.reason
            )
        
        booking.status = BookingStatus.CANCELLED
        booking.refund_amount = refund_amount
        booking.payment_status = PaymentStatus.REFUNDED if refund_amount > 0 else PaymentStatus.FAILED
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking


class HotelBookingService(BaseBookingService):
    """
    Hotel booking service for managing hotel reservations.
    """
    
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, tenant_id)
        self.payment_processor = BookingPaymentProcessor(db)

    async def create_hotel_booking(
        self, 
        user: User, 
        booking_request: HotelBookingRequest,
        hotel_data: Dict[str, Any],
        created_by_user: Optional[User] = None,
        payment_mode: PaymentMode = PaymentMode.WALLET
    ) -> HotelBooking:
        """Create hotel booking with tenant isolation."""
        try:
            booking_reference = self._generate_booking_reference()
            
            checkin_datetime = datetime.combine(booking_request.checkin_date, datetime.min.time())
            checkout_datetime = datetime.combine(booking_request.checkout_date, datetime.min.time())
            nights = (checkout_datetime - checkin_datetime).days
            
            room_rate = hotel_data.get('price_per_night', 0)
            total_amount = round(room_rate * nights * booking_request.rooms, 2)
            
            hotel_booking = HotelBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                tenant_id=self.tenant_id,
                created_by_id=created_by_user.id if created_by_user else user.id,
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
                payment_method=payment_mode.value,
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                expires_at=self._calculate_expiry_time()
            )
            
            self.db.add(hotel_booking)
            await self.db.flush()
            
            # Process payment
            payment_result = await self.payment_processor.process_payment(
                user_id=user.id,
                amount=total_amount,
                payment_mode=payment_mode,
                booking_id=hotel_booking.id,
                booking_type="hotel"
            )
            
            if payment_result['status'] == PaymentStatus.SUCCESS:
                hotel_booking.payment_status = PaymentStatus.SUCCESS
                hotel_booking.status = BookingStatus.CONFIRMED
                hotel_booking.confirmation_number = f"HTL{hotel_booking.id:06d}"
            
            await self.db.commit()
            await self.db.refresh(hotel_booking)

            # Send booking confirmation email (non-blocking)
            if hotel_booking.status == BookingStatus.CONFIRMED:
                try:
                    await email_service.send_booking_confirmation(
                        to_email=user.email,
                        booking_reference=booking_reference,
                        service_type="Hotel",
                        travel_date=str(hotel_booking.checkin_date.date()),
                        amount=hotel_booking.total_amount,
                        passenger_name=user.name,
                    )
                    logger.info(f"hotel booking email sent:{user.email}")
                except Exception as email_err:
                    logger.warning(f"Hotel booking email failed: {email_err}")

            return hotel_booking
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_hotel_booking(self, booking_id: int, user_id: int) -> Optional[HotelBooking]:
        """Get hotel booking with tenant isolation."""
        query = select(HotelBooking).where(
            and_(HotelBooking.id == booking_id, HotelBooking.user_id == user_id)
        )
        if self.tenant_id:
            query = query.where(HotelBooking.tenant_id == self.tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_hotel_bookings(self, user_id: int, skip: int = 0, limit: int = 10, status_filter: Optional[BookingStatus] = None) -> List[HotelBooking]:
        """Get user hotel bookings with tenant isolation."""
        query = select(HotelBooking).where(HotelBooking.user_id == user_id)
        if self.tenant_id:
            query = query.where(HotelBooking.tenant_id == self.tenant_id)
        if status_filter:
            query = query.where(HotelBooking.status == status_filter)
        query = query.order_by(HotelBooking.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()


class BusBookingError(Exception):
    """Exception for bus booking errors."""
    pass


class SeatNotAvailableError(BusBookingError):
    """Selected seats are not available."""
    pass


class BusBookingService(BaseBookingService):
    """
    Bus booking service for managing bus reservations.
    """
    
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, tenant_id)
        self.payment_processor = BookingPaymentProcessor(db)

    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number."""
        import uuid
        return f"TKT{uuid.uuid4().hex[:10].upper()}"

    async def create_bus_booking(
        self, 
        user: User, 
        booking_request: BusBookingRequest,
        bus_data: Dict[str, Any],
        created_by_user: Optional[User] = None,
        payment_mode: PaymentMode = PaymentMode.WALLET
    ) -> BusBooking:
        """Create bus booking with tenant isolation."""
        try:
            booking_reference = self._generate_booking_reference()
            
            fare_per_passenger = bus_data.get('price', 0)
            total_amount = round(fare_per_passenger * booking_request.passengers, 2)
            
            bus_booking = BusBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                tenant_id=self.tenant_id,
                created_by_id=created_by_user.id if created_by_user else user.id,
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
                payment_method=payment_mode.value,
                boarding_point=booking_request.boarding_point,
                dropping_point=booking_request.dropping_point,
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                expires_at=self._calculate_expiry_time()
            )
            
            self.db.add(bus_booking)
            await self.db.flush()
            
            # Process payment
            payment_result = await self.payment_processor.process_payment(
                user_id=user.id,
                amount=total_amount,
                payment_mode=payment_mode,
                booking_id=bus_booking.id,
                booking_type="bus"
            )
            
            if payment_result['status'] == PaymentStatus.SUCCESS:
                bus_booking.payment_status = PaymentStatus.SUCCESS
                bus_booking.status = BookingStatus.CONFIRMED
                bus_booking.ticket_number = self._generate_ticket_number()
            
            await self.db.commit()
            await self.db.refresh(bus_booking)

            # Send booking confirmation email (non-blocking)
            if bus_booking.status == BookingStatus.CONFIRMED:
                try:
                    await email_service.send_booking_confirmation(
                        to_email=user.email,
                        booking_reference=booking_reference,
                        service_type="Bus",
                        travel_date=str(bus_booking.travel_date.date()),
                        amount=bus_booking.total_amount,
                        passenger_name=user.name,
                    )
                    logger.info(f"Bus booking confirmation email sent: {user.email} ")
                except Exception as email_err:
                    logger.warning(f"Bus booking email failed: {email_err}")

            return bus_booking
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_bus_booking(self, booking_id: int, user_id: int) -> Optional[BusBooking]:
        """Get bus booking with tenant isolation."""
        query = select(BusBooking).where(
            and_(BusBooking.id == booking_id, BusBooking.user_id == user_id)
        )
        if self.tenant_id:
            query = query.where(BusBooking.tenant_id == self.tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_bus_bookings(self, user_id: int, skip: int = 0, limit: int = 10, status_filter: Optional[BookingStatus] = None) -> List[BusBooking]:
        """Get user bus bookings with tenant isolation."""
        query = select(BusBooking).where(BusBooking.user_id == user_id)
        if self.tenant_id:
            query = query.where(BusBooking.tenant_id == self.tenant_id)
        if status_filter:
            query = query.where(BusBooking.status == status_filter)
        query = query.order_by(BusBooking.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
