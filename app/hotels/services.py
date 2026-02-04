"""
Offline Hotel Services

Business logic for hotel inventory management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
import uuid

from app.hotels.models import (
    Hotel, HotelCategory, RoomType, RoomAmenity, HotelAmenity,
    MealPlan, HotelRoom, HotelRate, HotelContract, RoomInventory,
    HotelImage, HotelEnquiry, OfflineHotelBooking,
    HotelStatus, ContractStatus, BookingStatus, RateType
)


class HotelService:
    """Service for hotel CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # CATEGORIES
    # =========================================================================
    
    async def get_categories(self, active_only: bool = True) -> List[HotelCategory]:
        stmt = select(HotelCategory)
        if active_only:
            stmt = stmt.where(HotelCategory.is_active == True)
        stmt = stmt.order_by(HotelCategory.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_category(self, **data) -> HotelCategory:
        category = HotelCategory(**data)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def get_category(self, category_id: int) -> Optional[HotelCategory]:
        stmt = select(HotelCategory).where(HotelCategory.id == category_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_category(self, category_id: int, **data) -> Optional[HotelCategory]:
        category = await self.get_category(category_id)
        if not category:
            return None
        for key, value in data.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    # =========================================================================
    # AMENITIES
    # =========================================================================
    
    async def get_hotel_amenities(self, active_only: bool = True) -> List[HotelAmenity]:
        stmt = select(HotelAmenity)
        if active_only:
            stmt = stmt.where(HotelAmenity.is_active == True)
        stmt = stmt.order_by(HotelAmenity.category, HotelAmenity.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_hotel_amenity(self, **data) -> HotelAmenity:
        amenity = HotelAmenity(**data)
        self.db.add(amenity)
        await self.db.commit()
        await self.db.refresh(amenity)
        return amenity
    
    async def get_room_amenities(self, active_only: bool = True) -> List[RoomAmenity]:
        stmt = select(RoomAmenity)
        if active_only:
            stmt = stmt.where(RoomAmenity.is_active == True)
        stmt = stmt.order_by(RoomAmenity.category, RoomAmenity.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_room_amenity(self, **data) -> RoomAmenity:
        amenity = RoomAmenity(**data)
        self.db.add(amenity)
        await self.db.commit()
        await self.db.refresh(amenity)
        return amenity
    
    # =========================================================================
    # MEAL PLANS
    # =========================================================================
    
    async def get_meal_plans(self, active_only: bool = True) -> List[MealPlan]:
        stmt = select(MealPlan)
        if active_only:
            stmt = stmt.where(MealPlan.is_active == True)
        stmt = stmt.order_by(MealPlan.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_meal_plan(self, **data) -> MealPlan:
        plan = MealPlan(**data)
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan
    
    # =========================================================================
    # ROOM TYPES
    # =========================================================================
    
    async def get_room_types(self, active_only: bool = True) -> List[RoomType]:
        stmt = select(RoomType)
        if active_only:
            stmt = stmt.where(RoomType.is_active == True)
        stmt = stmt.order_by(RoomType.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_room_type(self, **data) -> RoomType:
        room_type = RoomType(**data)
        self.db.add(room_type)
        await self.db.commit()
        await self.db.refresh(room_type)
        return room_type
    
    async def get_room_type(self, room_type_id: int) -> Optional[RoomType]:
        stmt = select(RoomType).where(RoomType.id == room_type_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_room_type(self, room_type_id: int, **data) -> Optional[RoomType]:
        room_type = await self.get_room_type(room_type_id)
        if not room_type:
            return None
        for key, value in data.items():
            if hasattr(room_type, key) and value is not None:
                setattr(room_type, key, value)
        await self.db.commit()
        await self.db.refresh(room_type)
        return room_type
    
    # =========================================================================
    # HOTELS
    # =========================================================================
    
    async def get_hotels(
        self,
        tenant_id: Optional[int] = None,
        city: Optional[str] = None,
        category_id: Optional[int] = None,
        star_rating: Optional[int] = None,
        status: Optional[HotelStatus] = None,
        is_featured: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Hotel], int]:
        stmt = select(Hotel).options(selectinload(Hotel.category))
        
        if tenant_id:
            stmt = stmt.where(Hotel.tenant_id == tenant_id)
        if city:
            stmt = stmt.where(Hotel.city.ilike(f"%{city}%"))
        if category_id:
            stmt = stmt.where(Hotel.category_id == category_id)
        if star_rating:
            stmt = stmt.where(Hotel.star_rating == star_rating)
        if status:
            stmt = stmt.where(Hotel.status == status)
        else:
            stmt = stmt.where(Hotel.status == HotelStatus.ACTIVE)
        if is_featured is not None:
            stmt = stmt.where(Hotel.is_featured == is_featured)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Pagination
        stmt = stmt.order_by(Hotel.display_order, Hotel.name)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        hotels = list(result.scalars().all())
        
        return hotels, total
    
    async def search_hotels(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        star_rating: Optional[int] = None,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        amenity_ids: Optional[List[int]] = None,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        rooms: int = 1,
        tenant_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Hotel], int, Dict]:
        stmt = select(Hotel).where(Hotel.status == HotelStatus.ACTIVE)
        
        if tenant_id:
            stmt = stmt.where(Hotel.tenant_id == tenant_id)
        if query:
            stmt = stmt.where(
                or_(
                    Hotel.name.ilike(f"%{query}%"),
                    Hotel.city.ilike(f"%{query}%"),
                    Hotel.description.ilike(f"%{query}%")
                )
            )
        if city:
            stmt = stmt.where(Hotel.city.ilike(f"%{city}%"))
        if state:
            stmt = stmt.where(Hotel.state.ilike(f"%{state}%"))
        if star_rating:
            stmt = stmt.where(Hotel.star_rating == star_rating)
        if category_id:
            stmt = stmt.where(Hotel.category_id == category_id)
        if min_price:
            stmt = stmt.where(Hotel.starting_price >= min_price)
        if max_price:
            stmt = stmt.where(Hotel.starting_price <= max_price)
        
        # TODO: Filter by amenities (JSON contains)
        # TODO: Filter by availability if check_in/check_out provided
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Pagination
        stmt = stmt.order_by(Hotel.is_featured.desc(), Hotel.is_popular.desc(), Hotel.name)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        hotels = list(result.scalars().all())
        
        filters_applied = {
            "city": city,
            "state": state,
            "star_rating": star_rating,
            "min_price": min_price,
            "max_price": max_price,
            "check_in": str(check_in) if check_in else None,
            "check_out": str(check_out) if check_out else None
        }
        
        return hotels, total, filters_applied
    
    async def get_hotel(self, hotel_id: int) -> Optional[Hotel]:
        stmt = select(Hotel).options(
            selectinload(Hotel.category),
            selectinload(Hotel.rooms).selectinload(HotelRoom.room_type),
            selectinload(Hotel.rooms).selectinload(HotelRoom.rates),
            selectinload(Hotel.images)
        ).where(Hotel.id == hotel_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_hotel_by_slug(self, slug: str) -> Optional[Hotel]:
        stmt = select(Hotel).options(
            selectinload(Hotel.category),
            selectinload(Hotel.rooms).selectinload(HotelRoom.room_type),
            selectinload(Hotel.images)
        ).where(Hotel.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_hotel(self, tenant_id: Optional[int] = None, created_by_id: Optional[int] = None, **data) -> Hotel:
        hotel = Hotel(tenant_id=tenant_id, created_by_id=created_by_id, **data)
        self.db.add(hotel)
        await self.db.commit()
        await self.db.refresh(hotel)
        return hotel
    
    async def update_hotel(self, hotel_id: int, **data) -> Optional[Hotel]:
        hotel = await self.get_hotel(hotel_id)
        if not hotel:
            return None
        for key, value in data.items():
            if hasattr(hotel, key) and value is not None:
                setattr(hotel, key, value)
        await self.db.commit()
        await self.db.refresh(hotel)
        return hotel
    
    async def delete_hotel(self, hotel_id: int) -> bool:
        hotel = await self.get_hotel(hotel_id)
        if not hotel:
            return False
        await self.db.delete(hotel)
        await self.db.commit()
        return True
    
    # =========================================================================
    # HOTEL ROOMS
    # =========================================================================
    
    async def get_hotel_rooms(self, hotel_id: int, active_only: bool = True) -> List[HotelRoom]:
        stmt = select(HotelRoom).options(
            selectinload(HotelRoom.room_type),
            selectinload(HotelRoom.rates)
        ).where(HotelRoom.hotel_id == hotel_id)
        
        if active_only:
            stmt = stmt.where(HotelRoom.is_active == True)
        stmt = stmt.order_by(HotelRoom.display_order)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_room(self, room_id: int) -> Optional[HotelRoom]:
        stmt = select(HotelRoom).options(
            selectinload(HotelRoom.room_type),
            selectinload(HotelRoom.rates).selectinload(HotelRate.meal_plan)
        ).where(HotelRoom.id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_room(self, hotel_id: int, **data) -> HotelRoom:
        room = HotelRoom(hotel_id=hotel_id, **data)
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room
    
    async def update_room(self, room_id: int, **data) -> Optional[HotelRoom]:
        room = await self.get_room(room_id)
        if not room:
            return None
        for key, value in data.items():
            if hasattr(room, key) and value is not None:
                setattr(room, key, value)
        await self.db.commit()
        await self.db.refresh(room)
        return room
    
    async def delete_room(self, room_id: int) -> bool:
        room = await self.get_room(room_id)
        if not room:
            return False
        await self.db.delete(room)
        await self.db.commit()
        return True
    
    # =========================================================================
    # HOTEL RATES
    # =========================================================================
    
    async def get_room_rates(
        self,
        room_id: int,
        active_only: bool = True,
        as_of_date: Optional[date] = None
    ) -> List[HotelRate]:
        stmt = select(HotelRate).options(
            selectinload(HotelRate.meal_plan)
        ).where(HotelRate.room_id == room_id)
        
        if active_only:
            stmt = stmt.where(HotelRate.is_active == True)
        if as_of_date:
            stmt = stmt.where(
                and_(
                    HotelRate.valid_from <= as_of_date,
                    HotelRate.valid_to >= as_of_date
                )
            )
        
        stmt = stmt.order_by(HotelRate.valid_from)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_rate(self, rate_id: int) -> Optional[HotelRate]:
        stmt = select(HotelRate).options(
            selectinload(HotelRate.meal_plan)
        ).where(HotelRate.id == rate_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_rate(self, **data) -> HotelRate:
        rate = HotelRate(**data)
        self.db.add(rate)
        await self.db.commit()
        await self.db.refresh(rate)
        return rate
    
    async def update_rate(self, rate_id: int, **data) -> Optional[HotelRate]:
        rate = await self.get_rate(rate_id)
        if not rate:
            return None
        for key, value in data.items():
            if hasattr(rate, key) and value is not None:
                setattr(rate, key, value)
        await self.db.commit()
        await self.db.refresh(rate)
        return rate
    
    async def delete_rate(self, rate_id: int) -> bool:
        rate = await self.get_rate(rate_id)
        if not rate:
            return False
        await self.db.delete(rate)
        await self.db.commit()
        return True
    
    # =========================================================================
    # CONTRACTS
    # =========================================================================
    
    async def get_hotel_contracts(
        self,
        hotel_id: int,
        status: Optional[ContractStatus] = None
    ) -> List[HotelContract]:
        stmt = select(HotelContract).where(HotelContract.hotel_id == hotel_id)
        if status:
            stmt = stmt.where(HotelContract.status == status)
        stmt = stmt.order_by(HotelContract.valid_from.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_contract(self, contract_id: int) -> Optional[HotelContract]:
        stmt = select(HotelContract).where(HotelContract.id == contract_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_contract(self, created_by_id: Optional[int] = None, **data) -> HotelContract:
        contract = HotelContract(created_by_id=created_by_id, **data)
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract
    
    async def update_contract(self, contract_id: int, **data) -> Optional[HotelContract]:
        contract = await self.get_contract(contract_id)
        if not contract:
            return None
        for key, value in data.items():
            if hasattr(contract, key) and value is not None:
                setattr(contract, key, value)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract


class HotelInventoryService:
    """Service for inventory and booking operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # INVENTORY
    # =========================================================================
    
    async def get_inventory(
        self,
        room_id: int,
        start_date: date,
        end_date: date
    ) -> List[RoomInventory]:
        stmt = select(RoomInventory).where(
            and_(
                RoomInventory.room_id == room_id,
                RoomInventory.inventory_date >= start_date,
                RoomInventory.inventory_date <= end_date
            )
        ).order_by(RoomInventory.inventory_date)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_inventory(
        self,
        room_id: int,
        inventory_date: date,
        updated_by_id: Optional[int] = None,
        **data
    ) -> RoomInventory:
        # Get or create
        stmt = select(RoomInventory).where(
            and_(
                RoomInventory.room_id == room_id,
                RoomInventory.inventory_date == inventory_date
            )
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if inventory:
            for key, value in data.items():
                if hasattr(inventory, key) and value is not None:
                    setattr(inventory, key, value)
            inventory.updated_by_id = updated_by_id
        else:
            inventory = RoomInventory(
                room_id=room_id,
                inventory_date=inventory_date,
                updated_by_id=updated_by_id,
                **data
            )
            self.db.add(inventory)
        
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory
    
    async def bulk_update_inventory(
        self,
        room_id: int,
        start_date: date,
        end_date: date,
        updated_by_id: Optional[int] = None,
        **data
    ) -> int:
        """Update inventory for a date range."""
        current_date = start_date
        count = 0
        
        while current_date <= end_date:
            await self.update_inventory(
                room_id=room_id,
                inventory_date=current_date,
                updated_by_id=updated_by_id,
                **data
            )
            current_date += timedelta(days=1)
            count += 1
        
        return count
    
    async def check_availability(
        self,
        room_id: int,
        check_in: date,
        check_out: date,
        rooms_required: int = 1
    ) -> Tuple[bool, int]:
        """Check if room is available for dates."""
        min_available = rooms_required
        
        current_date = check_in
        while current_date < check_out:
            stmt = select(RoomInventory).where(
                and_(
                    RoomInventory.room_id == room_id,
                    RoomInventory.inventory_date == current_date
                )
            )
            result = await self.db.execute(stmt)
            inventory = result.scalar_one_or_none()
            
            if inventory:
                if inventory.stop_sale:
                    return False, 0
                available = inventory.total_rooms - inventory.booked_rooms - inventory.blocked_rooms
                min_available = min(min_available, available)
            else:
                # Get room total if no inventory record
                room_stmt = select(HotelRoom).where(HotelRoom.id == room_id)
                room_result = await self.db.execute(room_stmt)
                room = room_result.scalar_one_or_none()
                if room:
                    min_available = min(min_available, room.total_rooms)
            
            current_date += timedelta(days=1)
        
        return min_available >= rooms_required, min_available
    
    # =========================================================================
    # ENQUIRIES
    # =========================================================================
    
    async def create_enquiry(
        self,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        **data
    ) -> HotelEnquiry:
        enquiry_number = f"HE{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        enquiry = HotelEnquiry(
            enquiry_number=enquiry_number,
            user_id=user_id,
            tenant_id=tenant_id,
            **data
        )
        self.db.add(enquiry)
        await self.db.commit()
        await self.db.refresh(enquiry)
        return enquiry
    
    async def get_enquiries(
        self,
        tenant_id: Optional[int] = None,
        hotel_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[HotelEnquiry], int]:
        stmt = select(HotelEnquiry)
        
        if tenant_id:
            stmt = stmt.where(HotelEnquiry.tenant_id == tenant_id)
        if hotel_id:
            stmt = stmt.where(HotelEnquiry.hotel_id == hotel_id)
        if status:
            stmt = stmt.where(HotelEnquiry.status == status)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Pagination
        stmt = stmt.order_by(HotelEnquiry.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        enquiries = list(result.scalars().all())
        
        return enquiries, total
    
    async def get_enquiry(self, enquiry_id: int) -> Optional[HotelEnquiry]:
        stmt = select(HotelEnquiry).where(HotelEnquiry.id == enquiry_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_enquiry(self, enquiry_id: int, **data) -> Optional[HotelEnquiry]:
        enquiry = await self.get_enquiry(enquiry_id)
        if not enquiry:
            return None
        for key, value in data.items():
            if hasattr(enquiry, key) and value is not None:
                setattr(enquiry, key, value)
        await self.db.commit()
        await self.db.refresh(enquiry)
        return enquiry
    
    # =========================================================================
    # BOOKINGS
    # =========================================================================
    
    async def create_booking(
        self,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        created_by_id: Optional[int] = None,
        **data
    ) -> OfflineHotelBooking:
        booking_ref = f"HB{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate nights
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        nights = (check_out - check_in).days if check_in and check_out else 1
        
        # Get rate for pricing
        room_rate = data.get('room_rate', 0)
        rooms_booked = data.get('rooms_booked', 1)
        total_room_charge = room_rate * nights * rooms_booked
        
        taxes = data.get('taxes', 0)
        discount = data.get('discount', 0)
        extra_charges = data.get('extra_adult_charge', 0) + data.get('extra_child_charge', 0) + data.get('meal_charge', 0)
        total_amount = total_room_charge + extra_charges + taxes - discount
        
        booking = OfflineHotelBooking(
            booking_reference=booking_ref,
            user_id=user_id,
            tenant_id=tenant_id,
            created_by_id=created_by_id,
            nights=nights,
            total_room_charge=total_room_charge,
            total_amount=total_amount,
            **data
        )
        self.db.add(booking)
        
        # Update inventory (deduct rooms)
        room_id = data.get('room_id')
        if room_id:
            current_date = check_in
            while current_date < check_out:
                await self._increment_booked_rooms(room_id, current_date, rooms_booked)
                current_date += timedelta(days=1)
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def _increment_booked_rooms(self, room_id: int, inv_date: date, count: int):
        stmt = select(RoomInventory).where(
            and_(
                RoomInventory.room_id == room_id,
                RoomInventory.inventory_date == inv_date
            )
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if inventory:
            inventory.booked_rooms += count
        else:
            # Get room total
            room_stmt = select(HotelRoom).where(HotelRoom.id == room_id)
            room_result = await self.db.execute(room_stmt)
            room = room_result.scalar_one_or_none()
            total = room.total_rooms if room else 1
            
            inventory = RoomInventory(
                room_id=room_id,
                inventory_date=inv_date,
                total_rooms=total,
                booked_rooms=count
            )
            self.db.add(inventory)
    
    async def get_bookings(
        self,
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None,
        hotel_id: Optional[int] = None,
        status: Optional[BookingStatus] = None,
        check_in_from: Optional[date] = None,
        check_in_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[OfflineHotelBooking], int]:
        stmt = select(OfflineHotelBooking)
        
        if tenant_id:
            stmt = stmt.where(OfflineHotelBooking.tenant_id == tenant_id)
        if user_id:
            stmt = stmt.where(OfflineHotelBooking.user_id == user_id)
        if hotel_id:
            stmt = stmt.where(OfflineHotelBooking.hotel_id == hotel_id)
        if status:
            stmt = stmt.where(OfflineHotelBooking.status == status)
        if check_in_from:
            stmt = stmt.where(OfflineHotelBooking.check_in_date >= check_in_from)
        if check_in_to:
            stmt = stmt.where(OfflineHotelBooking.check_in_date <= check_in_to)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Pagination
        stmt = stmt.order_by(OfflineHotelBooking.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        bookings = list(result.scalars().all())
        
        return bookings, total
    
    async def get_booking(self, booking_id: int) -> Optional[OfflineHotelBooking]:
        stmt = select(OfflineHotelBooking).options(
            selectinload(OfflineHotelBooking.hotel)
        ).where(OfflineHotelBooking.id == booking_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_booking_by_ref(self, booking_ref: str) -> Optional[OfflineHotelBooking]:
        stmt = select(OfflineHotelBooking).options(
            selectinload(OfflineHotelBooking.hotel)
        ).where(OfflineHotelBooking.booking_reference == booking_ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_booking(self, booking_id: int, **data) -> Optional[OfflineHotelBooking]:
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        for key, value in data.items():
            if hasattr(booking, key) and value is not None:
                setattr(booking, key, value)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def cancel_booking(
        self,
        booking_id: int,
        reason: str,
        cancellation_charges: float = 0,
        refund_amount: float = 0
    ) -> Optional[OfflineHotelBooking]:
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        booking.cancellation_charges = cancellation_charges
        booking.refund_amount = refund_amount
        
        # Release inventory
        room_id = booking.room_id
        current_date = booking.check_in_date
        while current_date < booking.check_out_date:
            await self._decrement_booked_rooms(room_id, current_date, booking.rooms_booked)
            current_date += timedelta(days=1)
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def _decrement_booked_rooms(self, room_id: int, inv_date: date, count: int):
        stmt = select(RoomInventory).where(
            and_(
                RoomInventory.room_id == room_id,
                RoomInventory.inventory_date == inv_date
            )
        )
        result = await self.db.execute(stmt)
        inventory = result.scalar_one_or_none()
        
        if inventory:
            inventory.booked_rooms = max(0, inventory.booked_rooms - count)
