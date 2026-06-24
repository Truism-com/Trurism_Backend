"""
Booking API Endpoints

This module defines FastAPI endpoints for booking operations:
- Flight booking creation and management
- Hotel booking creation and management
- Bus booking creation and management
- Booking listing and details
- Booking cancellation and refunds
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
import logging

from app.core.database import get_database_session
from app.core.redis import get_redis_client
from app.auth.api import get_current_user, get_approved_agent
from app.auth.models import User
from app.booking.schemas import (
    FlightBookingRequest, HotelBookingRequest, BusBookingRequest,
    FlightBookingResponse, HotelBookingResponse, BusBookingResponse,
    BookingListResponse, BookingDetailsResponse, CancelBookingRequest,
    CancelBookingResponse, BookingStatusResponse
)
from app.booking.services import FlightBookingService, HotelBookingService, BusBookingService
from app.booking.models import BookingStatus

# Router for booking endpoints
router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/flights", response_model=FlightBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_flight_booking(
    booking_request: FlightBookingRequest,
    current_user: User = Depends(get_approved_agent),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new flight booking.
    
    This endpoint creates a flight booking for the authenticated user.
    It processes payment and confirms the booking if payment is successful.
    Automatically tracks who created the booking (salesperson/agent tracking).
    
    Args:
        booking_request: Flight booking request data
        current_user: Current authenticated user (who created this booking)
        db: Database session
        
    Returns:
        FlightBookingResponse: Created flight booking details
        
    Raises:
        HTTPException: If booking creation fails or payment fails
    """
    try:
        flight_data = None

        # Retrieve cached search results
        redis_client = get_redis_client()
        if redis_client is not None:
            cache_key = f"search:flight:{booking_request.search_id}"
            try:
                cached_data_str = await redis_client.get(cache_key)
                if cached_data_str:
                    cached_data = json.loads(cached_data_str)
                    for result in cached_data.get("results", []):
                        if result.get("offer_id") == booking_request.offer_id:
                            flight_data = result
                            break
            except Exception as redis_err:
                logging.getLogger(__name__).warning(f"Redis read during booking: {redis_err}")

        if flight_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Flight offer not found in search cache. Please search again before booking."
            )

        tenant_id = getattr(request.state, "tenant_id", None)
        booking_service = FlightBookingService(db, tenant_id=tenant_id)

        booking = await booking_service.create_flight_booking(
            current_user, booking_request, flight_data, created_by_user=current_user
        )
        
        return FlightBookingResponse.model_validate(booking)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(f"Flight booking creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Flight booking creation failed. Please try again."
        )


@router.post("/hotels", response_model=HotelBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel_booking(
    booking_request: HotelBookingRequest,
    current_user: User = Depends(get_approved_agent),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new hotel booking.
    
    This endpoint creates a hotel booking for the authenticated user.
    It processes payment and confirms the booking if payment is successful.
    Automatically tracks who created the booking (salesperson/agent tracking).
    
    Args:
        booking_request: Hotel booking request data
        current_user: Current authenticated user (who created this booking)
        db: Database session
        
    Returns:
        HotelBookingResponse: Created hotel booking details
        
    Raises:
        HTTPException: If booking creation fails or payment fails
    """
    try:
        # Look up hotel data from cached search results
        redis_client = get_redis_client()
        if redis_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search cache is unavailable. Please try again later."
            )

        hotel_data = None
        cache_key = f"search:hotel:{booking_request.search_id}"
        try:
            cached_data_str = await redis_client.get(cache_key)
            if cached_data_str:
                cached_data = json.loads(cached_data_str)
                for result in cached_data.get("results", []):
                    if result.get("hotel_id") == booking_request.hotel_id:
                        hotel_data = result
                        break
        except Exception as redis_err:
            logging.getLogger(__name__).error(f"Redis read error during hotel booking: {redis_err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search cache is unavailable. Please try again later."
            )

        if not hotel_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired search_id, or the requested hotel was not found in the search results."
            )

        tenant_id = getattr(request.state, "tenant_id", None)
        booking_service = HotelBookingService(db, tenant_id=tenant_id)
        # Track who created this booking (for B2B agent tracking)
        booking = await booking_service.create_hotel_booking(
            current_user, booking_request, hotel_data, created_by_user=current_user
        )
        
        return HotelBookingResponse.model_validate(booking)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hotel booking creation failed. Please try again."
        )


@router.post("/buses", response_model=BusBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_bus_booking(
    booking_request: BusBookingRequest,
    current_user: User = Depends(get_approved_agent),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new bus booking.
    
    This endpoint creates a bus booking for the authenticated user.
    It processes payment and confirms the booking if payment is successful.
    Automatically tracks who created the booking (salesperson/agent tracking).
    
    Args:
        booking_request: Bus booking request data
        current_user: Current authenticated user (who created this booking)
        db: Database session
        
    Returns:
        BusBookingResponse: Created bus booking details
        
    Raises:
        HTTPException: If booking creation fails or payment fails
    """
    try:
        # Look up bus data from cached search results
        redis_client = get_redis_client()
        if redis_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search cache is unavailable. Please try again later."
            )

        bus_data = None
        cache_key = f"search:bus:{booking_request.search_id}"
        try:
            cached_data_str = await redis_client.get(cache_key)
            if cached_data_str:
                cached_data = json.loads(cached_data_str)
                for result in cached_data.get("results", []):
                    if result.get("bus_id") == booking_request.bus_id:
                        bus_data = result
                        break
        except Exception as redis_err:
            logging.getLogger(__name__).error(f"Redis read error during bus booking: {redis_err}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search cache is unavailable. Please try again later."
            )

        if not bus_data:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Bus search integration is not yet available. Cannot verify bus pricing."
            )

        tenant_id = getattr(request.state, "tenant_id", None)
        booking_service = BusBookingService(db, tenant_id=tenant_id)
        # Track who created this booking (for B2B agent tracking)
        booking = await booking_service.create_bus_booking(
            current_user, booking_request, bus_data, created_by_user=current_user
        )
        
        return BusBookingResponse.model_validate(booking)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bus booking creation failed. Please try again."
        )


@router.get("/", response_model=BookingListResponse)
async def get_user_bookings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Number of bookings per page"),
    status_filter: Optional[BookingStatus] = Query(None, alias="status", description="Filter by booking status"),
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get user's bookings with pagination and filtering.
    
    This endpoint returns a paginated list of all bookings for the
    authenticated user with optional status filtering.
    
    Args:
        page: Page number for pagination
        size: Number of bookings per page
        status: Optional booking status filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BookingListResponse: Paginated list of user bookings
    """
    try:
        tenant_id = getattr(request.state, "tenant_id", None)
        # Get bookings from all services
        flight_service = FlightBookingService(db, tenant_id=tenant_id)
        hotel_service = HotelBookingService(db, tenant_id=tenant_id)
        bus_service = BusBookingService(db, tenant_id=tenant_id)
        
        # Fetch all matching bookings from each service (no DB-level pagination;
        # we combine and paginate over the merged set so the total count and
        # page boundaries are correct across booking types).
        flight_bookings = await flight_service.get_user_flight_bookings(
            current_user.id, 0, 10000, status_filter
        )
        hotel_bookings = await hotel_service.get_user_hotel_bookings(
            current_user.id, 0, 10000, status_filter
        )
        bus_bookings = await bus_service.get_user_bus_bookings(
            current_user.id, 0, 10000, status_filter
        )
        
        # Combine and format bookings
        all_bookings = []
        
        # Add flight bookings
        for booking in flight_bookings:
            all_bookings.append({
                "booking_id": booking.id,
                "type": "flight",
                "booking_reference": booking.booking_reference,
                "status": booking.status,
                "total_amount": booking.total_amount,
                "currency": booking.currency,
                "created_at": booking.created_at,
                "airline": booking.airline,
                "origin": booking.origin,
                "destination": booking.destination,
                "departure_time": booking.departure_time
            })
        
        # Add hotel bookings
        for booking in hotel_bookings:
            all_bookings.append({
                "booking_id": booking.id,
                "type": "hotel",
                "booking_reference": booking.booking_reference,
                "status": booking.status,
                "total_amount": booking.total_amount,
                "currency": booking.currency,
                "created_at": booking.created_at,
                "hotel_name": booking.hotel_name,
                "city": booking.city,
                "checkin_date": booking.checkin_date,
                "checkout_date": booking.checkout_date
            })
        
        # Add bus bookings
        for booking in bus_bookings:
            all_bookings.append({
                "booking_id": booking.id,
                "type": "bus",
                "booking_reference": booking.booking_reference,
                "status": booking.status,
                "total_amount": booking.total_amount,
                "currency": booking.currency,
                "created_at": booking.created_at,
                "operator": booking.operator,
                "origin": booking.origin,
                "destination": booking.destination,
                "departure_time": booking.departure_time
            })
        
        # Sort by creation date (most recent first) then apply pagination
        all_bookings.sort(key=lambda x: x["created_at"], reverse=True)
        total = len(all_bookings)
        skip = (page - 1) * size
        page_bookings = all_bookings[skip: skip + size]

        return BookingListResponse(
            total=total,
            page=page,
            size=size,
            bookings=page_bookings
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings. Please try again."
        )


@router.get("/{booking_id}", response_model=BookingDetailsResponse)
async def get_booking_details(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get detailed information for a specific booking.
    
    This endpoint returns comprehensive details for a booking including
    passenger information, booking status, and payment details.
    
    Args:
        booking_id: Booking ID to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        BookingDetailsResponse: Detailed booking information
        
    Raises:
        HTTPException: If booking not found or doesn't belong to user
    """
    try:
        tenant_id = getattr(request.state, "tenant_id", None)
        # Try to find booking in each service
        flight_service = FlightBookingService(db, tenant_id=tenant_id)
        hotel_service = HotelBookingService(db, tenant_id=tenant_id)
        bus_service = BusBookingService(db, tenant_id=tenant_id)
        
        # Check flight bookings
        flight_booking = await flight_service.get_flight_booking(booking_id, current_user.id)
        if flight_booking:
            return BookingDetailsResponse(
                booking_id=flight_booking.id,
                booking_reference=flight_booking.booking_reference,
                type="flight",
                status=flight_booking.status,
                total_amount=flight_booking.total_amount,
                currency=flight_booking.currency,
                payment_status=flight_booking.payment_status,
                details={
                    "airline": flight_booking.airline,
                    "flight_number": flight_booking.flight_number,
                    "origin": flight_booking.origin,
                    "destination": flight_booking.destination,
                    "departure_time": flight_booking.departure_time,
                    "arrival_time": flight_booking.arrival_time,
                    "travel_class": flight_booking.travel_class,
                    "passenger_count": flight_booking.passenger_count,
                    "base_fare": flight_booking.base_fare,
                    "taxes": flight_booking.taxes,
                    "confirmation_number": flight_booking.confirmation_number
                },
                passenger_details=flight_booking.passenger_details,
                created_at=flight_booking.created_at,
                updated_at=flight_booking.updated_at
            )
        
        # Check hotel bookings
        hotel_booking = await hotel_service.get_hotel_booking(booking_id, current_user.id)
        if hotel_booking:
            return BookingDetailsResponse(
                booking_id=hotel_booking.id,
                booking_reference=hotel_booking.booking_reference,
                type="hotel",
                status=hotel_booking.status,
                total_amount=hotel_booking.total_amount,
                currency=hotel_booking.currency,
                payment_status=hotel_booking.payment_status,
                details={
                    "hotel_name": hotel_booking.hotel_name,
                    "hotel_address": hotel_booking.hotel_address,
                    "city": hotel_booking.city,
                    "checkin_date": hotel_booking.checkin_date,
                    "checkout_date": hotel_booking.checkout_date,
                    "nights": hotel_booking.nights,
                    "rooms": hotel_booking.rooms,
                    "adults": hotel_booking.adults,
                    "children": hotel_booking.children,
                    "room_rate": hotel_booking.room_rate,
                    "confirmation_number": hotel_booking.confirmation_number,
                    "cancellation_policy": hotel_booking.cancellation_policy
                },
                passenger_details=hotel_booking.guest_details,
                created_at=hotel_booking.created_at,
                updated_at=hotel_booking.updated_at
            )
        
        # Check bus bookings
        bus_booking = await bus_service.get_bus_booking(booking_id, current_user.id)
        if bus_booking:
            return BookingDetailsResponse(
                booking_id=bus_booking.id,
                booking_reference=bus_booking.booking_reference,
                type="bus",
                status=bus_booking.status,
                total_amount=bus_booking.total_amount,
                currency=bus_booking.currency,
                payment_status=bus_booking.payment_status,
                details={
                    "operator": bus_booking.operator,
                    "bus_type": bus_booking.bus_type,
                    "origin": bus_booking.origin,
                    "destination": bus_booking.destination,
                    "departure_time": bus_booking.departure_time,
                    "arrival_time": bus_booking.arrival_time,
                    "travel_date": bus_booking.travel_date,
                    "passengers": bus_booking.passengers,
                    "fare_per_passenger": bus_booking.fare_per_passenger,
                    "boarding_point": bus_booking.boarding_point,
                    "dropping_point": bus_booking.dropping_point,
                    "confirmation_number": bus_booking.confirmation_number
                },
                passenger_details=bus_booking.passenger_details,
                created_at=bus_booking.created_at,
                updated_at=bus_booking.updated_at
            )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking details. Please try again."
        )


@router.put("/{booking_id}/cancel", response_model=CancelBookingResponse)
async def cancel_booking(
    booking_id: int,
    cancel_request: CancelBookingRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Cancel a booking.
    
    This endpoint cancels a booking and processes any applicable refunds
    based on the cancellation policy and timing.
    
    Args:
        booking_id: Booking ID to cancel
        cancel_request: Cancellation details
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CancelBookingResponse: Cancellation confirmation and refund details
        
    Raises:
        HTTPException: If booking not found or cannot be cancelled
    """
    try:
        tenant_id = getattr(request.state, "tenant_id", None)
        # Try to cancel booking in each service
        flight_service = FlightBookingService(db, tenant_id=tenant_id)
        hotel_service = HotelBookingService(db, tenant_id=tenant_id)
        bus_service = BusBookingService(db, tenant_id=tenant_id)
        
        # Check flight bookings
        flight_booking = await flight_service.get_flight_booking(booking_id, current_user.id)
        if flight_booking:
            cancelled_booking = await flight_service.cancel_flight_booking(
                booking_id, current_user.id, cancel_request
            )
            booking_type = "flight"
        else:
            # Check hotel bookings
            hotel_booking = await hotel_service.get_hotel_booking(booking_id, current_user.id)
            if hotel_booking:
                cancelled_booking = await hotel_service.cancel_hotel_booking(
                    booking_id, current_user.id, cancel_request
                )
                booking_type = "hotel"
            else:
                # Check bus bookings
                bus_booking = await bus_service.get_bus_booking(booking_id, current_user.id)
                if bus_booking:
                    cancelled_booking = await bus_service.cancel_bus_booking(
                        booking_id, current_user.id, cancel_request
                    )
                    booking_type = "bus"
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Booking not found"
                    )
        
        # Calculate cancellation fee
        cancellation_fee = cancelled_booking.total_amount - (cancelled_booking.refund_amount or 0)
        
        # Determine refund processing time
        refund_processing_time = None
        if cancelled_booking.refund_amount and cancelled_booking.refund_amount > 0:
            refund_processing_time = "5-7 business days"
        
        return CancelBookingResponse(
            booking_id=cancelled_booking.id,
            status=cancelled_booking.status,
            refund_amount=cancelled_booking.refund_amount,
            currency=cancelled_booking.currency,
            refund_processing_time=refund_processing_time,
            cancellation_fee=cancellation_fee if cancellation_fee > 0 else None,
            message=f"Your {booking_type} booking has been cancelled successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking. Please try again."
        )


@router.get("/flights/{booking_id}/status", response_model=BookingStatusResponse)
async def get_flight_booking_status(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get current status of a flight booking.

    Poll this after POST /bookings/flights to track when status
    moves from pending to confirmed or ticketing_failed.
    Returns pnr and airiq_booking_id once confirmed.
    """
    from sqlalchemy import select
    from app.booking.models import FlightBooking

    tenant_id = getattr(request.state, "tenant_id", None)
    try:
        query = select(FlightBooking).where(
            FlightBooking.id == booking_id,
            FlightBooking.user_id == current_user.id,
        )
        if tenant_id:
            query = query.where(FlightBooking.tenant_id == tenant_id)

        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flight booking not found"
            )

        return BookingStatusResponse.model_validate(booking)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking status. Please try again."
        )
