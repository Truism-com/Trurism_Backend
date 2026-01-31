"""
Tenant Services

Business logic for tenant management operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from fastapi import HTTPException, status
from typing import Optional, Tuple, List

from app.tenant.models import Tenant
from app.tenant.schemas import TenantCreate, TenantBrandingUpdate, TenantConfigUpdate


class TenantService:
    """Service for tenant management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            tenant_data: Tenant creation data
            
        Returns:
            Tenant: Created tenant object
            
        Raises:
            HTTPException: If tenant code or domain already exists
        """
        # Check if code exists
        existing_code = await self.db.execute(
            select(Tenant).where(Tenant.code == tenant_data.code)
        )
        if existing_code.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with code '{tenant_data.code}' already exists"
            )
        
        # Check if domain exists
        existing_domain = await self.db.execute(
            select(Tenant).where(Tenant.domain == tenant_data.domain)
        )
        if existing_domain.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with domain '{tenant_data.domain}' already exists"
            )
        
        # Create tenant with default settings
        tenant = Tenant(
            **tenant_data.model_dump(),
            theme_colors={
                "primary": "#1E40AF",
                "secondary": "#F59E0B",
                "accent": "#10B981"
            },
            enabled_modules={
                "flights": True,
                "hotels": True,
                "buses": True,
                "holidays": True,
                "visas": True,
                "activities": True,
                "transfers": True
            }
        )
        
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def get_tenant_by_id(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tenant_by_code(self, code: str) -> Optional[Tenant]:
        """Get tenant by code."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def get_all_tenants(
        self,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = False
    ) -> Tuple[List[Tenant], int]:
        """
        Get all tenants with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Filter only active tenants
            
        Returns:
            Tuple[List[Tenant], int]: List of tenants and total count
        """
        query = select(Tenant)
        
        if active_only:
            query = query.where(Tenant.is_active == True)
        
        # Get total count
        count_query = select(func.count(Tenant.id))
        if active_only:
            count_query = count_query.where(Tenant.is_active == True)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(Tenant.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        tenants = result.scalars().all()
        
        return list(tenants), total
    
    async def update_branding(
        self,
        tenant_id: int,
        branding_data: TenantBrandingUpdate
    ) -> Tenant:
        """
        Update tenant branding configuration.
        
        Args:
            tenant_id: Tenant ID
            branding_data: Branding update data
            
        Returns:
            Tenant: Updated tenant object
            
        Raises:
            HTTPException: If tenant not found
        """
        tenant = await self.get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Update fields
        update_data = branding_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def update_config(
        self,
        tenant_id: int,
        config_data: TenantConfigUpdate
    ) -> Tenant:
        """
        Update tenant configuration.
        
        Args:
            tenant_id: Tenant ID
            config_data: Configuration update data
            
        Returns:
            Tenant: Updated tenant object
            
        Raises:
            HTTPException: If tenant not found
        """
        tenant = await self.get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Update fields
        update_data = config_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        return tenant
    
    async def delete_tenant(self, tenant_id: int) -> bool:
        """
        Soft delete tenant (deactivate).
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deleted
            
        Raises:
            HTTPException: If tenant not found
        """
        tenant = await self.get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        tenant.is_active = False
        await self.db.commit()
        
        return True
