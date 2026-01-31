"""
Activity API

REST endpoints for activity operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, time

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.activities.models import ActivityStatus, BookingStatus
from app.activities.services import ActivityService
from app.activities.schemas import (
    # Category schemas
    CategoryCreate, CategoryUpdate, CategoryResponse,
    # Location schemas
    LocationCreate, LocationUpdate, LocationResponse,
    # Slot schemas
    SlotCreate, SlotUpdate, SlotResponse,
    # Activity schemas
    ActivityCreate, ActivityUpdate, ActivityListItem, ActivityDetail,
    ActivitySearchParams, ActivitySearchResponse,
    # Booking schemas
    BookingCreate, BookingUpdate, BookingResponse, BookingDetail, BookingListResponse
)

router = APIRouter(prefix="/activities", tags=["Activities"])


# =============================================================================
# Category Endpoints
# =============================================================================

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all activity categories."""
    service = ActivityService(db)
    categories = await service.get_categories(active_only=active_only)
    return categories


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new activity category."""
    service = ActivityService(db)
    category = await service.create_category(**data.model_dump())
    return category


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get category by ID."""
    service = ActivityService(db)
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a category."""
    service = ActivityService(db)
    category = await service.update_category(category_id, **data.model_dump(exclude_unset=True))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# =============================================================================
# Location Endpoints
# =============================================================================

@router.get("/locations", response_model=List[LocationResponse])
async def list_locations(
    active_only: bool = True,
    popular_only: bool = False,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all activity locations."""
    service = ActivityService(db)
    locations = await service.get_locations(
        active_only=active_only,
        popular_only=popular_only,
        city=city
    )
    return locations


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new activity location."""
    service = ActivityService(db)
    location = await service.create_location(**data.model_dump())
    return location


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get location by ID."""
    service = ActivityService(db)
    location = await service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    data: LocationUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a location."""
    service = ActivityService(db)
    location = await service.update_location(location_id, **data.model_dump(exclude_unset=True))
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


# =============================================================================
# Activity Endpoints
# =============================================================================

@router.get("", response_model=ActivitySearchResponse)
async def search_activities(
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    activity_date: Optional[date] = None,
    is_featured: Optional[bool] = None,
    sort_by: str = Query("display_order", regex="^(display_order|price_asc|price_desc|rating|newest)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session)
):
    """Search activities with filters."""
    service = ActivityService(db)
    result = await service.search_activities(
        query=query,
        category_id=category_id,
        location_id=location_id,
        city=city,
        min_price=min_price,
        max_price=max_price,
        activity_date=activity_date,
        is_featured=is_featured,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/featured", response_model=List[ActivityListItem])
async def get_featured_activities(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session)
):
    """Get featured activities."""
    service = ActivityService(db)
    activities = await service.get_featured_activities(limit=limit)
    return activities


@router.post("", response_model=ActivityDetail, status_code=status.HTTP_201_CREATED)
async def create_activity(
    data: ActivityCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new activity."""
    service = ActivityService(db)
    
    activity_data = data.model_dump()
    slots = activity_data.pop('slots', None)
    
    activity = await service.create_activity(
        created_by_id=int(current_user.id),
        slots=[s for s in slots] if slots else None,
        **activity_data
    )
    
    # Reload with all relationships
    activity = await service.get_activity(activity.id, include_slots=True)
    return activity


@router.get("/{activity_id}", response_model=ActivityDetail)
async def get_activity_by_id(
    activity_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get activity details by ID."""
    service = ActivityService(db)
    activity = await service.get_activity(activity_id, include_slots=True)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.get("/slug/{slug}", response_model=ActivityDetail)
async def get_activity_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_database_session)
):
    """Get activity by slug."""
    service = ActivityService(db)
    activity = await service.get_activity(slug=slug, include_slots=True)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.put("/{activity_id}", response_model=ActivityDetail)
async def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an activity."""
    service = ActivityService(db)
    activity = await service.update_activity(activity_id, **data.model_dump(exclude_unset=True))
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity = await service.get_activity(activity_id, include_slots=True)
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete an activity (soft delete)."""
    service = ActivityService(db)
    deleted = await service.delete_activity(activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Activity not found")
    return None


# =============================================================================
# Slot Endpoints
# =============================================================================

@router.get("/{activity_id}/slots", response_model=List[SlotResponse])
async def get_activity_slots(
    activity_id: int,
    slot_date: Optional[date] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get available slots for an activity."""
    service = ActivityService(db)
    slots = await service.get_slots(activity_id, slot_date=slot_date)
    return slots


@router.post("/{activity_id}/slots", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
async def add_slot(
    activity_id: int,
    data: SlotCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Add a time slot to an activity."""
    service = ActivityService(db)
    
    # Verify activity exists
    activity = await service.get_activity(activity_id, include_slots=False)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    slot = await service.add_slot(activity_id, **data.model_dump())
    return slot


@router.put("/slots/{slot_id}", response_model=SlotResponse)
async def update_slot(
    slot_id: int,
    data: SlotUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a slot."""
    service = ActivityService(db)
    slot = await service.update_slot(slot_id, **data.model_dump(exclude_unset=True))
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a slot."""
    service = ActivityService(db)
    deleted = await service.delete_slot(slot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Slot not found")
    return None


# =============================================================================
# Booking Endpoints
# =============================================================================

@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    Create an activity booking.
    
    Can be created by guest or authenticated user.
    """
    service = ActivityService(db)
    
    user_id = int(current_user.id) if current_user else None
    booking_data = data.model_dump()
    participants = booking_data.pop('participants', None)
    
    try:
        booking = await service.create_booking(
            user_id=user_id,
            participants=participants,
            **booking_data
        )
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status: Optional[BookingStatus] = None,
    activity_id: Optional[int] = None,
    booking_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """List all bookings (admin only)."""
    service = ActivityService(db)
    result = await service.list_bookings(
        status=status,
        activity_id=activity_id,
        booking_date=booking_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/bookings/{booking_id}", response_model=BookingDetail)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get booking details (admin)."""
    service = ActivityService(db)
    booking = await service.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.get("/bookings/ref/{booking_ref}", response_model=BookingResponse)
async def get_booking_by_ref(
    booking_ref: str,
    db: AsyncSession = Depends(get_database_session)
):
    """Get booking by reference (public - for customer)."""
    service = ActivityService(db)
    booking = await service.get_booking(booking_ref=booking_ref)
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
    """Update booking (admin)."""
    service = ActivityService(db)
    booking = await service.update_booking(booking_id, **data.model_dump(exclude_unset=True))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    reason: str,
    refund_amount: Optional[float] = None,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Cancel a booking."""
    service = ActivityService(db)
    booking = await service.cancel_booking(
        booking_id,
        reason=reason,
        refund_amount=refund_amount
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


# =============================================================================
# User Bookings
# =============================================================================

@router.get("/my/bookings", response_model=BookingListResponse)
async def get_my_bookings(
    status: Optional[BookingStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """Get current user's activity bookings."""
    service = ActivityService(db)
    result = await service.list_bookings(
        user_id=int(current_user.id),
        status=status,
        page=page,
        page_size=page_size
    )
    return result
