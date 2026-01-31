"""
Holiday/Tour Packages Module

This module handles holiday package management including:
- Package themes and categories
- Day-wise itineraries
- Inclusions/Exclusions
- Package enquiries and bookings
- Featured tours and promotions
"""

from app.holidays.models import (
    HolidayPackage, PackageTheme, PackageDestination,
    PackageItinerary, PackageInclusion, PackageImage,
    PackageEnquiry, PackageBooking, PackageType,
    EnquiryStatus, PackageBookingStatus
)
from app.holidays.services import HolidayService, PackageEnquiryService
from app.holidays.api import router, admin_router

__all__ = [
    # Models
    "HolidayPackage",
    "PackageTheme",
    "PackageDestination",
    "PackageItinerary",
    "PackageInclusion",
    "PackageImage",
    "PackageEnquiry",
    "PackageBooking",
    # Enums
    "PackageType",
    "EnquiryStatus",
    "PackageBookingStatus",
    # Services
    "HolidayService",
    "PackageEnquiryService",
    # Routers
    "router",
    "admin_router"
]
