"""
Holiday Package Services

Business logic for holiday package operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import secrets
import re
import logging

from app.holidays.models import (
    HolidayPackage, PackageTheme, PackageDestination,
    PackageItinerary, PackageInclusion, PackageImage,
    PackageEnquiry, PackageBooking, PackageType,
    EnquiryStatus, PackageBookingStatus
)

logger = logging.getLogger(__name__)


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:200]


def generate_code(prefix: str = "PKG") -> str:
    """Generate unique package code."""
    return f"{prefix}{secrets.token_hex(4).upper()}"


def generate_ref(prefix: str = "ENQ") -> str:
    """Generate unique reference number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()
    return f"{prefix}{timestamp}{random_part}"


class HolidayService:
    """
    Service for holiday package management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # Theme Management
    # =========================================================================
    
    async def create_theme(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        image_url: Optional[str] = None,
        display_order: int = 0
    ) -> PackageTheme:
        """Create a new package theme."""
        theme = PackageTheme(
            name=name,
            slug=slug or generate_slug(name),
            description=description,
            icon=icon,
            image_url=image_url,
            display_order=display_order
        )
        self.db.add(theme)
        await self.db.commit()
        await self.db.refresh(theme)
        return theme
    
    async def get_themes(
        self,
        active_only: bool = True,
        with_package_count: bool = False
    ) -> List[PackageTheme]:
        """Get all themes."""
        query = select(PackageTheme)
        
        if active_only:
            query = query.where(PackageTheme.is_active == True)
        
        query = query.order_by(PackageTheme.display_order, PackageTheme.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_theme(self, theme_id: int) -> Optional[PackageTheme]:
        """Get theme by ID."""
        result = await self.db.execute(
            select(PackageTheme).where(PackageTheme.id == theme_id)
        )
        return result.scalar_one_or_none()
    
    async def update_theme(
        self,
        theme_id: int,
        **updates
    ) -> Optional[PackageTheme]:
        """Update a theme."""
        theme = await self.get_theme(theme_id)
        if not theme:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(theme, key):
                setattr(theme, key, value)
        
        await self.db.commit()
        await self.db.refresh(theme)
        return theme
    
    async def delete_theme(self, theme_id: int) -> bool:
        """Delete a theme (soft delete by deactivating)."""
        theme = await self.get_theme(theme_id)
        if not theme:
            return False
        theme.is_active = False
        await self.db.commit()
        return True
    
    # =========================================================================
    # Destination Management
    # =========================================================================
    
    async def create_destination(
        self,
        name: str,
        slug: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: str = "India",
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        is_international: bool = False
    ) -> PackageDestination:
        """Create a new destination."""
        destination = PackageDestination(
            name=name,
            slug=slug or generate_slug(name),
            city=city,
            state=state,
            country=country,
            description=description,
            image_url=image_url,
            is_international=is_international
        )
        self.db.add(destination)
        await self.db.commit()
        await self.db.refresh(destination)
        return destination
    
    async def get_destinations(
        self,
        active_only: bool = True,
        international_only: Optional[bool] = None
    ) -> List[PackageDestination]:
        """Get all destinations."""
        query = select(PackageDestination)
        
        if active_only:
            query = query.where(PackageDestination.is_active == True)
        
        if international_only is not None:
            query = query.where(PackageDestination.is_international == international_only)
        
        query = query.order_by(PackageDestination.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_destination(self, destination_id: int) -> Optional[PackageDestination]:
        """Get destination by ID."""
        result = await self.db.execute(
            select(PackageDestination).where(PackageDestination.id == destination_id)
        )
        return result.scalar_one_or_none()
    
    async def update_destination(
        self,
        destination_id: int,
        **updates
    ) -> Optional[PackageDestination]:
        """Update a destination."""
        destination = await self.get_destination(destination_id)
        if not destination:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(destination, key):
                setattr(destination, key, value)
        
        await self.db.commit()
        await self.db.refresh(destination)
        return destination
    
    # =========================================================================
    # Package Management
    # =========================================================================
    
    async def create_package(
        self,
        name: str,
        destination_id: int,
        created_by_id: Optional[int] = None,
        **kwargs
    ) -> HolidayPackage:
        """Create a new holiday package."""
        # Extract nested data
        itinerary_data = kwargs.pop('itinerary', None)
        inclusions_data = kwargs.pop('inclusions', None)
        images_data = kwargs.pop('images', None)
        
        # Generate slug and code if not provided
        slug = kwargs.pop('slug', None) or generate_slug(name)
        code = kwargs.pop('code', None) or generate_code()
        
        package = HolidayPackage(
            name=name,
            slug=slug,
            code=code,
            destination_id=destination_id,
            created_by_id=created_by_id,
            **kwargs
        )
        self.db.add(package)
        await self.db.flush()  # Get ID before adding related items
        
        # Add itinerary
        if itinerary_data:
            for item in itinerary_data:
                itinerary = PackageItinerary(
                    package_id=package.id,
                    **item
                )
                self.db.add(itinerary)
        
        # Add inclusions
        if inclusions_data:
            for item in inclusions_data:
                inclusion = PackageInclusion(
                    package_id=package.id,
                    **item
                )
                self.db.add(inclusion)
        
        # Add images
        if images_data:
            for item in images_data:
                image = PackageImage(
                    package_id=package.id,
                    **item
                )
                self.db.add(image)
        
        await self.db.commit()
        await self.db.refresh(package)
        return package
    
    async def get_package(
        self,
        package_id: Optional[int] = None,
        slug: Optional[str] = None,
        code: Optional[str] = None,
        include_details: bool = True
    ) -> Optional[HolidayPackage]:
        """Get package by ID, slug, or code."""
        query = select(HolidayPackage)
        
        if package_id:
            query = query.where(HolidayPackage.id == package_id)
        elif slug:
            query = query.where(HolidayPackage.slug == slug)
        elif code:
            query = query.where(HolidayPackage.code == code)
        else:
            return None
        
        if include_details:
            query = query.options(
                selectinload(HolidayPackage.theme),
                selectinload(HolidayPackage.destination),
                selectinload(HolidayPackage.origin),
                selectinload(HolidayPackage.itinerary),
                selectinload(HolidayPackage.inclusions),
                selectinload(HolidayPackage.images)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_packages(
        self,
        query: Optional[str] = None,
        theme_id: Optional[int] = None,
        destination_id: Optional[int] = None,
        origin_id: Optional[int] = None,
        min_nights: Optional[int] = None,
        max_nights: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        package_type: Optional[PackageType] = None,
        is_featured: Optional[bool] = None,
        active_only: bool = True,
        sort_by: str = "display_order",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search and filter packages."""
        stmt = select(HolidayPackage).options(
            selectinload(HolidayPackage.theme),
            selectinload(HolidayPackage.destination)
        )
        
        # Apply filters
        conditions = []
        
        if active_only:
            conditions.append(HolidayPackage.is_active == True)
        
        if query:
            search_term = f"%{query}%"
            conditions.append(
                or_(
                    HolidayPackage.name.ilike(search_term),
                    HolidayPackage.description.ilike(search_term),
                    HolidayPackage.code.ilike(search_term)
                )
            )
        
        if theme_id:
            conditions.append(HolidayPackage.theme_id == theme_id)
        
        if destination_id:
            conditions.append(HolidayPackage.destination_id == destination_id)
        
        if origin_id:
            conditions.append(HolidayPackage.origin_id == origin_id)
        
        if min_nights:
            conditions.append(HolidayPackage.nights >= min_nights)
        
        if max_nights:
            conditions.append(HolidayPackage.nights <= max_nights)
        
        if min_price:
            conditions.append(
                func.coalesce(HolidayPackage.discounted_price, HolidayPackage.base_price) >= min_price
            )
        
        if max_price:
            conditions.append(
                func.coalesce(HolidayPackage.discounted_price, HolidayPackage.base_price) <= max_price
            )
        
        if package_type:
            conditions.append(HolidayPackage.package_type == package_type)
        
        if is_featured is not None:
            conditions.append(HolidayPackage.is_featured == is_featured)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Apply sorting
        if sort_by == "price_asc":
            stmt = stmt.order_by(
                func.coalesce(HolidayPackage.discounted_price, HolidayPackage.base_price).asc()
            )
        elif sort_by == "price_desc":
            stmt = stmt.order_by(
                func.coalesce(HolidayPackage.discounted_price, HolidayPackage.base_price).desc()
            )
        elif sort_by == "rating":
            stmt = stmt.order_by(HolidayPackage.star_rating.desc())
        elif sort_by == "newest":
            stmt = stmt.order_by(HolidayPackage.created_at.desc())
        else:
            stmt = stmt.order_by(HolidayPackage.display_order, HolidayPackage.name)
        
        # Count total
        count_stmt = select(func.count(HolidayPackage.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        packages = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "packages": packages,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def get_featured_packages(self, limit: int = 10) -> List[HolidayPackage]:
        """Get featured packages for homepage."""
        stmt = select(HolidayPackage).options(
            selectinload(HolidayPackage.destination)
        ).where(
            and_(
                HolidayPackage.is_active == True,
                HolidayPackage.is_featured == True
            )
        ).order_by(
            HolidayPackage.display_order
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_package(
        self,
        package_id: int,
        **updates
    ) -> Optional[HolidayPackage]:
        """Update a package."""
        package = await self.get_package(package_id, include_details=False)
        if not package:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(package, key):
                setattr(package, key, value)
        
        await self.db.commit()
        await self.db.refresh(package)
        return package
    
    async def delete_package(self, package_id: int) -> bool:
        """Soft delete a package."""
        package = await self.get_package(package_id, include_details=False)
        if not package:
            return False
        package.is_active = False
        await self.db.commit()
        return True
    
    # =========================================================================
    # Itinerary Management
    # =========================================================================
    
    async def add_itinerary(
        self,
        package_id: int,
        day_number: int,
        title: str,
        **kwargs
    ) -> PackageItinerary:
        """Add itinerary item to package."""
        itinerary = PackageItinerary(
            package_id=package_id,
            day_number=day_number,
            title=title,
            **kwargs
        )
        self.db.add(itinerary)
        await self.db.commit()
        await self.db.refresh(itinerary)
        return itinerary
    
    async def update_itinerary(
        self,
        itinerary_id: int,
        **updates
    ) -> Optional[PackageItinerary]:
        """Update itinerary item."""
        result = await self.db.execute(
            select(PackageItinerary).where(PackageItinerary.id == itinerary_id)
        )
        itinerary = result.scalar_one_or_none()
        if not itinerary:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(itinerary, key):
                setattr(itinerary, key, value)
        
        await self.db.commit()
        await self.db.refresh(itinerary)
        return itinerary
    
    async def delete_itinerary(self, itinerary_id: int) -> bool:
        """Delete itinerary item."""
        result = await self.db.execute(
            select(PackageItinerary).where(PackageItinerary.id == itinerary_id)
        )
        itinerary = result.scalar_one_or_none()
        if not itinerary:
            return False
        await self.db.delete(itinerary)
        await self.db.commit()
        return True
    
    # =========================================================================
    # Inclusion Management
    # =========================================================================
    
    async def add_inclusion(
        self,
        package_id: int,
        item: str,
        is_included: bool = True,
        **kwargs
    ) -> PackageInclusion:
        """Add inclusion/exclusion to package."""
        inclusion = PackageInclusion(
            package_id=package_id,
            item=item,
            is_included=is_included,
            **kwargs
        )
        self.db.add(inclusion)
        await self.db.commit()
        await self.db.refresh(inclusion)
        return inclusion
    
    async def delete_inclusion(self, inclusion_id: int) -> bool:
        """Delete inclusion."""
        result = await self.db.execute(
            select(PackageInclusion).where(PackageInclusion.id == inclusion_id)
        )
        inclusion = result.scalar_one_or_none()
        if not inclusion:
            return False
        await self.db.delete(inclusion)
        await self.db.commit()
        return True
    
    # =========================================================================
    # Image Management
    # =========================================================================
    
    async def add_image(
        self,
        package_id: int,
        image_url: str,
        **kwargs
    ) -> PackageImage:
        """Add image to package gallery."""
        image = PackageImage(
            package_id=package_id,
            image_url=image_url,
            **kwargs
        )
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image
    
    async def delete_image(self, image_id: int) -> bool:
        """Delete image."""
        result = await self.db.execute(
            select(PackageImage).where(PackageImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            return False
        await self.db.delete(image)
        await self.db.commit()
        return True


class PackageEnquiryService:
    """
    Service for package enquiries and bookings.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # Enquiry Management
    # =========================================================================
    
    async def create_enquiry(
        self,
        name: str,
        email: str,
        phone: str,
        package_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> PackageEnquiry:
        """Create a new package enquiry."""
        enquiry = PackageEnquiry(
            enquiry_ref=generate_ref("ENQ"),
            name=name,
            email=email,
            phone=phone,
            package_id=package_id,
            user_id=user_id,
            **kwargs
        )
        self.db.add(enquiry)
        await self.db.commit()
        await self.db.refresh(enquiry)
        
        logger.info(f"Created enquiry {enquiry.enquiry_ref}")
        return enquiry
    
    async def get_enquiry(
        self,
        enquiry_id: Optional[int] = None,
        enquiry_ref: Optional[str] = None
    ) -> Optional[PackageEnquiry]:
        """Get enquiry by ID or reference."""
        query = select(PackageEnquiry).options(
            selectinload(PackageEnquiry.package)
        )
        
        if enquiry_id:
            query = query.where(PackageEnquiry.id == enquiry_id)
        elif enquiry_ref:
            query = query.where(PackageEnquiry.enquiry_ref == enquiry_ref)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_enquiries(
        self,
        status: Optional[EnquiryStatus] = None,
        package_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List enquiries with filters."""
        stmt = select(PackageEnquiry).options(
            selectinload(PackageEnquiry.package)
        )
        
        conditions = []
        
        if status:
            conditions.append(PackageEnquiry.status == status)
        
        if package_id:
            conditions.append(PackageEnquiry.package_id == package_id)
        
        if assigned_to_id:
            conditions.append(PackageEnquiry.assigned_to_id == assigned_to_id)
        
        if user_id:
            conditions.append(PackageEnquiry.user_id == user_id)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(PackageEnquiry.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Order and paginate
        stmt = stmt.order_by(PackageEnquiry.created_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        enquiries = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "enquiries": enquiries,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def update_enquiry(
        self,
        enquiry_id: int,
        **updates
    ) -> Optional[PackageEnquiry]:
        """Update enquiry (admin use)."""
        enquiry = await self.get_enquiry(enquiry_id)
        if not enquiry:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(enquiry, key):
                setattr(enquiry, key, value)
        
        if updates.get('status') in [EnquiryStatus.CONTACTED, EnquiryStatus.QUOTE_SENT]:
            enquiry.last_contact_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(enquiry)
        return enquiry
    
    # =========================================================================
    # Booking Management
    # =========================================================================
    
    async def create_booking(
        self,
        package_id: int,
        lead_traveler_name: str,
        lead_traveler_email: str,
        lead_traveler_phone: str,
        travel_date: date,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        user_id: Optional[int] = None,
        enquiry_id: Optional[int] = None,
        booked_by_id: Optional[int] = None,
        travelers: Optional[list] = None,
        **kwargs
    ) -> PackageBooking:
        """Create a package booking."""
        # Get package for pricing
        package_result = await self.db.execute(
            select(HolidayPackage).where(HolidayPackage.id == package_id)
        )
        package = package_result.scalar_one_or_none()
        
        if not package:
            raise ValueError(f"Package {package_id} not found")
        
        # Calculate pricing
        effective_price = package.discounted_price or package.base_price
        child_price = package.child_price or (effective_price * 0.5)
        infant_price = package.infant_price or 0
        
        base_amount = (adults * effective_price) + (children * child_price) + (infants * infant_price)
        taxes = base_amount * 0.05  # 5% GST
        total_amount = base_amount + taxes
        
        import json
        travelers_data = json.dumps(travelers) if travelers else None
        
        booking = PackageBooking(
            booking_ref=generate_ref("BKG"),
            package_id=package_id,
            user_id=user_id,
            enquiry_id=enquiry_id,
            lead_traveler_name=lead_traveler_name,
            lead_traveler_email=lead_traveler_email,
            lead_traveler_phone=lead_traveler_phone,
            travelers_data=travelers_data,
            travel_date=travel_date,
            adults=adults,
            children=children,
            infants=infants,
            base_amount=base_amount,
            taxes=taxes,
            total_amount=total_amount,
            booked_by_id=booked_by_id,
            **kwargs
        )
        
        self.db.add(booking)
        
        # Update enquiry status if from enquiry
        if enquiry_id:
            enquiry_result = await self.db.execute(
                select(PackageEnquiry).where(PackageEnquiry.id == enquiry_id)
            )
            enquiry = enquiry_result.scalar_one_or_none()
            if enquiry:
                enquiry.status = EnquiryStatus.CONVERTED
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Created booking {booking.booking_ref}")
        return booking
    
    async def get_booking(
        self,
        booking_id: Optional[int] = None,
        booking_ref: Optional[str] = None
    ) -> Optional[PackageBooking]:
        """Get booking by ID or reference."""
        query = select(PackageBooking).options(
            selectinload(PackageBooking.package)
        )
        
        if booking_id:
            query = query.where(PackageBooking.id == booking_id)
        elif booking_ref:
            query = query.where(PackageBooking.booking_ref == booking_ref)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_bookings(
        self,
        status: Optional[PackageBookingStatus] = None,
        package_id: Optional[int] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List bookings with filters."""
        stmt = select(PackageBooking).options(
            selectinload(PackageBooking.package)
        )
        
        conditions = []
        
        if status:
            conditions.append(PackageBooking.status == status)
        
        if package_id:
            conditions.append(PackageBooking.package_id == package_id)
        
        if user_id:
            conditions.append(PackageBooking.user_id == user_id)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(PackageBooking.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Order and paginate
        stmt = stmt.order_by(PackageBooking.created_at.desc())
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
    ) -> Optional[PackageBooking]:
        """Update booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(booking, key):
                setattr(booking, key, value)
        
        # Auto-update status based on payment
        if booking.amount_paid >= booking.total_amount:
            booking.status = PackageBookingStatus.FULLY_PAID
        elif booking.amount_paid > 0:
            booking.status = PackageBookingStatus.PARTIALLY_PAID
        
        await self.db.commit()
        await self.db.refresh(booking)
        return booking
    
    async def cancel_booking(
        self,
        booking_id: int,
        reason: str,
        refund_amount: Optional[float] = None
    ) -> Optional[PackageBooking]:
        """Cancel a booking."""
        booking = await self.get_booking(booking_id)
        if not booking:
            return None
        
        booking.status = PackageBookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        booking.refund_amount = refund_amount
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        logger.info(f"Cancelled booking {booking.booking_ref}")
        return booking
