"""
Enhanced Bus Booking Service

This module provides comprehensive bus booking functionality:
- Seat selection and layout management
- Real-time availability checks
- Integrated payment processing (wallet, Razorpay, credit)
- Booking confirmation and ticketing
- Cancellation with refund handling
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from fastapi import HTTPException, status

from app.booking.models import (
    BusBooking, BookingStatus, PaymentStatus, PaymentMethod
)
from app.booking.payment_processor import (
    BookingPaymentProcessor, PaymentMode, PaymentProcessingError
)
from app.auth.models import User, UserRole
from app.core.config import settings

logger = logging.getLogger(__name__)


class BusBookingError(Exception):
    """Exception for bus booking errors."""
    pass


class SeatNotAvailableError(BusBookingError):
    """Selected seats are not available."""
    pass


class BusBookingService:
    """
    Enhanced bus booking service with real payment integration.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_processor = BookingPaymentProcessor(db)
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference."""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"BUS{timestamp}{unique_id}"
    
    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number."""
        import uuid
        return f"TKT{uuid.uuid4().hex[:10].upper()}"
    
    # =========================================================================
    # Seat Selection
    # =========================================================================
    
    async def get_seat_layout(
        self,
        bus_id: str,
        travel_date: datetime
    ) -> Dict[str, Any]:
        """
        Get bus seat layout with availability.
        
        Args:
            bus_id: Bus ID
            travel_date: Travel date
            
        Returns:
            Dict with seat layout and availability
        """
        # In production, call external API
        # For now, generate mock seat layout
        return await self._generate_mock_seat_layout(bus_id)
    
    async def _generate_mock_seat_layout(self, bus_id: str) -> Dict[str, Any]:
        """Generate mock seat layout for development."""
        # Standard sleeper bus layout (2x1 configuration)
        lower_deck = []
        upper_deck = []
        
        # Lower deck - rows 1-10
        for row in range(1, 11):
            # Left side (2 seats)
            for seat in ["A", "B"]:
                seat_number = f"L{row}{seat}"
                lower_deck.append({
                    "seat_number": seat_number,
                    "deck": "lower",
                    "row": row,
                    "column": seat,
                    "type": "sleeper",
                    "is_available": random.random() > 0.3,
                    "price": 1200 + (row * 50),
                    "is_window": seat == "A",
                    "is_aisle": seat == "B"
                })
            
            # Right side (1 seat - single sleeper)
            seat_number = f"L{row}C"
            lower_deck.append({
                "seat_number": seat_number,
                "deck": "lower",
                "row": row,
                "column": "C",
                "type": "sleeper",
                "is_available": random.random() > 0.3,
                "price": 1400 + (row * 50),  # Premium for single sleeper
                "is_window": True,
                "is_aisle": False
            })
        
        # Upper deck - rows 1-10
        for row in range(1, 11):
            for seat in ["A", "B"]:
                seat_number = f"U{row}{seat}"
                upper_deck.append({
                    "seat_number": seat_number,
                    "deck": "upper",
                    "row": row,
                    "column": seat,
                    "type": "sleeper",
                    "is_available": random.random() > 0.25,
                    "price": 1000 + (row * 40),  # Upper deck slightly cheaper
                    "is_window": seat == "A",
                    "is_aisle": seat == "B"
                })
            
            seat_number = f"U{row}C"
            upper_deck.append({
                "seat_number": seat_number,
                "deck": "upper",
                "row": row,
                "column": "C",
                "type": "sleeper",
                "is_available": random.random() > 0.25,
                "price": 1200 + (row * 40),
                "is_window": True,
                "is_aisle": False
            })
        
        total_seats = len(lower_deck) + len(upper_deck)
        available_seats = sum(1 for s in lower_deck + upper_deck if s["is_available"])
        
        return {
            "bus_id": bus_id,
            "total_seats": total_seats,
            "available_seats": available_seats,
            "layout": {
                "lower_deck": lower_deck,
                "upper_deck": upper_deck
            },
            "amenities": ["AC", "Blanket", "Water Bottle", "Charging Point"],
            "bus_type": "AC Sleeper"
        }
    
    async def get_boarding_points(
        self,
        bus_id: str,
        origin: str
    ) -> List[Dict[str, Any]]:
        """Get boarding points for a bus."""
        # Mock boarding points
        return [
            {
                "id": "BP001",
                "name": f"{origin} Central Bus Stand",
                "address": f"Main Road, {origin}",
                "time": "21:00",
                "landmark": "Near Railway Station"
            },
            {
                "id": "BP002",
                "name": f"{origin} Highway Stop",
                "address": f"NH-44, {origin}",
                "time": "21:30",
                "landmark": "Near Petrol Pump"
            },
            {
                "id": "BP003",
                "name": f"{origin} City Point",
                "address": f"City Center, {origin}",
                "time": "20:45",
                "landmark": "Near City Mall"
            }
        ]
    
    async def get_dropping_points(
        self,
        bus_id: str,
        destination: str
    ) -> List[Dict[str, Any]]:
        """Get dropping points for a bus."""
        # Mock dropping points
        return [
            {
                "id": "DP001",
                "name": f"{destination} Bus Terminal",
                "address": f"Main Bus Stand, {destination}",
                "time": "06:00",
                "landmark": "Near Metro Station"
            },
            {
                "id": "DP002",
                "name": f"{destination} Highway Junction",
                "address": f"NH-44, {destination}",
                "time": "05:30",
                "landmark": "Near Toll Plaza"
            }
        ]
    
    # =========================================================================
    # Booking Operations
    # =========================================================================
    
    async def create_booking(
        self,
        user: User,
        bus_id: str,
        bus_data: Dict[str, Any],
        seats: List[str],
        passengers: List[Dict[str, Any]],
        boarding_point: Dict[str, Any],
        dropping_point: Dict[str, Any],
        payment_mode: PaymentMode,
        contact_info: Dict[str, Any],
        razorpay_payment_id: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        razorpay_signature: Optional[str] = None,
        wallet_amount: Optional[float] = None
    ) -> BusBooking:
        """
        Create a new bus booking with payment processing.
        
        Args:
            user: User making the booking
            bus_id: Bus ID
            bus_data: Bus details from search
            seats: List of selected seat numbers
            passengers: Passenger details
            boarding_point: Boarding point details
            dropping_point: Dropping point details
            payment_mode: Payment method
            contact_info: Contact information
            razorpay_*: Razorpay payment details (if applicable)
            wallet_amount: Amount to use from wallet (for split payments)
            
        Returns:
            Created BusBooking
        """
        try:
            # Verify seat availability
            await self._verify_seat_availability(bus_id, seats, bus_data.get("travel_date"))
            
            # Calculate pricing
            pricing = self._calculate_pricing(seats, bus_data)
            
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            
            # Create booking record (pending payment)
            bus_booking = BusBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                bus_id=bus_id,
                operator=bus_data.get("operator", ""),
                bus_type=bus_data.get("bus_type", ""),
                origin=bus_data.get("origin", ""),
                destination=bus_data.get("destination", ""),
                departure_time=datetime.fromisoformat(bus_data.get("departure_time", "")),
                arrival_time=datetime.fromisoformat(bus_data.get("arrival_time", "")),
                seat_numbers=seats,
                passenger_count=len(passengers),
                passenger_details=passengers,
                boarding_point=boarding_point.get("name", ""),
                boarding_time=boarding_point.get("time", ""),
                dropping_point=dropping_point.get("name", ""),
                dropping_time=dropping_point.get("time", ""),
                base_fare=pricing["base_fare"],
                taxes=pricing["taxes"],
                convenience_fee=pricing["convenience_fee"],
                total_amount=pricing["total_amount"],
                payment_method=self._get_payment_method(payment_mode),
                contact_email=contact_info.get("email", ""),
                contact_phone=contact_info.get("phone", ""),
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            
            self.db.add(bus_booking)
            await self.db.flush()
            
            # Process payment
            payment_result = await self.payment_processor.process_payment(
                user_id=user.id,
                amount=pricing["total_amount"],
                payment_mode=payment_mode,
                booking_id=bus_booking.id,
                booking_type="bus",
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
                use_wallet_amount=wallet_amount,
                description=f"Bus booking {booking_reference}"
            )
            
            # Update booking based on payment result
            if payment_result["status"] == PaymentStatus.SUCCESS:
                bus_booking.status = BookingStatus.CONFIRMED
                bus_booking.payment_status = PaymentStatus.SUCCESS
                bus_booking.ticket_number = self._generate_ticket_number()
                bus_booking.confirmed_at = datetime.utcnow()
                
                logger.info(f"Bus booking {booking_reference} confirmed")
            else:
                bus_booking.status = BookingStatus.PENDING
                bus_booking.payment_status = PaymentStatus.FAILED
                bus_booking.payment_failure_reason = payment_result.get("error", "Payment failed")
                
                logger.warning(f"Bus booking {booking_reference} payment failed: {payment_result.get('error')}")
            
            await self.db.commit()
            await self.db.refresh(bus_booking)
            
            return bus_booking
            
        except SeatNotAvailableError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        except PaymentProcessingError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Payment failed: {str(e)}"
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Bus booking creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Booking creation failed: {str(e)}"
            )
    
    async def _verify_seat_availability(
        self,
        bus_id: str,
        seats: List[str],
        travel_date: Optional[str]
    ) -> bool:
        """Verify selected seats are available."""
        # In production, call external API to verify
        # For now, check against mock data
        seat_layout = await self.get_seat_layout(bus_id, datetime.utcnow())
        
        all_seats = (
            seat_layout["layout"]["lower_deck"] + 
            seat_layout["layout"]["upper_deck"]
        )
        
        for seat_number in seats:
            seat_info = next(
                (s for s in all_seats if s["seat_number"] == seat_number),
                None
            )
            
            if not seat_info:
                raise SeatNotAvailableError(f"Seat {seat_number} does not exist")
            
            # For demo, we'll allow booking even if mock shows unavailable
            # In production, check seat_info["is_available"]
        
        return True
    
    def _calculate_pricing(
        self,
        seats: List[str],
        bus_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate booking pricing."""
        base_price_per_seat = bus_data.get("price", 1000)
        num_seats = len(seats)
        
        base_fare = base_price_per_seat * num_seats
        taxes = round(base_fare * 0.05, 2)  # 5% GST
        convenience_fee = round(base_fare * 0.02, 2)  # 2% convenience fee
        total_amount = round(base_fare + taxes + convenience_fee, 2)
        
        return {
            "base_fare": base_fare,
            "taxes": taxes,
            "convenience_fee": convenience_fee,
            "total_amount": total_amount
        }
    
    def _get_payment_method(self, payment_mode: PaymentMode) -> PaymentMethod:
        """Convert payment mode to payment method."""
        if payment_mode == PaymentMode.WALLET:
            return PaymentMethod.WALLET
        elif payment_mode == PaymentMode.AGENT_CREDIT:
            return PaymentMethod.AGENT_CREDIT
        else:
            return PaymentMethod.CARD  # Default for Razorpay
    
    # =========================================================================
    # Booking Management
    # =========================================================================
    
    async def get_booking(self, booking_id: int, user_id: int) -> Optional[BusBooking]:
        """Get bus booking by ID."""
        result = await self.db.execute(
            select(BusBooking).where(
                and_(BusBooking.id == booking_id, BusBooking.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_booking_by_reference(self, booking_reference: str) -> Optional[BusBooking]:
        """Get bus booking by reference number."""
        result = await self.db.execute(
            select(BusBooking).where(BusBooking.booking_reference == booking_reference)
        )
        return result.scalar_one_or_none()
    
    async def get_user_bookings(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        status_filter: Optional[BookingStatus] = None
    ) -> List[BusBooking]:
        """Get user's bus bookings."""
        query = select(BusBooking).where(BusBooking.user_id == user_id)
        
        if status_filter:
            query = query.where(BusBooking.status == status_filter)
        
        query = query.order_by(BusBooking.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def cancel_booking(
        self,
        booking_id: int,
        user_id: int,
        reason: str
    ) -> BusBooking:
        """
        Cancel a bus booking with refund processing.
        
        Args:
            booking_id: Booking ID
            user_id: User ID
            reason: Cancellation reason
            
        Returns:
            Updated BusBooking
        """
        booking = await self.get_booking(booking_id, user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled"
            )
        
        # Calculate refund based on cancellation policy
        refund_amount = self._calculate_refund(booking)
        
        # Process refund
        if refund_amount > 0:
            refund_result = await self.payment_processor.process_refund(
                user_id=user_id,
                amount=refund_amount,
                booking_id=booking_id,
                booking_type="bus",
                original_payment_method=booking.payment_method,
                reason=reason
            )
            
            booking.refund_amount = refund_amount
            booking.refund_status = refund_result.get("status")
        
        # Update booking
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason
        booking.cancelled_at = datetime.utcnow()
        
        if refund_amount > 0:
            booking.payment_status = PaymentStatus.REFUNDED
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Bus booking {booking.booking_reference} cancelled. Refund: {refund_amount}")
        
        return booking
    
    def _calculate_refund(self, booking: BusBooking) -> float:
        """Calculate refund amount based on cancellation policy."""
        if booking.status != BookingStatus.CONFIRMED:
            return 0
        
        hours_until_departure = (booking.departure_time - datetime.utcnow()).total_seconds() / 3600
        
        if hours_until_departure > 48:
            # Full refund minus cancellation fee
            return round(booking.total_amount * 0.9, 2)
        elif hours_until_departure > 24:
            # 75% refund
            return round(booking.total_amount * 0.75, 2)
        elif hours_until_departure > 6:
            # 50% refund
            return round(booking.total_amount * 0.5, 2)
        elif hours_until_departure > 0:
            # 25% refund
            return round(booking.total_amount * 0.25, 2)
        else:
            # No refund after departure
            return 0
    
    # =========================================================================
    # Payment Order Creation
    # =========================================================================
    
    async def create_payment_order(
        self,
        user_id: int,
        bus_data: Dict[str, Any],
        seats: List[str]
    ) -> Dict[str, Any]:
        """
        Create a Razorpay payment order for bus booking.
        
        Args:
            user_id: User ID
            bus_data: Bus details
            seats: Selected seats
            
        Returns:
            Razorpay order details
        """
        pricing = self._calculate_pricing(seats, bus_data)
        
        # Create a temporary booking ID for reference
        temp_booking_id = f"TEMP_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        order = await self.payment_processor.create_payment_order(
            amount=pricing["total_amount"],
            booking_id=0,  # Will be updated after booking creation
            booking_type="bus"
        )
        
        return {
            **order,
            "pricing": pricing,
            "seats": seats,
            "bus_id": bus_data.get("bus_id")
        }
    
    async def check_payment_eligibility(
        self,
        user_id: int,
        bus_data: Dict[str, Any],
        seats: List[str],
        payment_mode: PaymentMode
    ) -> Dict[str, Any]:
        """Check if user is eligible for the payment mode."""
        pricing = self._calculate_pricing(seats, bus_data)
        
        return await self.payment_processor.check_payment_eligibility(
            user_id=user_id,
            amount=pricing["total_amount"],
            payment_mode=payment_mode
        )
