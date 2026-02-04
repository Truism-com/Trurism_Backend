"""
Customer Dashboard Module (B2C Portal)

User-facing features for managing bookings, profile, and support.
"""

from app.dashboard.models import (
    SocialAccount, AmendmentRequest, UserQuery, ActivityLog,
    AmendmentType, AmendmentStatus, QueryType, QueryStatus, ActivityType
)
from app.dashboard.services import DashboardService
from app.dashboard.api import router

__all__ = [
    # Models
    "SocialAccount",
    "AmendmentRequest",
    "UserQuery",
    "ActivityLog",
    # Enums
    "AmendmentType",
    "AmendmentStatus",
    "QueryType",
    "QueryStatus",
    "ActivityType",
    # Services
    "DashboardService",
    # Router
    "router"
]
