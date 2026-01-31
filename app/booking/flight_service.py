"""
Enhanced Flight Booking Service

This module provides comprehensive flight booking functionality:
- Flight search and offer management
- Multi-passenger booking
- Integrated payment processing (wallet, Razorpay, credit)
- Booking confirmation and PNR management
- Cancellation with refund handling
- Amendment and rebooking support
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from fastapi import HTTPException, status

from app.booking.models import (
    FlightBooking, PassengerInfo, BookingStatus, PaymentStatus, PaymentMethod
)
from app.booking.payment_processor import (
    BookingPaymentProcessor, PaymentMode, PaymentProcessingError
)
from app.auth.models import User, UserRole
from app.core.config import settings

logger = logging.getLogger(__name__)


class FlightBookingError(Exception):
    """Exception for flight booking errors."""
    pass


class FlightNotAvailableError(FlightBookingError):
    """Selected flight is not available."""
    pass


class EnhancedFlightBookingService:
    """
    Enhanced flight booking service with real payment integration.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_processor = BookingPaymentProcessor(db)
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"FL{timestamp}{unique_id}"
    
    def _generate_pnr(self) -> str:
        """Generate PNR (Passenger Name Record)."""
        import string
        import random
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=6))
    
    # =========================================================================
    # Flight Search & Offer Management
    # =========================================================================
    
    async def get_flight_details(
        self,
        offer_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed flight information for an offer.
        
        Args:
            offer_id: Flight offer ID from search results
            
        Returns:
            Dict with flight details
        """
        # In production, call external API
        # For now, return mock flight details
        return await self._generate_mock_flight_details(offer_id)
    
    async def _generate_mock_flight_details(self, offer_id: str) -> Dict[str, Any]:
        """Generate mock flight details."""
        import random
        
        airlines = [
            ("AI", "Air India", "₹"),
            ("6E", "IndiGo", "₹"),
            ("SG", "SpiceJet", "₹"),
            ("G8", "GoAir", "₹"),
            ("UK", "Vistara", "₹")
        ]
        
        airline_code, airline_name, currency = random.choice(airlines)
        
        return {
            "offer_id": offer_id,
            "airline": airline_name,
            "airline_code": airline_code,
            "flight_number": f"{airline_code}{random.randint(100, 999)}",
            "origin": "DEL",
            "destination": "BOM",
            "departure_time": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "arrival_time": (datetime.utcnow() + timedelta(days=7, hours=2)).isoformat(),
            "duration": "2h 15m",
            "travel_class": "ECONOMY",
            "stops": 0,
            "aircraft_type": "Boeing 737-800",
            "baggage": {
                "cabin": "7 kg",
                "checked": "15 kg"
            },
            "meal_included": True,
            "price": random.randint(3500, 8000),
            "currency": currency,
            "refundable": random.random() > 0.5,
            "fare_rules": {
                "cancellation_fee": "₹3000 per passenger",
                "date_change_fee": "₹2500 per passenger",
                "no_show_fee": "100% fare"
            },
            "available_seats": random.randint(5, 50)
        }
    
    async def validate_offer(self, offer_id: str) -> Dict[str, Any]:
        """
        Validate a flight offer is still available.
        
        Args:
            offer_id: Flight offer ID
            
        Returns:
            Validation result with current pricing
        """
        flight_details = await self.get_flight_details(offer_id)
        
        if flight_details.get("available_seats", 0) < 1:
            raise FlightNotAvailableError("Flight is no longer available")
        
        return {
            "valid": True,
            "current_price": flight_details["price"],
            "available_seats": flight_details["available_seats"],
            "price_changed": False  # In production, compare with original
        }
    
    # =========================================================================
    # Booking Operations
    # =========================================================================
    
    async def create_booking(
        self,
        user: User,
        offer_id: str,
        flight_data: Dict[str, Any],
        passengers: List[Dict[str, Any]],
        payment_mode: PaymentMode,
        contact_info: Dict[str, Any],
        special_requests: Optional[str] = None,
        razorpay_payment_id: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        razorpay_signature: Optional[str] = None,
        wallet_amount: Optional[float] = None,
        created_by_user: Optional[User] = None
    ) -> FlightBooking:
        """
        Create a new flight booking with payment processing.
        
        Args:
            user: User making the booking
            offer_id: Flight offer ID
            flight_data: Flight details from search
            passengers: List of passenger details
            payment_mode: Payment method
            contact_info: Contact information
            special_requests: Special requests
            razorpay_*: Razorpay payment details (if applicable)
            wallet_amount: Amount to use from wallet (for split payments)
            created_by_user: Agent who created booking (for B2B)
            
        Returns:
            Created FlightBooking
        """
        try:
            # Validate offer
            await self.validate_offer(offer_id)
            
            # Calculate pricing
            pricing = self._calculate_pricing(passengers, flight_data)
            
            # Generate booking reference
            booking_reference = self._generate_booking_reference()
            
            # Create booking record (pending payment)
            flight_booking = FlightBooking(
                booking_reference=booking_reference,
                user_id=user.id,
                created_by_id=created_by_user.id if created_by_user else user.id,
                offer_id=offer_id,
                airline=flight_data.get("airline", ""),
                flight_number=flight_data.get("flight_number", ""),
                origin=flight_data.get("origin", ""),
                destination=flight_data.get("destination", ""),
                departure_time=datetime.fromisoformat(flight_data.get("departure_time", "")),
                arrival_time=datetime.fromisoformat(flight_data.get("arrival_time", "")),
                travel_class=flight_data.get("travel_class", "ECONOMY"),
                passenger_count=len(passengers),
                passenger_details=passengers,
                base_fare=pricing["base_fare"],
                taxes=pricing["taxes"],
                convenience_fee=pricing.get("convenience_fee", 0),
                total_amount=pricing["total_amount"],
                payment_method=self._get_payment_method(payment_mode),
                contact_email=contact_info.get("email", ""),
                contact_phone=contact_info.get("phone", ""),
                special_requests=special_requests,
                status=BookingStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(minutes=20)
            )
            
            self.db.add(flight_booking)
            await self.db.flush()
            
            # Process payment
            payment_result = await self.payment_processor.process_payment(
                user_id=user.id,
                amount=pricing["total_amount"],
                payment_mode=payment_mode,
                booking_id=flight_booking.id,
                booking_type="flight",
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
                use_wallet_amount=wallet_amount,
                description=f"Flight booking {booking_reference}"
            )
            
            # Update booking based on payment result
            if payment_result["status"] == PaymentStatus.SUCCESS:
                flight_booking.status = BookingStatus.CONFIRMED
                flight_booking.payment_status = PaymentStatus.SUCCESS
                flight_booking.confirmation_number = f"CONF{flight_booking.id:06d}"
                flight_booking.pnr = self._generate_pnr()
                
                # In production, call external API to confirm booking
                # external_booking = await self._confirm_with_airline(flight_booking)
                
                logger.info(f"Flight booking {booking_reference} confirmed, PNR: {flight_booking.pnr}")
            else:
                flight_booking.status = BookingStatus.PENDING
                flight_booking.payment_status = PaymentStatus.FAILED
                
                logger.warning(f"Flight booking {booking_reference} payment failed")
            
            await self.db.commit()
            await self.db.refresh(flight_booking)
            
            return flight_booking
            
        except FlightNotAvailableError as e:
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
            logger.error(f"Flight booking creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Booking creation failed: {str(e)}"
            )
    
    def _calculate_pricing(
        self,
        passengers: List[Dict[str, Any]],
        flight_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate booking pricing based on passenger types."""
        base_price = flight_data.get("price", 0)
        
        adult_count = sum(1 for p in passengers if p.get("type", "ADT") == "ADT")
        child_count = sum(1 for p in passengers if p.get("type") == "CHD")
        infant_count = sum(1 for p in passengers if p.get("type") == "INF")
        
        # Pricing calculation
        adult_fare = base_price * adult_count
        child_fare = base_price * 0.75 * child_count  # 75% of adult fare
        infant_fare = base_price * 0.1 * infant_count  # 10% of adult fare
        
        base_fare = round(adult_fare + child_fare + infant_fare, 2)
        taxes = round(base_fare * 0.12, 2)  # 12% taxes
        convenience_fee = round(base_fare * 0.02, 2)  # 2% convenience fee
        total_amount = round(base_fare + taxes + convenience_fee, 2)
        
        return {
            "base_fare": base_fare,
            "taxes": taxes,
            "convenience_fee": convenience_fee,
            "total_amount": total_amount,
            "breakdown": {
                "adult_count": adult_count,
                "adult_fare": adult_fare,
                "child_count": child_count,
                "child_fare": child_fare,
                "infant_count": infant_count,
                "infant_fare": infant_fare
            }
        }
    
    def _get_payment_method(self, payment_mode: PaymentMode) -> PaymentMethod:
        """Convert payment mode to payment method."""
        if payment_mode == PaymentMode.WALLET:
            return PaymentMethod.WALLET
        elif payment_mode == PaymentMode.AGENT_CREDIT:
            return PaymentMethod.AGENT_CREDIT
        else:
            return PaymentMethod.CARD
    
    # =========================================================================
    # Booking Management
    # =========================================================================
    
    async def get_booking(self, booking_id: int, user_id: int) -> Optional[FlightBooking]:
        """Get flight booking by ID."""
        result = await self.db.execute(
            select(FlightBooking).where(
                and_(FlightBooking.id == booking_id, FlightBooking.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_booking_by_reference(self, booking_reference: str) -> Optional[FlightBooking]:
        """Get flight booking by reference number."""
        result = await self.db.execute(
            select(FlightBooking).where(FlightBooking.booking_reference == booking_reference)
        )
        return result.scalar_one_or_none()
    
    async def get_booking_by_pnr(self, pnr: str) -> Optional[FlightBooking]:
        """Get flight booking by PNR."""
        result = await self.db.execute(
            select(FlightBooking).where(FlightBooking.pnr == pnr)
        )
        return result.scalar_one_or_none()
    
    async def get_user_bookings(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        status_filter: Optional[BookingStatus] = None
    ) -> List[FlightBooking]:
        """Get user's flight bookings."""
        query = select(FlightBooking).where(FlightBooking.user_id == user_id)
        
        if status_filter:
            query = query.where(FlightBooking.status == status_filter)
        
        query = query.order_by(FlightBooking.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def cancel_booking(
        self,
        booking_id: int,
        user_id: int,
        reason: str
    ) -> FlightBooking:
        """
        Cancel a flight booking with refund processing.
        
        Args:
            booking_id: Booking ID
            user_id: User ID
            reason: Cancellation reason
            
        Returns:
            Updated FlightBooking
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
        
        # Calculate refund based on airline policy
        refund_amount = self._calculate_refund(booking)
        
        # Process refund
        if refund_amount > 0:
            refund_result = await self.payment_processor.process_refund(
                user_id=user_id,
                amount=refund_amount,
                booking_id=booking_id,
                booking_type="flight",
                original_payment_method=booking.payment_method,
                reason=reason
            )
            
            booking.refund_amount = refund_amount
        
        # In production, call airline API to cancel
        # await self._cancel_with_airline(booking)
        
        # Update booking
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason
        
        if refund_amount > 0:
            booking.payment_status = PaymentStatus.REFUNDED
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Flight booking {booking.booking_reference} cancelled. Refund: {refund_amount}")
        
        return booking
    
    def _calculate_refund(self, booking: FlightBooking) -> float:
        """Calculate refund amount based on airline policy."""
        if booking.status != BookingStatus.CONFIRMED:
            return 0
        
        hours_until_departure = (booking.departure_time - datetime.utcnow()).total_seconds() / 3600
        
        # Cancellation fee per passenger (mock)
        cancellation_fee_per_pax = 3000
        total_cancellation_fee = cancellation_fee_per_pax * booking.passenger_count
        
        if hours_until_departure > 24:
            # Refund minus cancellation fee
            refund = max(0, booking.total_amount - total_cancellation_fee)
        elif hours_until_departure > 4:
            # 50% refund
            refund = booking.total_amount * 0.5
        else:
            # No refund for last-minute cancellations
            refund = 0
        
        return round(refund, 2)
    
    # =========================================================================
    # Amendment Operations
    # =========================================================================
    
    async def request_date_change(
        self,
        booking_id: int,
        user_id: int,
        new_departure_date: datetime,
        new_return_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Request date change for a booking.
        
        Args:
            booking_id: Booking ID
            user_id: User ID
            new_departure_date: New departure date
            new_return_date: New return date (if round-trip)
            
        Returns:
            Date change quote with fare difference
        """
        booking = await self.get_booking(booking_id, user_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        if booking.status != BookingStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only confirmed bookings can be amended"
            )
        
        # Calculate date change fee and fare difference
        date_change_fee = 2500 * booking.passenger_count  # Mock fee
        
        # In production, check new flight availability and pricing
        new_fare = booking.base_fare  # Mock - same fare
        fare_difference = max(0, new_fare - booking.base_fare)
        
        total_amendment_cost = date_change_fee + fare_difference
        
        return {
            "booking_reference": booking.booking_reference,
            "current_departure": booking.departure_time.isoformat(),
            "new_departure": new_departure_date.isoformat(),
            "date_change_fee": date_change_fee,
            "fare_difference": fare_difference,
            "total_amendment_cost": total_amendment_cost,
            "valid_until": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
    
    async def confirm_date_change(
        self,
        booking_id: int,
        user_id: int,
        new_departure_date: datetime,
        payment_mode: PaymentMode,
        razorpay_payment_id: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        razorpay_signature: Optional[str] = None
    ) -> FlightBooking:
        """Confirm and process date change."""
        quote = await self.request_date_change(booking_id, user_id, new_departure_date)
        
        if quote["total_amendment_cost"] > 0:
            booking = await self.get_booking(booking_id, user_id)
            
            # Process amendment payment
            payment_result = await self.payment_processor.process_payment(
                user_id=user_id,
                amount=quote["total_amendment_cost"],
                payment_mode=payment_mode,
                booking_id=booking_id,
                booking_type="flight",
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
                description=f"Date change for booking {booking.booking_reference}"
            )
            
            if payment_result["status"] != PaymentStatus.SUCCESS:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Amendment payment failed"
                )
        
        # Update booking with new date
        booking = await self.get_booking(booking_id, user_id)
        
        # Calculate time difference to apply to arrival
        time_difference = new_departure_date - booking.departure_time
        
        booking.departure_time = new_departure_date
        booking.arrival_time = booking.arrival_time + time_difference
        booking.total_amount += quote["total_amendment_cost"]
        
        # In production, update with airline
        # await self._amend_with_airline(booking)
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Flight booking {booking.booking_reference} date changed to {new_departure_date}")
        
        return booking
    
    # =========================================================================
    # Payment Order Creation
    # =========================================================================
    
    async def create_payment_order(
        self,
        user_id: int,
        offer_id: str,
        passengers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a Razorpay payment order for flight booking.
        
        Args:
            user_id: User ID
            offer_id: Flight offer ID
            passengers: Passenger list
            
        Returns:
            Razorpay order details
        """
        flight_data = await self.get_flight_details(offer_id)
        pricing = self._calculate_pricing(passengers, flight_data)
        
        order = await self.payment_processor.create_payment_order(
            amount=pricing["total_amount"],
            booking_id=0,  # Will be updated after booking creation
            booking_type="flight"
        )
        
        return {
            **order,
            "pricing": pricing,
            "offer_id": offer_id,
            "flight_details": flight_data
        }
    
    async def check_payment_eligibility(
        self,
        user_id: int,
        offer_id: str,
        passengers: List[Dict[str, Any]],
        payment_mode: PaymentMode
    ) -> Dict[str, Any]:
        """Check if user is eligible for the payment mode."""
        flight_data = await self.get_flight_details(offer_id)
        pricing = self._calculate_pricing(passengers, flight_data)
        
        return await self.payment_processor.check_payment_eligibility(
            user_id=user_id,
            amount=pricing["total_amount"],
            payment_mode=payment_mode
        )
