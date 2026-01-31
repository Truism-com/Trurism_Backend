"""
Tenant Middleware

This middleware identifies the tenant from the request and injects
tenant context for all subsequent operations.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.tenant.models import Tenant

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to identify and inject tenant context.
    
    This middleware reads the Host header or X-Tenant-ID header
    to identify the tenant and injects tenant information into
    the request state for use in endpoints.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and inject tenant context.
        
        Priority order for tenant identification:
        1. X-Tenant-ID header (explicit tenant ID)
        2. X-Tenant-Code header (explicit tenant code)
        3. Host header (domain-based routing)
        """
        # Skip tenant resolution for certain paths
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/v1/admin/tenants"  # Admin endpoints for tenant management
        ]
        
        if any(request.url.path.startswith(path) for path in skip_paths):
            request.state.tenant = None
            request.state.tenant_id = None
            return await call_next(request)
        
        tenant = None
        tenant_id = None
        
        # Method 1: Check X-Tenant-ID header
        tenant_id_header = request.headers.get("X-Tenant-ID")
        if tenant_id_header:
            try:
                tenant_id = int(tenant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Tenant-ID header"
                )
        
        # Method 2: Check X-Tenant-Code header
        tenant_code = request.headers.get("X-Tenant-Code")
        
        # Method 3: Extract from Host header
        host = request.headers.get("Host", "").split(":")[0]  # Remove port if present
        
        # Resolve tenant from database
        try:
            from app.core.database import async_session_maker
            
            async with async_session_maker() as db:
                if tenant_id:
                    # Query by ID
                    result = await db.execute(
                        select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
                    )
                    tenant = result.scalar_one_or_none()
                elif tenant_code:
                    # Query by code
                    result = await db.execute(
                        select(Tenant).where(Tenant.code == tenant_code, Tenant.is_active == True)
                    )
                    tenant = result.scalar_one_or_none()
                elif host:
                    # Query by domain or subdomain
                    result = await db.execute(
                        select(Tenant).where(
                            (Tenant.domain == host) | (Tenant.subdomain == host.split(".")[0]),
                            Tenant.is_active == True
                        )
                    )
                    tenant = result.scalar_one_or_none()
                
                if tenant:
                    tenant_id = tenant.id
                    logger.info(f"Resolved tenant: {tenant.code} (ID: {tenant.id})")
                else:
                    # For development: allow requests without tenant
                    # In production, you might want to raise an error here
                    logger.warning(f"No tenant resolved for host: {host}")
        
        except Exception as e:
            logger.error(f"Error resolving tenant: {e}")
            # Continue without tenant in development
            # In production, consider raising an error
        
        # Inject tenant context into request state
        request.state.tenant = tenant
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        
        # Add tenant information to response headers (optional)
        if tenant:
            response.headers["X-Tenant-Code"] = tenant.code
            response.headers["X-Tenant-ID"] = str(tenant.id)
        
        return response


def get_current_tenant(request: Request) -> Tenant:
    """
    Get current tenant from request state.
    
    This is a dependency that can be used in endpoints to access
    the current tenant.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tenant: Current tenant object
        
    Raises:
        HTTPException: If no tenant is resolved
    """
    tenant = getattr(request.state, "tenant", None)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant not identified. Please provide X-Tenant-ID or X-Tenant-Code header."
        )
    
    return tenant


def get_optional_tenant(request: Request) -> Tenant | None:
    """
    Get current tenant from request state (optional).
    
    Returns None if no tenant is resolved instead of raising an error.
    """
    return getattr(request.state, "tenant", None)
