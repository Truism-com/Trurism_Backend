"""
Tax rate resolution with per-tenant override support.

Reads tax rates from SystemSetting (tenant-scoped) with config.py defaults as fallback.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

_SETTING_KEYS = {
    "flight_gst_domestic": "flight_gst_domestic",
    "flight_gst_international": "flight_gst_international",
    "hotel_gst": "hotel_gst",
    "bus_gst": "bus_gst",
}

_DEFAULTS = {
    "flight_gst_domestic": settings.flight_gst_domestic,
    "flight_gst_international": settings.flight_gst_international,
    "hotel_gst": settings.hotel_gst_default,
    "bus_gst": settings.bus_gst,
}


async def get_tax_rate(
    db: AsyncSession,
    tax_key: str,
    tenant_id: Optional[int] = None,
) -> float:
    """
    Resolve a tax rate from SystemSetting, falling back to config.py default.

    Args:
        db: Database session
        tax_key: One of 'flight_gst_domestic', 'flight_gst_international', 'hotel_gst', 'bus_gst'
        tenant_id: Optional tenant ID for tenant-scoped override

    Returns:
        Tax rate as a decimal (e.g. 0.05 for 5%)
    """
    default = _DEFAULTS.get(tax_key, 0.0)
    setting_key = _SETTING_KEYS.get(tax_key)
    if not setting_key:
        return default

    try:
        from app.settings.services import SettingsService
        svc = SettingsService(db)
        value = await svc.get_setting_value(setting_key, default=None, tenant_id=tenant_id)
        if value is not None:
            return float(value)
    except Exception:
        logger.debug("Failed to read tenant tax setting for %s, using default", tax_key)

    return default
