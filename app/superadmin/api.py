"""
Superadmin API Endpoints

Cross-tenant platform administration. Only accessible to SUPERADMIN role.
Provides global (non-tenant-scoped) views of:
- Platform-wide stats
- All tenants list
- Cross-tenant user lookup
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_database_session
from app.auth.api import get_current_superadmin_user
from app.auth.models import User, UserRole, AgentApprovalStatus
from app.booking.models import FlightBooking, HotelBooking, BusBooking, BookingStatus, PaymentStatus
from app.admin.services import AdminAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/superadmin", tags=["Superadmin"])


@router.get("/stats")
async def get_platform_stats(
    current_superadmin: User = Depends(get_current_superadmin_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    Platform-wide dashboard stats (all tenants combined).

    tenant_id=None lifts tenant scoping in AdminAnalyticsService
    so the superadmin sees aggregate metrics across all white-label portals.
    """
    try:
        analytics_service = AdminAnalyticsService(db, tenant_id=None)
        stats = await analytics_service.get_dashboard_stats()
        return {"scope": "platform_wide", **stats}
    except Exception as e:
        logger.error("Superadmin stats failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve platform stats: {str(e)}"
        )


@router.get("/tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_superadmin: User = Depends(get_current_superadmin_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    List all tenants (distinct tenant_ids) registered on the platform.

    Returns one row per tenant_id with: user_count, admin_email, created_at of first user.
    Uses a single GROUP BY query — no N+1.
    """
    try:
        skip = (page - 1) * size

        # Count distinct tenants
        count_result = await db.execute(
            select(func.count(func.distinct(User.tenant_id))).where(User.tenant_id.isnot(None))
        )
        total = count_result.scalar() or 0

        # Fetch tenant summaries
        result = await db.execute(
            select(
                User.tenant_id,
                func.count(User.id).label("user_count"),
                func.min(User.created_at).label("registered_at"),
            )
            .where(User.tenant_id.isnot(None))
            .group_by(User.tenant_id)
            .order_by(func.min(User.created_at).desc())
            .limit(size)
            .offset(skip)
        )
        rows = result.all()

        tenants = [
            {
                "tenant_id": row.tenant_id,
                "user_count": row.user_count,
                "registered_at": row.registered_at.isoformat() if row.registered_at else None,
            }
            for row in rows
        ]

        total_pages = max(1, (total + size - 1) // size)
        return {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "items": tenants,
        }

    except Exception as e:
        logger.error("Superadmin tenants list failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tenants: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: int,
    current_superadmin: User = Depends(get_current_superadmin_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Stats scoped to a specific tenant. Superadmin can drill into any tenant."""
    try:
        analytics_service = AdminAnalyticsService(db, tenant_id=tenant_id)
        stats = await analytics_service.get_dashboard_stats()
        return {"scope": "tenant", "tenant_id": tenant_id, **stats}
    except Exception as e:
        logger.error("Tenant stats failed for tenant %d: %s", tenant_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tenant stats: {str(e)}"
        )


@router.get("/users/search")
async def search_users_cross_tenant(
    email: Optional[str] = Query(None, description="Partial email match"),
    tenant_id: Optional[int] = Query(None, description="Filter by tenant"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_superadmin: User = Depends(get_current_superadmin_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Cross-tenant user search. No tenant scoping applied unless tenant_id is specified."""
    try:
        skip = (page - 1) * size
        conditions = []

        if email:
            conditions.append(User.email.ilike(f"%{email}%"))
        if tenant_id is not None:
            conditions.append(User.tenant_id == tenant_id)
        if role:
            conditions.append(User.role == role)

        count_q = select(func.count(User.id))
        if conditions:
            count_q = count_q.where(*conditions)
        total = (await db.execute(count_q)).scalar() or 0

        data_q = select(User).order_by(User.created_at.desc()).limit(size).offset(skip)
        if conditions:
            data_q = data_q.where(*conditions)
        users = (await db.execute(data_q)).scalars().all()

        items = [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "tenant_id": u.tenant_id,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]

        total_pages = max(1, (total + size - 1) // size)
        return {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "items": items,
        }

    except Exception as e:
        logger.error("Cross-tenant user search failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User search failed: {str(e)}"
        )
