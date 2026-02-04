"""
Offline Hotel API

REST endpoints for offline hotel inventory management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.hotels.models import HotelStatus, ContractStatus, BookingStatus
from app.hotels.services import HotelService, HotelInventoryService
from app.hotels.schemas import (
    # Category
    HotelCategoryCreate, HotelCategoryUpdate, HotelCategoryResponse,
    # Amenities
    HotelAmenityCreate, RoomAmenityCreate, AmenityResponse,
    # Meal Plans
    MealPlanCreate, MealPlanResponse,
    # Room Types
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse,
    # Hotels
    HotelCreate, HotelUpdate, HotelResponse, HotelDetail,
    HotelListResponse, HotelSearchParams, HotelSearchResponse,
    # Rooms
    HotelRoomCreate, HotelRoomUpdate, HotelRoomResponse,
    # Rates
    HotelRateCreate, HotelRateUpdate, HotelRateResponse,
    # Contracts
    HotelContractCreate, HotelContractUpdate, HotelContractResponse,
    # Inventory
    RoomInventoryUpdate, RoomInventoryResponse, BulkInventoryUpdate,
    # Enquiries
    HotelEnquiryCreate, HotelEnquiryUpdate, HotelEnquiryResponse, HotelEnquiryListResponse,
    # Bookings
    BookingCreate, BookingUpdate, BookingResponse, BookingDetail,
    BookingListResponse, BookingCancellation,
    # Availability
    AvailabilityRequest, AvailabilityResponse
)

router = APIRouter(prefix="/offline-hotels", tags=["Offline Hotels"])


# =============================================================================
# CATEGORIES
# =============================================================================

@router.get("/categories", response_model=List[HotelCategoryResponse])
async def list_categories(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all hotel categories."""
    service = HotelService(db)
    return await service.get_categories(active_only=active_only)


@router.post("/categories", response_model=HotelCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: HotelCategoryCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new hotel category."""
    service = HotelService(db)
    return await service.create_category(**data.model_dump())


@router.put("/categories/{category_id}", response_model=HotelCategoryResponse)
async def update_category(
    category_id: int,
    data: HotelCategoryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a category."""
    service = HotelService(db)
    category = await service.update_category(category_id, **data.model_dump(exclude_unset=True))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# =============================================================================
# AMENITIES
# =============================================================================

@router.get("/amenities/hotel", response_model=List[AmenityResponse])
async def list_hotel_amenities(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all hotel-level amenities."""
    service = HotelService(db)
    return await service.get_hotel_amenities(active_only=active_only)


@router.post("/amenities/hotel", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel_amenity(
    data: HotelAmenityCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new hotel amenity."""
    service = HotelService(db)
    return await service.create_hotel_amenity(**data.model_dump())


@router.get("/amenities/room", response_model=List[AmenityResponse])
async def list_room_amenities(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all room-level amenities."""
    service = HotelService(db)
    return await service.get_room_amenities(active_only=active_only)


@router.post("/amenities/room", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_room_amenity(
    data: RoomAmenityCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new room amenity."""
    service = HotelService(db)
    return await service.create_room_amenity(**data.model_dump())


# =============================================================================
# MEAL PLANS
# =============================================================================

@router.get("/meal-plans", response_model=List[MealPlanResponse])
async def list_meal_plans(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all meal plans."""
    service = HotelService(db)
    return await service.get_meal_plans(active_only=active_only)


@router.post("/meal-plans", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    data: MealPlanCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new meal plan."""
    service = HotelService(db)
    return await service.create_meal_plan(**data.model_dump())


# =============================================================================
# ROOM TYPES
# =============================================================================

@router.get("/room-types", response_model=List[RoomTypeResponse])
async def list_room_types(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all room types."""
    service = HotelService(db)
    return await service.get_room_types(active_only=active_only)


@router.post("/room-types", response_model=RoomTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_room_type(
    data: RoomTypeCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new room type."""
    service = HotelService(db)
    return await service.create_room_type(**data.model_dump())


@router.put("/room-types/{room_type_id}", response_model=RoomTypeResponse)
async def update_room_type(
    room_type_id: int,
    data: RoomTypeUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a room type."""
    service = HotelService(db)
    room_type = await service.update_room_type(room_type_id, **data.model_dump(exclude_unset=True))
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")
    return room_type


# =============================================================================
# HOTELS
# =============================================================================

@router.get("/", response_model=HotelListResponse)
async def list_hotels(
    city: Optional[str] = None,
    category_id: Optional[int] = None,
    star_rating: Optional[int] = None,
    is_featured: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session)
):
    """List all hotels with filters."""
    service = HotelService(db)
    hotels, total = await service.get_hotels(
        city=city,
        category_id=category_id,
        star_rating=star_rating,
        is_featured=is_featured,
        page=page,
        page_size=page_size
    )
    return HotelListResponse(
        items=hotels,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/search", response_model=HotelSearchResponse)
async def search_hotels(
    params: HotelSearchParams,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session)
):
    """Search hotels with availability check."""
    service = HotelService(db)
    hotels, total, filters = await service.search_hotels(
        query=params.query,
        city=params.city,
        state=params.state,
        star_rating=params.star_rating,
        category_id=params.category_id,
        min_price=params.min_price,
        max_price=params.max_price,
        amenity_ids=params.amenity_ids,
        check_in=params.check_in,
        check_out=params.check_out,
        rooms=params.rooms,
        page=page,
        page_size=page_size
    )
    return HotelSearchResponse(
        hotels=hotels,
        total=total,
        page=page,
        page_size=page_size,
        filters_applied=filters
    )


@router.post("/", response_model=HotelDetail, status_code=status.HTTP_201_CREATED)
async def create_hotel(
    data: HotelCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new hotel."""
    service = HotelService(db)
    hotel = await service.create_hotel(created_by_id=current_user.id, **data.model_dump())
    return await service.get_hotel(hotel.id)


@router.get("/{hotel_id}", response_model=HotelDetail)
async def get_hotel(
    hotel_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get hotel details with rooms."""
    service = HotelService(db)
    hotel = await service.get_hotel(hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


@router.get("/slug/{slug}", response_model=HotelDetail)
async def get_hotel_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_database_session)
):
    """Get hotel by slug."""
    service = HotelService(db)
    hotel = await service.get_hotel_by_slug(slug)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


@router.put("/{hotel_id}", response_model=HotelDetail)
async def update_hotel(
    hotel_id: int,
    data: HotelUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update hotel."""
    service = HotelService(db)
    hotel = await service.update_hotel(hotel_id, **data.model_dump(exclude_unset=True))
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return await service.get_hotel(hotel_id)


@router.delete("/{hotel_id}")
async def delete_hotel(
    hotel_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete hotel."""
    service = HotelService(db)
    deleted = await service.delete_hotel(hotel_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {"message": "Hotel deleted successfully"}


# =============================================================================
# HOTEL ROOMS
# =============================================================================

@router.get("/{hotel_id}/rooms", response_model=List[HotelRoomResponse])
async def list_hotel_rooms(
    hotel_id: int,
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all rooms for a hotel."""
    service = HotelService(db)
    return await service.get_hotel_rooms(hotel_id, active_only=active_only)


@router.post("/{hotel_id}/rooms", response_model=HotelRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel_room(
    hotel_id: int,
    data: HotelRoomCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new room for hotel."""
    service = HotelService(db)
    room = await service.create_room(hotel_id, **data.model_dump())
    return await service.get_room(room.id)


@router.get("/rooms/{room_id}", response_model=HotelRoomResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get room details."""
    service = HotelService(db)
    room = await service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.put("/rooms/{room_id}", response_model=HotelRoomResponse)
async def update_room(
    room_id: int,
    data: HotelRoomUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update room."""
    service = HotelService(db)
    room = await service.update_room(room_id, **data.model_dump(exclude_unset=True))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete room."""
    service = HotelService(db)
    deleted = await service.delete_room(room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted successfully"}


# =============================================================================
# ROOM RATES
# =============================================================================

@router.get("/rooms/{room_id}/rates", response_model=List[HotelRateResponse])
async def list_room_rates(
    room_id: int,
    active_only: bool = True,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get rates for a room."""
    service = HotelService(db)
    return await service.get_room_rates(room_id, active_only=active_only, as_of_date=as_of_date)


@router.post("/rates", response_model=HotelRateResponse, status_code=status.HTTP_201_CREATED)
async def create_rate(
    data: HotelRateCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new rate."""
    service = HotelService(db)
    rate = await service.create_rate(**data.model_dump())
    return await service.get_rate(rate.id)


@router.put("/rates/{rate_id}", response_model=HotelRateResponse)
async def update_rate(
    rate_id: int,
    data: HotelRateUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update rate."""
    service = HotelService(db)
    rate = await service.update_rate(rate_id, **data.model_dump(exclude_unset=True))
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    return rate


@router.delete("/rates/{rate_id}")
async def delete_rate(
    rate_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete rate."""
    service = HotelService(db)
    deleted = await service.delete_rate(rate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rate not found")
    return {"message": "Rate deleted successfully"}


# =============================================================================
# CONTRACTS
# =============================================================================

@router.get("/{hotel_id}/contracts", response_model=List[HotelContractResponse])
async def list_hotel_contracts(
    hotel_id: int,
    status: Optional[ContractStatus] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get contracts for a hotel."""
    service = HotelService(db)
    return await service.get_hotel_contracts(hotel_id, status=status)


@router.post("/contracts", response_model=HotelContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: HotelContractCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new contract."""
    service = HotelService(db)
    return await service.create_contract(created_by_id=current_user.id, **data.model_dump())


@router.put("/contracts/{contract_id}", response_model=HotelContractResponse)
async def update_contract(
    contract_id: int,
    data: HotelContractUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update contract."""
    service = HotelService(db)
    contract = await service.update_contract(contract_id, **data.model_dump(exclude_unset=True))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


# =============================================================================
# INVENTORY
# =============================================================================

@router.get("/rooms/{room_id}/inventory", response_model=List[RoomInventoryResponse])
async def get_room_inventory(
    room_id: int,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_database_session)
):
    """Get room inventory for date range."""
    service = HotelInventoryService(db)
    inventory = await service.get_inventory(room_id, start_date, end_date)
    return [
        RoomInventoryResponse(
            id=inv.id,
            room_id=inv.room_id,
            inventory_date=inv.inventory_date,
            total_rooms=inv.total_rooms,
            booked_rooms=inv.booked_rooms,
            blocked_rooms=inv.blocked_rooms,
            available_rooms=inv.available_rooms,
            stop_sale=inv.stop_sale,
            stop_sale_reason=inv.stop_sale_reason,
            cutoff_days=inv.cutoff_days,
            rate_override=inv.rate_override,
            updated_at=inv.updated_at
        )
        for inv in inventory
    ]


@router.put("/rooms/{room_id}/inventory/{inventory_date}", response_model=RoomInventoryResponse)
async def update_room_inventory(
    room_id: int,
    inventory_date: date,
    data: RoomInventoryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update inventory for a specific date."""
    service = HotelInventoryService(db)
    inventory = await service.update_inventory(
        room_id=room_id,
        inventory_date=inventory_date,
        updated_by_id=current_user.id,
        **data.model_dump(exclude_unset=True)
    )
    return RoomInventoryResponse(
        id=inventory.id,
        room_id=inventory.room_id,
        inventory_date=inventory.inventory_date,
        total_rooms=inventory.total_rooms,
        booked_rooms=inventory.booked_rooms,
        blocked_rooms=inventory.blocked_rooms,
        available_rooms=inventory.available_rooms,
        stop_sale=inventory.stop_sale,
        stop_sale_reason=inventory.stop_sale_reason,
        cutoff_days=inventory.cutoff_days,
        rate_override=inventory.rate_override,
        updated_at=inventory.updated_at
    )


@router.post("/inventory/bulk-update")
async def bulk_update_inventory(
    data: BulkInventoryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Bulk update inventory for date range."""
    service = HotelInventoryService(db)
    count = await service.bulk_update_inventory(
        room_id=data.room_id,
        start_date=data.start_date,
        end_date=data.end_date,
        updated_by_id=current_user.id,
        total_rooms=data.total_rooms,
        blocked_rooms=data.blocked_rooms,
        stop_sale=data.stop_sale,
        rate_override=data.rate_override
    )
    return {"message": f"Updated inventory for {count} days"}


# =============================================================================
# AVAILABILITY CHECK
# =============================================================================

@router.post("/availability")
async def check_availability(
    data: AvailabilityRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Check room availability for dates."""
    hotel_service = HotelService(db)
    inventory_service = HotelInventoryService(db)
    
    hotel = await hotel_service.get_hotel(data.hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    rooms_available = []
    
    if data.room_id:
        # Check specific room
        available, count = await inventory_service.check_availability(
            data.room_id, data.check_in, data.check_out, data.rooms
        )
        if available:
            room = await hotel_service.get_room(data.room_id)
            rates = await hotel_service.get_room_rates(data.room_id, as_of_date=data.check_in)
            if room and rates:
                rate = rates[0]
                nights = (data.check_out - data.check_in).days
                rooms_available.append({
                    "room_id": room.id,
                    "room_name": room.name,
                    "room_type": room.room_type.name if room.room_type else "Standard",
                    "available_rooms": count,
                    "rate": float(rate.double_rate),
                    "rate_type": rate.rate_type.value,
                    "meal_plan": rate.meal_plan.name if rate.meal_plan else None,
                    "taxes": float(rate.tax_percentage),
                    "total_per_night": float(rate.double_rate) * (1 + rate.tax_percentage / 100),
                    "total_for_stay": float(rate.double_rate) * nights * (1 + rate.tax_percentage / 100)
                })
    else:
        # Check all rooms
        rooms = await hotel_service.get_hotel_rooms(data.hotel_id)
        for room in rooms:
            available, count = await inventory_service.check_availability(
                room.id, data.check_in, data.check_out, data.rooms
            )
            if available and count > 0:
                rates = await hotel_service.get_room_rates(room.id, as_of_date=data.check_in)
                if rates:
                    rate = rates[0]
                    nights = (data.check_out - data.check_in).days
                    rooms_available.append({
                        "room_id": room.id,
                        "room_name": room.name,
                        "room_type": room.room_type.name if room.room_type else "Standard",
                        "available_rooms": count,
                        "rate": float(rate.double_rate),
                        "rate_type": rate.rate_type.value,
                        "meal_plan": rate.meal_plan.name if rate.meal_plan else None,
                        "taxes": float(rate.tax_percentage),
                        "total_per_night": float(rate.double_rate) * (1 + rate.tax_percentage / 100),
                        "total_for_stay": float(rate.double_rate) * nights * (1 + rate.tax_percentage / 100)
                    })
    
    return {
        "hotel_id": data.hotel_id,
        "hotel_name": hotel.name,
        "check_in": data.check_in,
        "check_out": data.check_out,
        "nights": (data.check_out - data.check_in).days,
        "rooms_available": rooms_available
    }


# =============================================================================
# ENQUIRIES
# =============================================================================

@router.post("/enquiries", response_model=HotelEnquiryResponse, status_code=status.HTTP_201_CREATED)
async def create_enquiry(
    data: HotelEnquiryCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new enquiry."""
    service = HotelInventoryService(db)
    user_id = current_user.id if current_user else None
    return await service.create_enquiry(user_id=user_id, **data.model_dump())


@router.get("/enquiries", response_model=HotelEnquiryListResponse)
async def list_enquiries(
    hotel_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """List enquiries (admin only)."""
    service = HotelInventoryService(db)
    enquiries, total = await service.get_enquiries(
        hotel_id=hotel_id,
        status=status,
        page=page,
        page_size=page_size
    )
    return HotelEnquiryListResponse(
        items=enquiries,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/enquiries/{enquiry_id}", response_model=HotelEnquiryResponse)
async def get_enquiry(
    enquiry_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get enquiry details."""
    service = HotelInventoryService(db)
    enquiry = await service.get_enquiry(enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return enquiry


@router.put("/enquiries/{enquiry_id}", response_model=HotelEnquiryResponse)
async def update_enquiry(
    enquiry_id: int,
    data: HotelEnquiryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update enquiry."""
    service = HotelInventoryService(db)
    enquiry = await service.update_enquiry(enquiry_id, **data.model_dump(exclude_unset=True))
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return enquiry


# =============================================================================
# BOOKINGS
# =============================================================================

@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new offline hotel booking."""
    hotel_service = HotelService(db)
    inventory_service = HotelInventoryService(db)
    
    # Check availability
    available, _ = await inventory_service.check_availability(
        data.room_id, data.check_in_date, data.check_out_date, data.rooms_booked
    )
    if not available:
        raise HTTPException(status_code=400, detail="Room not available for selected dates")
    
    # Get rate
    rates = await hotel_service.get_room_rates(data.room_id, as_of_date=data.check_in_date)
    if not rates:
        raise HTTPException(status_code=400, detail="No rate found for selected room and dates")
    
    rate = rates[0]
    room_rate = float(rate.double_rate)
    tax_percentage = float(rate.tax_percentage) if rate.tax_percentage else 0
    
    booking_data = data.model_dump()
    booking_data['room_rate'] = room_rate
    booking_data['taxes'] = room_rate * (data.check_out_date - data.check_in_date).days * data.rooms_booked * (tax_percentage / 100)
    
    booking = await inventory_service.create_booking(
        user_id=current_user.id,
        created_by_id=current_user.id,
        **booking_data
    )
    return booking


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    hotel_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    check_in_from: Optional[date] = None,
    check_in_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """List bookings (admin only)."""
    service = HotelInventoryService(db)
    bookings, total = await service.get_bookings(
        hotel_id=hotel_id,
        status=status,
        check_in_from=check_in_from,
        check_in_to=check_in_to,
        page=page,
        page_size=page_size
    )
    return BookingListResponse(
        items=bookings,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/bookings/{booking_id}", response_model=BookingDetail)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """Get booking details."""
    service = HotelInventoryService(db)
    booking = await service.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    data: BookingUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update booking."""
    service = HotelInventoryService(db)
    booking = await service.update_booking(booking_id, **data.model_dump(exclude_unset=True))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    data: BookingCancellation,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Cancel a booking."""
    service = HotelInventoryService(db)
    booking = await service.cancel_booking(
        booking_id,
        reason=data.cancellation_reason,
        cancellation_charges=data.cancellation_charges,
        refund_amount=data.refund_amount
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
