"""
Transfer Services

Business logic for transfer/cab operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from datetime import datetime, date, time, timedelta
import secrets
import re
import logging

from app.transfers.models import (
    CarType, TransferRoute, TransferBooking, TransferBookingStatus
)

logger = logging.getLogger(__name__)


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:200]


def generate_ref(prefix: str = "TRF") -> str:
    """Generate unique reference number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()
    return f"{prefix}{timestamp}{random_part}"


class TransferService:
    """
    Service for transfer/cab management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # Car Type Management
    # =========================================================================
    
    async def create_car_type(
        self,
        name: str,
        slug: Optional[str] = None,
        **kwargs
    ) -> CarType:
        """Create a new car type."""
        car_type = CarType(
            name=name,
            slug=slug or generate_slug(name),
            **kwargs
        )
        self.db.add(car_type)
        await self.db.commit()
        await self.db.refresh(car_type)
        return car_type
    
    async def get_car_types(
        self,
        active_only: bool = True,
        category: Optional[str] = None
    ) -> List[CarType]:
        """Get all car types."""
        query = select(CarType)
        
        if active_only:
            query = query.where(CarType.is_active == True)
        
        if category:
            query = query.where(CarType.category == category)
        
        query = query.order_by(CarType.display_order, CarType.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_car_type(
        self,
        car_type_id: Optional[int] = None,
        slug: Optional[str] = None
    ) -> Optional[CarType]:
        """Get car type by ID or slug."""
        query = select(CarType)
        
        if car_type_id:
            query = query.where(CarType.id == car_type_id)
        elif slug:
            query = query.where(CarType.slug == slug)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_car_type(
        self,
        car_type_id: int,
        **updates
    ) -> Optional[CarType]:
        """Update a car type."""
        car_type = await self.get_car_type(car_type_id)
        if not car_type:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(car_type, key):
                setattr(car_type, key, value)
        
        await self.db.commit()
        await self.db.refresh(car_type)
        return car_type
    
    # =========================================================================
    # Route Management
    # =========================================================================
    
    async def create_route(
        self,
        name: str,
        origin_city: str,
        destination_city: str,
        car_type_id: int,
        slug: Optional[str] = None,
        **kwargs
    ) -> TransferRoute:
        """Create a new transfer route."""
        route = TransferRoute(
            name=name,
            slug=slug or generate_slug(name),
            origin_city=origin_city,
            destination_city=destination_city,
            car_type_id=car_type_id,
            **kwargs
        )
        self.db.add(route)
        await self.db.commit()
        await self.db.refresh(route)
        return route
    
    async def get_routes(
        self,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        car_type_id: Optional[int] = None,
        is_popular: Optional[bool] = None,
        active_only: bool = True
    ) -> List[TransferRoute]:
        """Get routes with filters."""
        query = select(TransferRoute).options(
            selectinload(TransferRoute.car_type)
        )
        
        conditions = []
        
        if active_only:
            conditions.append(TransferRoute.is_active == True)
        
        if origin_city:
            conditions.append(TransferRoute.origin_city.ilike(f"%{origin_city}%"))
        
        if destination_city:
            conditions.append(TransferRoute.destination_city.ilike(f"%{destination_city}%"))
        
        if car_type_id:
            conditions.append(TransferRoute.car_type_id == car_type_id)
        
        if is_popular is not None:
            conditions.append(TransferRoute.is_popular == is_popular)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(TransferRoute.display_order, TransferRoute.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_route(
        self,
        route_id: Optional[int] = None,
        slug: Optional[str] = None
    ) -> Optional[TransferRoute]:
        """Get route by ID or slug."""
        query = select(TransferRoute).options(
            selectinload(TransferRoute.car_type)
        )
        
        if route_id:
            query = query.where(TransferRoute.id == route_id)
        elif slug:
            query = query.where(TransferRoute.slug == slug)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_routes(
        self,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        car_type_id: Optional[int] = None,
        is_popular: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search routes with pagination."""
        stmt = select(TransferRoute).options(
            selectinload(TransferRoute.car_type)
        )
        
        conditions = []
        conditions.append(TransferRoute.is_active == True)
        
        if origin_city:
            conditions.append(TransferRoute.origin_city.ilike(f"%{origin_city}%"))
        
        if destination_city:
            conditions.append(TransferRoute.destination_city.ilike(f"%{destination_city}%"))
        
        if car_type_id:
            conditions.append(TransferRoute.car_type_id == car_type_id)
        
        if is_popular is not None:
            conditions.append(TransferRoute.is_popular == is_popular)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(TransferRoute.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(TransferRoute.display_order, TransferRoute.name)
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        routes = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "routes": routes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def update_route(
        self,
        route_id: int,
        **updates
    ) -> Optional[TransferRoute]:
        """Update a route."""
        route = await self.get_route(route_id)
        if not route:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(route, key):
                setattr(route, key, value)
        
        await self.db.commit()
        await self.db.refresh(route)
        return route
    
    async def get_popular_routes(self, limit: int = 10) -> List[TransferRoute]:
        """Get popular routes."""
        stmt = select(TransferRoute).options(
            selectinload(TransferRoute.car_type)
        ).where(
            and_(
                TransferRoute.is_active == True,
                TransferRoute.is_popular == True
            )
        ).order_by(
            TransferRoute.display_order
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # =========================================================================
    # Price Estimation
    # =========================================================================
    
    async def estimate_price(
        self,
        car_type_id: int,
        trip_type: str = "one_way",
        route_id: Optional[int] = None,
        pickup_date: Optional[date] = None,
        pickup_time: Optional[time] = None,
        return_date: Optional[date] = None,
        custom_distance_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """Estimate price for a transfer."""
        # Get car type
        car_type = await self.get_car_type(car_type_id)
        if not car_type:
            raise ValueError(f"Car type {car_type_id} not found")
        
        base_fare = 0
        toll_charges = 0
        state_tax = 0
        included_km = 0
        included_hours = 0
        extra_km_charge = 0
        extra_hour_charge = 0
        
        # Use route pricing if available
        if route_id:
            route = await self.get_route(route_id)
            if route:
                if trip_type == "round_trip" and route.round_trip_price:
                    base_fare = route.round_trip_price
                else:
                    base_fare = route.base_price
                    if trip_type == "round_trip":
                        base_fare = base_fare * 2
                
                toll_charges = route.toll_charges * (2 if trip_type == "round_trip" else 1)
                state_tax = route.state_tax * (2 if trip_type == "round_trip" else 1)
                included_km = route.included_km * (2 if trip_type == "round_trip" else 1)
                included_hours = route.included_hours * (2 if trip_type == "round_trip" else 1)
                extra_km_charge = route.extra_km_charge
                extra_hour_charge = route.extra_hour_charge
        
        # Or calculate from distance
        elif custom_distance_km:
            base_fare = custom_distance_km * car_type.base_price_per_km
            if trip_type == "round_trip":
                base_fare = base_fare * 2
            extra_km_charge = car_type.base_price_per_km
        
        # Calculate driver allowance (if overnight trip)
        driver_allowance = 0
        night_charges = 0
        
        if pickup_date and return_date:
            days = (return_date - pickup_date).days
            if days > 0:
                driver_allowance = car_type.driver_allowance_per_day * days
        
        # Night charges (if pickup after 10 PM or before 6 AM)
        if pickup_time:
            if pickup_time.hour >= 22 or pickup_time.hour < 6:
                night_charges = car_type.night_charges
        
        subtotal = base_fare + toll_charges + state_tax + driver_allowance + night_charges
        taxes = subtotal * 0.05  # 5% GST
        total_amount = subtotal + taxes
        
        return {
            "car_type": car_type,
            "base_fare": base_fare,
            "toll_charges": toll_charges,
            "state_tax": state_tax,
            "driver_allowance": driver_allowance,
            "night_charges": night_charges,
            "taxes": taxes,
            "total_amount": total_amount,
            "included_km": included_km,
            "included_hours": included_hours,
            "extra_km_charge": extra_km_charge,
            "extra_hour_charge": extra_hour_charge
        }
    
    # =========================================================================
    # Booking Management
    # =========================================================================
    
    async def create_booking(
        self,
        car_type_id: int,
        passenger_name: str,
        passenger_email: str,
        passenger_phone: str,
        pickup_date: date,
        pickup_time: time,
        pickup_address: str,
        dropoff_address: str,
        trip_type: str = "one_way",
        route_id: Optional[int] = None,
        user_id: Optional[int] = None,
        booked_by_id: Optional[int] = None,
        **kwargs
    ) -> TransferBooking:
        """Create a transfer booking."""
        # Estimate price
        estimate = await self.estimate_price(
            car_type_id=car_type_id,
            trip_type=trip_type,
            route_id=route_id,
            pickup_date=pickup_date,
            pickup_time=pickup_time,
            return_date=kwargs.get('return_date'),
            custom_distance_km=kwargs.get('custom_distance_km')
        )
        
        booking = TransferBooking(
            booking_ref=generate_ref("TRF"),
            car_type_id=car_type_id,
            route_id=route_id,
            trip_type=trip_type,
            user_id=user_id,
            passenger_name=passenger_name,
            passenger_email=passenger_email,
            passenger_phone=passenger_phone,
            pickup_date=pickup_date,
            pickup_time=pickup_time,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            base_fare=estimate['base_fare'],
            toll_charges=estimate['toll_charges'],
            state_tax=estimate['state_tax'],
            driver_allowance=estimate['driver_allowance'],
            night_charges=estimate['night_charges'],
            taxes=estimate['taxes'],
            total_amount=estimate['total_amount'],
            booked_by_id=booked_by_id,
            **kwargs
        )
        
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Created transfer booking {booking.booking_ref}")
        return booking
    
    async def get_booking(
        self,
        booking_id: Optional[int] = None,
        booking_ref: Optional[str] = None
    ) -> Optional[TransferBooking]:
        """Get booking by ID or reference."""
        query = select(TransferBooking).options(
            selectinload(TransferBooking.route),
            selectinload(TransferBooking.car_type)
        )
        
        if booking_id:
            query = query.where(TransferBooking.id == booking_id)
        elif booking_ref:
            query = query.where(TransferBooking.booking_ref == booking_ref)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_bookings(
        self,
        status: Optional[TransferBookingStatus] = None,
        route_id: Optional[int] = None,
        car_type_id: Optional[int] = None,
        user_id: Optional[int] = None,
        pickup_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List bookings with filters."""
        stmt = select(TransferBooking).options(
            selectinload(TransferBooking.route),
            selectinload(TransferBooking.car_type)
        )
        
        conditions = []
        
        if status:
            conditions.append(TransferBooking.status == status)
        
        if route_id:
            conditions.append(TransferBooking.route_id == route_id)
        
        if car_type_id:
            conditions.append(TransferBooking.car_type_id == car_type_id)
        
        if user_id:
            conditions.append(TransferBooking.user_id == user_id)
        
        if pickup_date:
            conditions.append(TransferBooking.pickup_date == pickup_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(TransferBooking.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Order and paginate
        stmt = stmt.order_by(TransferBooking.created_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        bookings = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "bookings": bookings,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def update_booking(
        self,
        booking_id: int,
        **updates
    ) -> Optional[TransferBooking]:
        """Update a booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(booking, key):
                setattr(booking, key, value)
        
        # Auto-update timestamps
        if updates.get('driver_name') and not booking.driver_assigned_at:
            booking.driver_assigned_at = datetime.utcnow()
            booking.status = TransferBookingStatus.DRIVER_ASSIGNED
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def confirm_booking(
        self,
        booking_id: int
    ) -> Optional[TransferBooking]:
        """Confirm a pending booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = TransferBookingStatus.CONFIRMED
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def start_trip(
        self,
        booking_id: int
    ) -> Optional[TransferBooking]:
        """Mark trip as started."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = TransferBookingStatus.IN_PROGRESS
        booking.started_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def complete_trip(
        self,
        booking_id: int,
        actual_km: Optional[float] = None
    ) -> Optional[TransferBooking]:
        """Mark trip as completed."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = TransferBookingStatus.COMPLETED
        booking.completed_at = datetime.utcnow()
        
        if actual_km:
            booking.actual_km = actual_km
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def cancel_booking(
        self,
        booking_id: int,
        reason: str,
        refund_amount: Optional[float] = None
    ) -> Optional[TransferBooking]:
        """Cancel a booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = TransferBookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        booking.refund_amount = refund_amount
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Cancelled transfer booking {booking.booking_ref}")
        return booking
    
    async def get_today_bookings(self) -> List[TransferBooking]:
        """Get all bookings for today."""
        today = date.today()
        
        stmt = select(TransferBooking).options(
            selectinload(TransferBooking.route),
            selectinload(TransferBooking.car_type)
        ).where(
            TransferBooking.pickup_date == today
        ).order_by(
            TransferBooking.pickup_time
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
