"""
Tenant Pydantic Schemas

Request/Response schemas for tenant configuration endpoints.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime


class TenantBase(BaseModel):
    """Base tenant schema with common fields."""
    code: str = Field(..., min_length=2, max_length=50, description="Unique tenant code")
    name: str = Field(..., min_length=2, max_length=255, description="Tenant name")
    domain: str = Field(..., description="Primary domain")
    subdomain: Optional[str] = Field(None, description="Subdomain (if using multi-subdomain)")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    company_name: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None


class TenantBrandingUpdate(BaseModel):
    """Schema for updating tenant branding."""
    logo_url: Optional[str] = Field(None, description="Logo URL")
    favicon_url: Optional[str] = Field(None, description="Favicon URL")
    brand_name: Optional[str] = Field(None, description="Brand name")
    theme_colors: Optional[Dict[str, str]] = Field(None, description="Theme colors")
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    support_whatsapp: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    enabled_modules: Optional[Dict[str, bool]] = None


class TenantConfigUpdate(BaseModel):
    """Schema for updating tenant configuration."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    default_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    default_language: Optional[str] = None
    timezone: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None


class TenantPublicConfig(BaseModel):
    """Public configuration returned to frontend."""
    tenant_id: int
    code: str
    brand_name: str
    logo_url: Optional[str]
    favicon_url: Optional[str]
    theme_colors: Dict[str, str]
    support: Dict[str, Optional[str]]
    social_links: Dict[str, str]
    enabled_modules: Dict[str, bool]
    currency: str
    language: str
    
    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    """Complete tenant information (admin view)."""
    id: int
    code: str
    name: str
    domain: str
    subdomain: Optional[str]
    is_active: bool
    is_verified: bool
    logo_url: Optional[str]
    favicon_url: Optional[str]
    brand_name: Optional[str]
    theme_colors: Dict[str, str]
    support_email: Optional[str]
    support_phone: Optional[str]
    support_whatsapp: Optional[str]
    social_links: Dict[str, str]
    enabled_modules: Dict[str, bool]
    default_currency: str
    default_language: str
    timezone: str
    company_name: Optional[str]
    gst_number: Optional[str]
    pan_number: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Paginated list of tenants."""
    tenants: list[TenantResponse]
    total: int
    page: int
    size: int
