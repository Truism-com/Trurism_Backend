"""
Holiday Package API

REST endpoints for holiday package operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.holidays.models import PackageType, EnquiryStatus, PackageBookingStatus
from app.holidays.services import HolidayService, PackageEnquiryService
from app.holidays.schemas import (
    # Theme schemas
    ThemeCreate, ThemeUpdate, ThemeResponse,
    # Destination schemas
    DestinationCreate, DestinationUpdate, DestinationResponse,
    # Package schemas
    PackageCreate, PackageUpdate, PackageListItem, PackageDetail,
    PackageSearchParams, PackageSearchResponse,
    # Itinerary schemas
    ItineraryCreate, ItineraryUpdate, ItineraryResponse,
    # Inclusion schemas
    InclusionCreate, InclusionResponse,
    # Image schemas
    ImageCreate, ImageResponse,
    # Enquiry schemas
    EnquiryCreate, EnquiryUpdate, EnquiryResponse, EnquiryListResponse,
    # Booking schemas
    BookingCreate, BookingUpdate, BookingResponse, BookingListResponse
)

router = APIRouter(prefix="/holidays", tags=["Holidays"])


# =============================================================================
# Theme Endpoints (Public + Admin)
# =============================================================================

@router.get("/themes", response_model=List[ThemeResponse])
async def list_themes(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all package themes.
    
    Public endpoint - no authentication required.
    """
    service = HolidayService(db)
    themes = await service.get_themes(active_only=active_only)
    return themes


@router.post("/themes", response_model=ThemeResponse, status_code=status.HTTP_201_CREATED)
async def create_theme(
    data: ThemeCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new package theme.
    
    Requires admin authentication.
    """
    service = HolidayService(db)
    theme = await service.create_theme(**data.model_dump())
    return theme


@router.get("/themes/{theme_id}", response_model=ThemeResponse)
async def get_theme(
    theme_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get theme by ID."""
    service = HolidayService(db)
    theme = await service.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: int,
    data: ThemeUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a theme."""
    service = HolidayService(db)
    theme = await service.update_theme(theme_id, **data.model_dump(exclude_unset=True))
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.delete("/themes/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a theme (soft delete)."""
    service = HolidayService(db)
    deleted = await service.delete_theme(theme_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Theme not found")
    return None


# =============================================================================
# Destination Endpoints (Public + Admin)
# =============================================================================

@router.get("/destinations", response_model=List[DestinationResponse])
async def list_destinations(
    active_only: bool = True,
    international_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all destinations.
    
    Public endpoint.
    """
    service = HolidayService(db)
    destinations = await service.get_destinations(
        active_only=active_only,
        international_only=international_only
    )
    return destinations


@router.post("/destinations", response_model=DestinationResponse, status_code=status.HTTP_201_CREATED)
async def create_destination(
    data: DestinationCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new destination."""
    service = HolidayService(db)
    destination = await service.create_destination(**data.model_dump())
    return destination


@router.get("/destinations/{destination_id}", response_model=DestinationResponse)
async def get_destination(
    destination_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get destination by ID."""
    service = HolidayService(db)
    destination = await service.get_destination(destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination


@router.put("/destinations/{destination_id}", response_model=DestinationResponse)
async def update_destination(
    destination_id: int,
    data: DestinationUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a destination."""
    service = HolidayService(db)
    destination = await service.update_destination(
        destination_id,
        **data.model_dump(exclude_unset=True)
    )
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination


# =============================================================================
# Package Endpoints (Public + Admin)
# =============================================================================

@router.get("/packages", response_model=PackageSearchResponse)
async def search_packages(
    query: Optional[str] = None,
    theme_id: Optional[int] = None,
    destination_id: Optional[int] = None,
    min_nights: Optional[int] = None,
    max_nights: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    package_type: Optional[PackageType] = None,
    is_featured: Optional[bool] = None,
    sort_by: str = Query("display_order", regex="^(display_order|price_asc|price_desc|rating|newest)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search holiday packages with filters.
    
    Public endpoint - no authentication required.
    """
    service = HolidayService(db)
    result = await service.search_packages(
        query=query,
        theme_id=theme_id,
        destination_id=destination_id,
        min_nights=min_nights,
        max_nights=max_nights,
        min_price=min_price,
        max_price=max_price,
        package_type=package_type,
        is_featured=is_featured,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/packages/featured", response_model=List[PackageListItem])
async def get_featured_packages(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get featured packages for homepage.
    
    Public endpoint.
    """
    service = HolidayService(db)
    packages = await service.get_featured_packages(limit=limit)
    return packages


@router.post("/packages", response_model=PackageDetail, status_code=status.HTTP_201_CREATED)
async def create_package(
    data: PackageCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new holiday package.
    
    Requires admin authentication.
    """
    service = HolidayService(db)
    package = await service.create_package(
        created_by_id=int(current_user.id),
        **data.model_dump()
    )
    # Reload with all relationships
    package = await service.get_package(package.id, include_details=True)
    return package


@router.get("/packages/{package_id}", response_model=PackageDetail)
async def get_package_by_id(
    package_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get package details by ID.
    
    Public endpoint.
    """
    service = HolidayService(db)
    package = await service.get_package(package_id, include_details=True)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@router.get("/packages/slug/{slug}", response_model=PackageDetail)
async def get_package_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get package details by slug (SEO friendly).
    
    Public endpoint.
    """
    service = HolidayService(db)
    package = await service.get_package(slug=slug, include_details=True)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@router.put("/packages/{package_id}", response_model=PackageDetail)
async def update_package(
    package_id: int,
    data: PackageUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a package."""
    service = HolidayService(db)
    package = await service.update_package(package_id, **data.model_dump(exclude_unset=True))
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    # Reload with relationships
    package = await service.get_package(package_id, include_details=True)
    return package


@router.delete("/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a package (soft delete)."""
    service = HolidayService(db)
    deleted = await service.delete_package(package_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Package not found")
    return None


# =============================================================================
# Itinerary Endpoints (Admin only)
# =============================================================================

@router.post("/packages/{package_id}/itinerary", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def add_itinerary(
    package_id: int,
    data: ItineraryCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Add itinerary item to a package."""
    service = HolidayService(db)
    
    # Verify package exists
    package = await service.get_package(package_id, include_details=False)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    itinerary = await service.add_itinerary(package_id, **data.model_dump())
    return itinerary


@router.put("/itinerary/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: int,
    data: ItineraryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update itinerary item."""
    service = HolidayService(db)
    itinerary = await service.update_itinerary(itinerary_id, **data.model_dump(exclude_unset=True))
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary item not found")
    return itinerary


@router.delete("/itinerary/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    itinerary_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete itinerary item."""
    service = HolidayService(db)
    deleted = await service.delete_itinerary(itinerary_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Itinerary item not found")
    return None


# =============================================================================
# Inclusion Endpoints (Admin only)
# =============================================================================

@router.post("/packages/{package_id}/inclusions", response_model=InclusionResponse, status_code=status.HTTP_201_CREATED)
async def add_inclusion(
    package_id: int,
    data: InclusionCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Add inclusion/exclusion to a package."""
    service = HolidayService(db)
    
    package = await service.get_package(package_id, include_details=False)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    inclusion = await service.add_inclusion(package_id, **data.model_dump())
    return inclusion


@router.delete("/inclusions/{inclusion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inclusion(
    inclusion_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete inclusion."""
    service = HolidayService(db)
    deleted = await service.delete_inclusion(inclusion_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inclusion not found")
    return None


# =============================================================================
# Image Endpoints (Admin only)
# =============================================================================

@router.post("/packages/{package_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def add_image(
    package_id: int,
    data: ImageCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Add image to package gallery."""
    service = HolidayService(db)
    
    package = await service.get_package(package_id, include_details=False)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    image = await service.add_image(package_id, **data.model_dump())
    return image


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete image."""
    service = HolidayService(db)
    deleted = await service.delete_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    return None


# =============================================================================
# Enquiry Endpoints (Public + Admin)
# =============================================================================

@router.post("/enquiries", response_model=EnquiryResponse, status_code=status.HTTP_201_CREATED)
async def create_enquiry(
    data: EnquiryCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(lambda: None)  # Optional auth
):
    """
    Submit an enquiry for a package.
    
    Public endpoint - no authentication required.
    If user is authenticated, enquiry is linked to their account.
    """
    service = PackageEnquiryService(db)
    user_id = int(current_user.id) if current_user else None
    enquiry = await service.create_enquiry(
        user_id=user_id,
        **data.model_dump()
    )
    return enquiry


@router.get("/enquiries", response_model=EnquiryListResponse)
async def list_enquiries(
    status: Optional[EnquiryStatus] = None,
    package_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all enquiries.
    
    Requires admin authentication.
    """
    service = PackageEnquiryService(db)
    result = await service.list_enquiries(
        status=status,
        package_id=package_id,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/enquiries/{enquiry_id}", response_model=EnquiryResponse)
async def get_enquiry(
    enquiry_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get enquiry details."""
    service = PackageEnquiryService(db)
    enquiry = await service.get_enquiry(enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return enquiry


@router.put("/enquiries/{enquiry_id}", response_model=EnquiryResponse)
async def update_enquiry(
    enquiry_id: int,
    data: EnquiryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update enquiry (assign, change status, add notes)."""
    service = PackageEnquiryService(db)
    enquiry = await service.update_enquiry(
        enquiry_id,
        **data.model_dump(exclude_unset=True)
    )
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return enquiry


# =============================================================================
# Booking Endpoints (Admin)
# =============================================================================

@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a package booking.
    
    Typically created by admin after receiving payment or from an enquiry.
    """
    service = PackageEnquiryService(db)
    
    booking_data = data.model_dump()
    travelers = booking_data.pop('travelers', None)
    
    booking = await service.create_booking(
        booked_by_id=int(current_user.id),
        travelers=[t.model_dump() for t in travelers] if travelers else None,
        **booking_data
    )
    return booking


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status: Optional[PackageBookingStatus] = None,
    package_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all package bookings.
    
    Requires admin authentication.
    """
    service = PackageEnquiryService(db)
    result = await service.list_bookings(
        status=status,
        package_id=package_id,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get booking details."""
    service = PackageEnquiryService(db)
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
    """Update booking details or record payment."""
    service = PackageEnquiryService(db)
    booking = await service.update_booking(
        booking_id,
        **data.model_dump(exclude_unset=True)
    )
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
    service = PackageEnquiryService(db)
    booking = await service.cancel_booking(
        booking_id,
        reason=reason,
        refund_amount=refund_amount
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


# =============================================================================
# User Bookings (Authenticated users)
# =============================================================================

@router.get("/my/bookings", response_model=BookingListResponse)
async def get_my_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's package bookings.
    """
    service = PackageEnquiryService(db)
    result = await service.list_bookings(
        user_id=int(current_user.id),
        page=page,
        page_size=page_size
    )
    return result


@router.get("/my/enquiries", response_model=EnquiryListResponse)
async def get_my_enquiries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's package enquiries.
    """
    service = PackageEnquiryService(db)
    result = await service.list_enquiries(
        user_id=int(current_user.id),
        page=page,
        page_size=page_size
    )
    return result
