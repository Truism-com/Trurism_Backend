"""
Tenant API Endpoints

REST API endpoints for tenant and white-label configuration management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_database_session
from app.auth.api import get_current_admin_user
from app.auth.models import User
from app.tenant.models import Tenant
from app.tenant.schemas import (
    TenantCreate, TenantResponse, TenantListResponse,
    TenantBrandingUpdate, TenantConfigUpdate, TenantPublicConfig
)
from app.tenant.services import TenantService
from app.tenant.middleware import get_current_tenant, get_optional_tenant

# Router for tenant endpoints
router = APIRouter(prefix="/v1", tags=["Tenant & White Label"])


@router.get("/config/public", response_model=TenantPublicConfig)
async def get_public_config(
    request: Request,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get public tenant configuration for frontend.
    
    **CRITICAL ENDPOINT**: The frontend calls this first to get branding,
    enabled modules, and customization based on the domain/tenant.
    
    The tenant is identified by:
    1. X-Tenant-ID header
    2. X-Tenant-Code header
    3. Host header (domain)
    
    Returns:
        TenantPublicConfig: Public configuration including logo, colors, modules
    """
    tenant = get_optional_tenant(request)
    
    if not tenant:
        # Return default configuration if no tenant identified
        return TenantPublicConfig(
            tenant_id=0,
            code="default",
            brand_name="Travel Platform",
            logo_url=None,
            favicon_url=None,
            theme_colors={
                "primary": "#1E40AF",
                "secondary": "#F59E0B",
                "accent": "#10B981"
            },
            support={
                "email": None,
                "phone": None,
                "whatsapp": None
            },
            social_links={},
            enabled_modules={
                "flights": True,
                "hotels": True,
                "buses": True,
                "holidays": True,
                "visas": True,
                "activities": True,
                "transfers": True
            },
            currency="INR",
            language="en"
        )
    
    return TenantPublicConfig(**tenant.get_public_config())


# Admin endpoints for tenant management

@router.post("/admin/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new tenant.
    
    **Admin Only**: Creates a new white-label tenant with default settings.
    
    Args:
        tenant_data: Tenant creation data
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        TenantResponse: Created tenant information
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.create_tenant(tenant_data)
    return TenantResponse.model_validate(tenant)


@router.get("/admin/tenants", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(False, description="Filter only active tenants"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    List all tenants with pagination.
    
    **Admin Only**: Returns paginated list of all tenants.
    
    Args:
        page: Page number
        size: Items per page
        active_only: Filter only active tenants
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        TenantListResponse: Paginated list of tenants
    """
    skip = (page - 1) * size
    
    tenant_service = TenantService(db)
    tenants, total = await tenant_service.get_all_tenants(
        skip=skip,
        limit=size,
        active_only=active_only
    )
    
    return TenantListResponse(
        tenants=[TenantResponse.model_validate(t) for t in tenants],
        total=total,
        page=page,
        size=size
    )


@router.get("/admin/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get tenant by ID.
    
    **Admin Only**: Returns detailed tenant information.
    
    Args:
        tenant_id: Tenant ID
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        TenantResponse: Tenant information
    """
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return TenantResponse.model_validate(tenant)


@router.put("/admin/config/branding", response_model=TenantResponse)
async def update_branding(
    branding_data: TenantBrandingUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update tenant branding configuration.
    
    **Admin Only**: Upload logo, set colors, toggle modules.
    
    This endpoint allows admins to customize:
    - Logo and favicon URLs
    - Theme colors (primary, secondary, accent)
    - Support contact information
    - Social media links
    - Module enablement (enable/disable specific modules)
    
    Args:
        branding_data: Branding update data
        request: Request object (to get current tenant)
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        TenantResponse: Updated tenant information
    """
    tenant = get_current_tenant(request)
    
    tenant_service = TenantService(db)
    updated_tenant = await tenant_service.update_branding(
        tenant.id,
        branding_data
    )
    
    return TenantResponse.model_validate(updated_tenant)


@router.put("/admin/tenants/{tenant_id}/config", response_model=TenantResponse)
async def update_tenant_config(
    tenant_id: int,
    config_data: TenantConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update tenant configuration.
    
    **Admin Only**: Update general tenant settings.
    
    Args:
        tenant_id: Tenant ID
        config_data: Configuration update data
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        TenantResponse: Updated tenant information
    """
    tenant_service = TenantService(db)
    updated_tenant = await tenant_service.update_config(tenant_id, config_data)
    return TenantResponse.model_validate(updated_tenant)


@router.delete("/admin/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete (deactivate) tenant.
    
    **Admin Only**: Soft delete tenant by setting is_active=False.
    
    Args:
        tenant_id: Tenant ID
        current_admin: Current authenticated admin user
        db: Database session
    """
    tenant_service = TenantService(db)
    await tenant_service.delete_tenant(tenant_id)
