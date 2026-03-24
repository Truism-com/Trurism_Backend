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


from app.core.redis import get_tenant_cache, set_tenant_cache

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
        """
        # Skip tenant resolution for certain paths
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth",
            "/v1/admin/tenants",
            "/favicon.ico"
        ]
        
        if any(request.url.path.startswith(path) for path in skip_paths):
            request.state.tenant = None
            request.state.tenant_id = None
            return await call_next(request)
        
        tenant_id = None
        tenant_code = request.headers.get("X-Tenant-Code")
        tenant_id_header = request.headers.get("X-Tenant-ID")
        host = request.headers.get("Host", "").split(":")[0]
        
        if tenant_id_header:
            try:
                tenant_id = int(tenant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Tenant-ID header"
                )
        
        cache_key = f"id:{tenant_id}" if tenant_id else (f"code:{tenant_code}" if tenant_code else f"host:{host}")
        
        # Try to get from Redis cache first
        cached_tenant = await get_tenant_cache(cache_key)
        if cached_tenant:
            request.state.tenant_id = cached_tenant.get("id")
            request.state.tenant = cached_tenant
            logger.debug(f"Resolved tenant from Redis cache: {cached_tenant.get('code')}")
            
            response = await call_next(request)
            response.headers["X-Tenant-Resolver"] = "cache"
            if request.state.tenant_id:
                response.headers["X-Tenant-ID"] = str(request.state.tenant_id)
            return response

        # Resolve tenant from database
        tenant = None
        try:
            from app.core.database import async_session_maker
            
            async with async_session_maker() as db:
                if tenant_id:
                    result = await db.execute(
                        select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
                    )
                    tenant = result.scalar_one_or_none()
                elif tenant_code:
                    result = await db.execute(
                        select(Tenant).where(Tenant.code == tenant_code, Tenant.is_active == True)
                    )
                    tenant = result.scalar_one_or_none()
                elif host:
                    result = await db.execute(
                        select(Tenant).where(
                            (Tenant.domain == host) | (Tenant.subdomain == host.split(".")[0]),
                            Tenant.is_active == True
                        )
                    )
                    tenant = result.scalar_one_or_none()
                
                if tenant:
                    tenant_id = tenant.id
                    tenant_data = {
                        "id": tenant.id,
                        "code": tenant.code,
                        "name": tenant.name,
                        "domain": tenant.domain,
                        "subdomain": tenant.subdomain,
                        "is_active": tenant.is_active
                    }
                    # Cache in Redis for 10 minutes
                    await set_tenant_cache(cache_key, tenant_data, ttl=600)
                    logger.info(f"Resolved tenant from DB: {tenant.code} (ID: {tenant.id}) - Cached in Redis")
                    
                    # For downstream logic that might expect a model object, 
                    # we'll store the object in the request state only for the first time
                    request.state.tenant = tenant
                else:
                    logger.warning(f"No tenant resolved for query: {cache_key}")
                    request.state.tenant = None
        
        except Exception as e:
            logger.error(f"Error resolving tenant: {e}")
            request.state.tenant = None
        
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        response.headers["X-Tenant-Resolver"] = "db"
        
        if tenant_id:
            # We use t_data if it was from cache, but here we might not have it
            # Let's ensure we have accessibility to tenant code
            t_code = getattr(request.state.tenant, "code", None) if hasattr(request.state.tenant, "code") else (request.state.tenant.get("code") if isinstance(request.state.tenant, dict) else None)
            if t_code:
                response.headers["X-Tenant-Code"] = t_code
            response.headers["X-Tenant-ID"] = str(tenant_id)
        
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
