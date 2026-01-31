"""
Activity Services

Business logic for activity operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
import secrets
import re
import json
import logging

from app.activities.models import (
    ActivityCategory, ActivityLocation, Activity,
    ActivitySlot, ActivityBooking, ActivityStatus, BookingStatus
)

logger = logging.getLogger(__name__)


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:200]


def generate_code(prefix: str = "ACT") -> str:
    """Generate unique code."""
    return f"{prefix}{secrets.token_hex(4).upper()}"


def generate_ref(prefix: str = "ABK") -> str:
    """Generate unique reference number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()
    return f"{prefix}{timestamp}{random_part}"


class ActivityService:
    """
    Service for activity management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # Category Management
    # =========================================================================
    
    async def create_category(
        self,
        name: str,
        slug: Optional[str] = None,
        **kwargs
    ) -> ActivityCategory:
        """Create a new activity category."""
        category = ActivityCategory(
            name=name,
            slug=slug or generate_slug(name),
            **kwargs
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def get_categories(
        self,
        active_only: bool = True
    ) -> List[ActivityCategory]:
        """Get all categories."""
        query = select(ActivityCategory)
        
        if active_only:
            query = query.where(ActivityCategory.is_active == True)
        
        query = query.order_by(ActivityCategory.display_order, ActivityCategory.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_category(self, category_id: int) -> Optional[ActivityCategory]:
        """Get category by ID."""
        result = await self.db.execute(
            select(ActivityCategory).where(ActivityCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def update_category(
        self,
        category_id: int,
        **updates
    ) -> Optional[ActivityCategory]:
        """Update a category."""
        category = await self.get_category(category_id)
        if not category:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    # =========================================================================
    # Location Management
    # =========================================================================
    
    async def create_location(
        self,
        name: str,
        slug: Optional[str] = None,
        **kwargs
    ) -> ActivityLocation:
        """Create a new activity location."""
        location = ActivityLocation(
            name=name,
            slug=slug or generate_slug(name),
            **kwargs
        )
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        return location
    
    async def get_locations(
        self,
        active_only: bool = True,
        popular_only: bool = False,
        city: Optional[str] = None
    ) -> List[ActivityLocation]:
        """Get all locations."""
        query = select(ActivityLocation)
        
        if active_only:
            query = query.where(ActivityLocation.is_active == True)
        
        if popular_only:
            query = query.where(ActivityLocation.is_popular == True)
        
        if city:
            query = query.where(ActivityLocation.city.ilike(f"%{city}%"))
        
        query = query.order_by(ActivityLocation.display_order, ActivityLocation.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_location(
        self,
        location_id: Optional[int] = None,
        slug: Optional[str] = None
    ) -> Optional[ActivityLocation]:
        """Get location by ID or slug."""
        query = select(ActivityLocation)
        
        if location_id:
            query = query.where(ActivityLocation.id == location_id)
        elif slug:
            query = query.where(ActivityLocation.slug == slug)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_location(
        self,
        location_id: int,
        **updates
    ) -> Optional[ActivityLocation]:
        """Update a location."""
        location = await self.get_location(location_id)
        if not location:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(location, key):
                setattr(location, key, value)
        
        await self.db.commit()
        await self.db.refresh(location)
        return location
    
    # =========================================================================
    # Activity Management
    # =========================================================================
    
    async def create_activity(
        self,
        name: str,
        location_id: int,
        created_by_id: Optional[int] = None,
        **kwargs
    ) -> Activity:
        """Create a new activity."""
        # Extract nested data
        slots_data = kwargs.pop('slots', None)
        
        slug = kwargs.pop('slug', None) or generate_slug(name)
        code = kwargs.pop('code', None) or generate_code()
        
        # Handle gallery as JSON
        gallery = kwargs.pop('gallery', None)
        if gallery:
            kwargs['gallery'] = json.dumps(gallery)
        
        activity = Activity(
            name=name,
            slug=slug,
            code=code,
            location_id=location_id,
            created_by_id=created_by_id,
            **kwargs
        )
        self.db.add(activity)
        await self.db.flush()
        
        # Add slots
        if slots_data:
            for slot_data in slots_data:
                slot = ActivitySlot(
                    activity_id=activity.id,
                    **slot_data
                )
                slot.available_spots = slot.max_capacity
                self.db.add(slot)
        
        await self.db.commit()
        await self.db.refresh(activity)
        return activity
    
    async def get_activity(
        self,
        activity_id: Optional[int] = None,
        slug: Optional[str] = None,
        code: Optional[str] = None,
        include_slots: bool = True
    ) -> Optional[Activity]:
        """Get activity by ID, slug, or code."""
        query = select(Activity).options(
            selectinload(Activity.category),
            selectinload(Activity.location)
        )
        
        if activity_id:
            query = query.where(Activity.id == activity_id)
        elif slug:
            query = query.where(Activity.slug == slug)
        elif code:
            query = query.where(Activity.code == code)
        else:
            return None
        
        if include_slots:
            query = query.options(selectinload(Activity.slots))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_activities(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        location_id: Optional[int] = None,
        city: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        activity_date: Optional[date] = None,
        is_featured: Optional[bool] = None,
        active_only: bool = True,
        sort_by: str = "display_order",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search activities with filters."""
        stmt = select(Activity).options(
            selectinload(Activity.category),
            selectinload(Activity.location)
        )
        
        conditions = []
        
        if active_only:
            conditions.append(Activity.status == ActivityStatus.ACTIVE)
        
        if query:
            search_term = f"%{query}%"
            conditions.append(
                or_(
                    Activity.name.ilike(search_term),
                    Activity.short_description.ilike(search_term),
                    Activity.code.ilike(search_term)
                )
            )
        
        if category_id:
            conditions.append(Activity.category_id == category_id)
        
        if location_id:
            conditions.append(Activity.location_id == location_id)
        
        if city:
            stmt = stmt.join(ActivityLocation)
            conditions.append(ActivityLocation.city.ilike(f"%{city}%"))
        
        if min_price is not None:
            conditions.append(
                func.coalesce(Activity.discounted_adult_price, Activity.adult_price) >= min_price
            )
        
        if max_price is not None:
            conditions.append(
                func.coalesce(Activity.discounted_adult_price, Activity.adult_price) <= max_price
            )
        
        if is_featured is not None:
            conditions.append(Activity.is_featured == is_featured)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Sorting
        if sort_by == "price_asc":
            stmt = stmt.order_by(
                func.coalesce(Activity.discounted_adult_price, Activity.adult_price).asc()
            )
        elif sort_by == "price_desc":
            stmt = stmt.order_by(
                func.coalesce(Activity.discounted_adult_price, Activity.adult_price).desc()
            )
        elif sort_by == "rating":
            stmt = stmt.order_by(Activity.avg_rating.desc())
        elif sort_by == "newest":
            stmt = stmt.order_by(Activity.created_at.desc())
        else:
            stmt = stmt.order_by(Activity.display_order, Activity.name)
        
        # Count
        count_stmt = select(func.count(Activity.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        activities = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "activities": activities,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def get_featured_activities(self, limit: int = 10) -> List[Activity]:
        """Get featured activities."""
        stmt = select(Activity).options(
            selectinload(Activity.location)
        ).where(
            and_(
                Activity.status == ActivityStatus.ACTIVE,
                Activity.is_featured == True
            )
        ).order_by(
            Activity.display_order
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_activity(
        self,
        activity_id: int,
        **updates
    ) -> Optional[Activity]:
        """Update an activity."""
        activity = await self.get_activity(activity_id, include_slots=False)
        if not activity:
            return None
        
        # Handle gallery
        if 'gallery' in updates and updates['gallery']:
            updates['gallery'] = json.dumps(updates['gallery'])
        
        for key, value in updates.items():
            if value is not None and hasattr(activity, key):
                setattr(activity, key, value)
        
        await self.db.commit()
        await self.db.refresh(activity)
        return activity
    
    async def delete_activity(self, activity_id: int) -> bool:
        """Soft delete an activity."""
        activity = await self.get_activity(activity_id, include_slots=False)
        if not activity:
            return False
        activity.status = ActivityStatus.INACTIVE
        await self.db.commit()
        return True
    
    # =========================================================================
    # Slot Management
    # =========================================================================
    
    async def add_slot(
        self,
        activity_id: int,
        start_time: time,
        **kwargs
    ) -> ActivitySlot:
        """Add a time slot to an activity."""
        max_capacity = kwargs.pop('max_capacity', 50)
        
        slot = ActivitySlot(
            activity_id=activity_id,
            start_time=start_time,
            max_capacity=max_capacity,
            available_spots=max_capacity,
            **kwargs
        )
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot
    
    async def get_slots(
        self,
        activity_id: int,
        slot_date: Optional[date] = None,
        active_only: bool = True
    ) -> List[ActivitySlot]:
        """Get slots for an activity."""
        query = select(ActivitySlot).where(ActivitySlot.activity_id == activity_id)
        
        if slot_date:
            # Get specific date slots or recurring slots for that day
            day_of_week = slot_date.isoweekday()
            query = query.where(
                or_(
                    ActivitySlot.slot_date == slot_date,
                    and_(
                        ActivitySlot.is_recurring == True,
                        ActivitySlot.days_of_week.contains(str(day_of_week))
                    )
                )
            )
        
        if active_only:
            query = query.where(
                and_(
                    ActivitySlot.is_active == True,
                    ActivitySlot.is_blocked == False
                )
            )
        
        query = query.order_by(ActivitySlot.start_time)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_slot(
        self,
        slot_id: int,
        **updates
    ) -> Optional[ActivitySlot]:
        """Update a slot."""
        result = await self.db.execute(
            select(ActivitySlot).where(ActivitySlot.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(slot, key):
                setattr(slot, key, value)
        
        await self.db.commit()
        await self.db.refresh(slot)
        return slot
    
    async def delete_slot(self, slot_id: int) -> bool:
        """Delete a slot."""
        result = await self.db.execute(
            select(ActivitySlot).where(ActivitySlot.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return False
        await self.db.delete(slot)
        await self.db.commit()
        return True
    
    # =========================================================================
    # Booking Management
    # =========================================================================
    
    async def create_booking(
        self,
        activity_id: int,
        booking_date: date,
        contact_name: str,
        contact_email: str,
        contact_phone: str,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        slot_id: Optional[int] = None,
        user_id: Optional[int] = None,
        booked_by_id: Optional[int] = None,
        participants: Optional[list] = None,
        **kwargs
    ) -> ActivityBooking:
        """Create an activity booking."""
        # Get activity for pricing
        activity = await self.get_activity(activity_id, include_slots=False)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        
        # Check availability
        if slot_id:
            slot_result = await self.db.execute(
                select(ActivitySlot).where(ActivitySlot.id == slot_id)
            )
            slot = slot_result.scalar_one_or_none()
            if slot and slot.available_spots < (adults + children):
                raise ValueError("Not enough spots available")
        
        # Calculate pricing
        adult_rate = activity.discounted_adult_price or activity.adult_price
        child_rate = activity.child_price
        infant_rate = activity.infant_price
        
        subtotal = (adults * adult_rate) + (children * child_rate) + (infants * infant_rate)
        taxes = subtotal * 0.18  # 18% GST
        total_amount = subtotal + taxes
        
        participants_data = json.dumps([p.model_dump() for p in participants]) if participants else None
        
        booking = ActivityBooking(
            booking_ref=generate_ref("ABK"),
            activity_id=activity_id,
            slot_id=slot_id,
            user_id=user_id,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            booking_date=booking_date,
            adults=adults,
            children=children,
            infants=infants,
            adult_rate=adult_rate,
            child_rate=child_rate,
            infant_rate=infant_rate,
            subtotal=subtotal,
            taxes=taxes,
            total_amount=total_amount,
            participants_data=participants_data,
            booked_by_id=booked_by_id,
            **kwargs
        )
        
        self.db.add(booking)
        
        # Update slot availability
        if slot_id:
            slot_result = await self.db.execute(
                select(ActivitySlot).where(ActivitySlot.id == slot_id)
            )
            slot = slot_result.scalar_one_or_none()
            if slot:
                slot.available_spots -= (adults + children)
        
        # Auto-confirm if instant confirmation
        if activity.is_instant_confirmation:
            booking.is_confirmed = True
            booking.confirmed_at = datetime.utcnow()
            booking.status = BookingStatus.CONFIRMED
            booking.confirmation_code = generate_code("CNF")
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Created activity booking {booking.booking_ref}")
        return booking
    
    async def get_booking(
        self,
        booking_id: Optional[int] = None,
        booking_ref: Optional[str] = None
    ) -> Optional[ActivityBooking]:
        """Get booking by ID or reference."""
        query = select(ActivityBooking).options(
            selectinload(ActivityBooking.activity).selectinload(Activity.location)
        )
        
        if booking_id:
            query = query.where(ActivityBooking.id == booking_id)
        elif booking_ref:
            query = query.where(ActivityBooking.booking_ref == booking_ref)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_bookings(
        self,
        status: Optional[BookingStatus] = None,
        activity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        booking_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List bookings with filters."""
        stmt = select(ActivityBooking).options(
            selectinload(ActivityBooking.activity)
        )
        
        conditions = []
        
        if status:
            conditions.append(ActivityBooking.status == status)
        
        if activity_id:
            conditions.append(ActivityBooking.activity_id == activity_id)
        
        if user_id:
            conditions.append(ActivityBooking.user_id == user_id)
        
        if booking_date:
            conditions.append(ActivityBooking.booking_date == booking_date)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(ActivityBooking.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Order and paginate
        stmt = stmt.order_by(ActivityBooking.created_at.desc())
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
    ) -> Optional[ActivityBooking]:
        """Update a booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(booking, key):
                setattr(booking, key, value)
        
        # Auto-update confirmed status
        if updates.get('is_confirmed') and not booking.confirmed_at:
            booking.confirmed_at = datetime.utcnow()
            booking.confirmation_code = generate_code("CNF")
            booking.status = BookingStatus.CONFIRMED
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def cancel_booking(
        self,
        booking_id: int,
        reason: str,
        refund_amount: Optional[float] = None
    ) -> Optional[ActivityBooking]:
        """Cancel a booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        booking.refund_amount = refund_amount
        
        # Restore slot availability
        if booking.slot_id:
            slot_result = await self.db.execute(
                select(ActivitySlot).where(ActivitySlot.id == booking.slot_id)
            )
            slot = slot_result.scalar_one_or_none()
            if slot:
                slot.available_spots += (booking.adults + booking.children)
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Cancelled activity booking {booking.booking_ref}")
        return booking
