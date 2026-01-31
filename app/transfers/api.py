"""
Transfer API

REST endpoints for transfer/cab operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, time

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.transfers.models import TransferBookingStatus
from app.transfers.services import TransferService
from app.transfers.schemas import (
    # Car type schemas
    CarTypeCreate, CarTypeUpdate, CarTypeResponse,
    # Route schemas
    RouteCreate, RouteUpdate, RouteResponse, RouteSearchParams,
    # Booking schemas
    BookingCreate, BookingUpdate, BookingResponse, BookingDetail, BookingListResponse,
    # Price estimation
    PriceEstimateRequest, PriceEstimateResponse
)

router = APIRouter(prefix="/transfers", tags=["Transfers"])


# =============================================================================
# Car Type Endpoints
# =============================================================================

@router.get("/car-types", response_model=List[CarTypeResponse])
async def list_car_types(
    active_only: bool = True,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all car types."""
    service = TransferService(db)
    car_types = await service.get_car_types(active_only=active_only, category=category)
    return car_types


@router.post("/car-types", response_model=CarTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_car_type(
    data: CarTypeCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new car type."""
    service = TransferService(db)
    car_type = await service.create_car_type(**data.model_dump())
    return car_type


@router.get("/car-types/{car_type_id}", response_model=CarTypeResponse)
async def get_car_type(
    car_type_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get car type by ID."""
    service = TransferService(db)
    car_type = await service.get_car_type(car_type_id)
    if not car_type:
        raise HTTPException(status_code=404, detail="Car type not found")
    return car_type


@router.put("/car-types/{car_type_id}", response_model=CarTypeResponse)
async def update_car_type(
    car_type_id: int,
    data: CarTypeUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a car type."""
    service = TransferService(db)
    car_type = await service.update_car_type(car_type_id, **data.model_dump(exclude_unset=True))
    if not car_type:
        raise HTTPException(status_code=404, detail="Car type not found")
    return car_type


# =============================================================================
# Route Endpoints
# =============================================================================

@router.get("/routes", response_model=List[RouteResponse])
async def list_routes(
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
    car_type_id: Optional[int] = None,
    is_popular: Optional[bool] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get all routes with filters."""
    service = TransferService(db)
    routes = await service.get_routes(
        origin_city=origin_city,
        destination_city=destination_city,
        car_type_id=car_type_id,
        is_popular=is_popular
    )
    return routes


@router.get("/routes/popular", response_model=List[RouteResponse])
async def get_popular_routes(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session)
):
    """Get popular routes."""
    service = TransferService(db)
    routes = await service.get_popular_routes(limit=limit)
    return routes


@router.post("/routes", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    data: RouteCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new route."""
    service = TransferService(db)
    
    # Verify car type exists
    car_type = await service.get_car_type(data.car_type_id)
    if not car_type:
        raise HTTPException(status_code=404, detail="Car type not found")
    
    route = await service.create_route(**data.model_dump())
    return route


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get route by ID."""
    service = TransferService(db)
    route = await service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: int,
    data: RouteUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a route."""
    service = TransferService(db)
    route = await service.update_route(route_id, **data.model_dump(exclude_unset=True))
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


# =============================================================================
# Price Estimation
# =============================================================================

@router.post("/estimate-price", response_model=PriceEstimateResponse)
async def estimate_price(
    data: PriceEstimateRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get price estimate for a transfer.
    
    Public endpoint - no authentication required.
    """
    service = TransferService(db)
    
    try:
        estimate = await service.estimate_price(
            car_type_id=data.car_type_id,
            trip_type=data.trip_type,
            route_id=data.route_id,
            pickup_date=data.pickup_date,
            pickup_time=data.pickup_time,
            return_date=data.return_date,
            custom_distance_km=data.custom_distance_km
        )
        return estimate
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    Create a transfer booking.
    
    Can be created by guest or authenticated user.
    """
    service = TransferService(db)
    
    user_id = int(current_user.id) if current_user else None
    
    try:
        booking = await service.create_booking(
            user_id=user_id,
            **data.model_dump()
        )
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status: Optional[TransferBookingStatus] = None,
    route_id: Optional[int] = None,
    car_type_id: Optional[int] = None,
    pickup_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """List all bookings (admin only)."""
    service = TransferService(db)
    result = await service.list_bookings(
        status=status,
        route_id=route_id,
        car_type_id=car_type_id,
        pickup_date=pickup_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/bookings/today", response_model=List[BookingResponse])
async def get_today_bookings(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all bookings for today."""
    service = TransferService(db)
    bookings = await service.get_today_bookings()
    return bookings


@router.get("/bookings/{booking_id}", response_model=BookingDetail)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get booking details (admin)."""
    service = TransferService(db)
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
    service = TransferService(db)
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
    service = TransferService(db)
    booking = await service.update_booking(booking_id, **data.model_dump(exclude_unset=True))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Confirm a pending booking."""
    service = TransferService(db)
    booking = await service.confirm_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/start", response_model=BookingResponse)
async def start_trip(
    booking_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Mark trip as started."""
    service = TransferService(db)
    booking = await service.start_trip(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/{booking_id}/complete", response_model=BookingResponse)
async def complete_trip(
    booking_id: int,
    actual_km: Optional[float] = None,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Mark trip as completed."""
    service = TransferService(db)
    booking = await service.complete_trip(booking_id, actual_km=actual_km)
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
    service = TransferService(db)
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
    status: Optional[TransferBookingStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """Get current user's transfer bookings."""
    service = TransferService(db)
    result = await service.list_bookings(
        user_id=int(current_user.id),
        status=status,
        page=page,
        page_size=page_size
    )
    return result
