"""
Main FastAPI Application

This is the main entry point for the Travel Booking Platform API.
It initializes the FastAPI application, includes all module routers,
and sets up middleware, exception handlers, and startup/shutdown events.

The application follows a modular architecture with separate modules for:
- Authentication (auth)
- Search functionality (search)  
- Booking management (booking)
- Administrative operations (admin)
"""

import os
os.environ.setdefault("RATELIMIT_STORAGE_URL", "memory://")

from fastapi import FastAPI, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
import time

from app.core.config import settings
from app.core.database import init_database, check_database_health
from app.core.redis import check_redis_health
from app.auth.api import router as auth_router
from app.search.api import router as search_router
from app.booking.api import router as booking_router
from app.admin.api import router as admin_router
from app.api_keys.api import router as api_keys_router
from app.tenant.api import router as tenant_router
from app.markup.api import router as markup_router
from app.payments.api import router as payments_router
from app.wallet.api import router as wallet_router, admin_router as wallet_admin_router
from app.holidays.api import router as holidays_router
from app.visa.api import router as visa_router
from app.activities.api import router as activities_router
from app.transfers.api import router as transfers_router
from app.cms.api import router as cms_router
from app.settings.api import router as settings_router
from app.dashboard.api import router as dashboard_router, admin_router as dashboard_admin_router
from app.pricing.api import router as pricing_router, admin_router as pricing_admin_router
from app.company.api import router as company_router
from app.files.api import router as files_router
from app.tenant.middleware import TenantMiddleware
from app.newsletter.api import router as newsletter_router
from app.feedback.api import router as feedback_router
from app.settings.api import router as settings_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize rate limiter with in-memory storage
_storage_uri = settings.redis_url if settings.redis_url and settings.redis_url.lower() != "none" else "memory://"
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_period}seconds"],
    storage_uri=_storage_uri,
    headers_enabled=True
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    This context manager handles:
    - Database initialization on startup
    - Health checks and system validation
    - Cleanup operations on shutdown
    """
    # Startup
    logger.info("Starting Travel Booking Platform API...")
    
    try:
        if os.getenv("SKIP_DB_INIT", "false").lower() not in ("1", "true", "yes"):
            await init_database()
            logger.info("Database initialized successfully")
        else:
            logger.info("Skipping database init due to SKIP_DB_INIT env var")
        
        # Check database health
        if os.getenv("SKIP_DB_INIT", "false").lower() not in ("1", "true", "yes"):
            db_healthy = await check_database_health()
            if not db_healthy:
                logger.error("Database health check failed - endpoints requiring DB will not work")
            else:
                logger.info("Database health check passed")
        else:
            logger.info("Skipping database health check due to SKIP_DB_INIT env var")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error("HINT: If this is on Azure, check if 'Allow Azure Services' is enabled in your Database Networking settings.")
        logger.error("API will start but database-dependent endpoints will not work")
    
    # Check Redis (if configured) - Non-blocking, optional service
    try:
        if settings.redis_url and settings.redis_url.lower() != "none" and not settings.redis_url.startswith("redis://localhost"):
            redis_ok = await check_redis_health(settings.redis_url)
            if redis_ok:
                logger.info("Redis ping successful")
            else:
                logger.warning("Redis health check returned False (non-critical)")
        else:
            logger.info("Redis not configured or using localhost - skipping health check")
    except Exception as re:
        logger.warning(f"Redis health check failed (non-critical): {re}")
    
    logger.info("Travel Booking Platform API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Travel Booking Platform API...")
    # Close database connections
    try:
        from app.core.database import engine
        await engine.dispose()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.error(f"Error disposing database engine: {e}")
    logger.info("Travel Booking Platform API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    **Travel Booking Platform API**
    
    A comprehensive travel booking system with modular architecture supporting:
    
    * **Authentication**: User registration, login, and JWT-based authentication
    * **Search**: Flight, hotel, and bus search with caching and filtering
    * **Booking**: Reservation management with payment processing
    * **Admin**: Administrative operations and system management
    
    ## Features
    
    * Secure JWT-based authentication with role-based access control
    * Flight search and booking with multiple airlines
    * Hotel search and booking with filtering and amenities
    * Bus search and booking for inter-city travel
    * Payment processing with multiple payment methods
    * Admin dashboard with analytics and reporting
    * Real-time booking status updates
    * RESTful API with comprehensive documentation
    
    ## Authentication
    
    Most endpoints require authentication. Use the `/auth/login` endpoint to get
    JWT tokens, then include them in the Authorization header:
    
    ```
    Authorization: Bearer <your_access_token>
    ```
    
    ## Rate Limiting
    
    API endpoints are rate-limited to prevent abuse. Default limits:
    - 60 requests per minute per user
    - 1000 requests per hour per IP address
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
# Parse CORS origins from comma-separated string
if settings.cors_origins.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

# Restrict HTTP methods and headers for better security
cors_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
cors_headers = ["Authorization", "Content-Type", "X-Tenant-ID", "X-Tenant-Code"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,  # Never allow credentials with wildcard
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

# Add tenant middleware for white-label support
app.add_middleware(TenantMiddleware)

# Add trusted host middleware for production
# Only add if trusted_hosts is configured and not "*" in production
if not settings.debug and settings.trusted_hosts.strip() and settings.trusted_hosts.strip() != "*":
    trusted_hosts_list = [h.strip() for h in settings.trusted_hosts.split(",") if h.strip()]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts_list
    )

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    """Middleware to enforce request body size limit."""
    content_length = request.headers.get("content-length")
    if content_length:
        if int(content_length) > settings.max_request_body_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"}
            )
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Middleware to add security headers to responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), usb=()"

    # Add Cache-Control for authenticated endpoints to prevent sensitive data caching
    if request.headers.get("Authorization"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and attach X-Process-Time header in one pass."""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with detailed error messages.
    
    This handler provides detailed validation error information
    for better API usability and debugging.
    """
    # Strip internal Pydantic URL field from error details
    errors = []
    for err in exc.errors():
        clean_err = {k: v for k, v in err.items() if k != "url"}
        errors.append(clean_err)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions with appropriate error responses.
    
    This handler catches unhandled exceptions and returns
    appropriate error responses while logging the details.
    """
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    
    # In production, hide internal error details
    if settings.environment == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "path": request.url.path
            }
        )
    
    # In production, we should probably be more careful,
    # but for debugging this 500, we need the error message.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "path": request.url.path,
            "error_type": type(exc).__name__
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 always; status may be 'degraded' if checks fail or are skipped.
    """
    issues: list[str] = []
    degraded = False
    skip_checks = os.getenv("SKIP_DB_INIT", "").lower() == "true"

    # Database health
    if not skip_checks:
        try:
            db_healthy = await check_database_health()
            if not db_healthy:
                degraded = True
                issues.append("database_connection_failed")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            degraded = True
            issues.append("database_health_error")
    else:
        degraded = True
        issues.append("database_check_skipped")

    # Redis health (optional)
    if settings.redis_url and settings.redis_url.lower() != "none" and not skip_checks:
        try:
            redis_ok = await check_redis_health(settings.redis_url)
            if not redis_ok:
                degraded = True
                issues.append("redis_connection_failed")
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            degraded = True
            issues.append("redis_connection_failed")

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy" if not degraded else "degraded",
            "timestamp": time.time(),
            "version": settings.app_version,
            "environment": settings.environment,
            "issues": issues,
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    This endpoint provides basic information about the API
    including version, documentation links, and status.
    """
    return {
        "message": "Welcome to Travel Booking Platform API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else None,
        "redoc_url": "/redoc" if settings.debug else None,
        "health_url": "/health"
    }


@app.post("/admin/init-db", tags=["Admin"], include_in_schema=True)
async def manual_init_db(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Manually trigger database initialization.
    Requires admin authentication.
    """
    # Verify admin token
    from app.core.security import SecurityManager
    payload = await SecurityManager.verify_token(credentials.credentials, "access")
    role = payload.get("role", "")
    if role != "admin":
        return JSONResponse(
            status_code=403,
            content={"detail": "Admin access required"}
        )
    
    try:
        from app.core.database import init_database
        await init_database()
        return {"message": "Database initialization triggered successfully"}
    except Exception as e:
        logger.error(f"Manual DB init failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e) if settings.debug else "Initialization failed", "type": type(e).__name__ if settings.debug else "Error"}
        )


# Include module routers
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(booking_router)
app.include_router(admin_router)
app.include_router(api_keys_router)
app.include_router(tenant_router)
app.include_router(markup_router)
app.include_router(payments_router)
app.include_router(wallet_router)
app.include_router(wallet_admin_router)
app.include_router(holidays_router)
app.include_router(visa_router)
app.include_router(activities_router)
app.include_router(transfers_router)
app.include_router(cms_router)
app.include_router(settings_router)
app.include_router(dashboard_router)
app.include_router(dashboard_admin_router)
app.include_router(pricing_router)
app.include_router(pricing_admin_router)
app.include_router(company_router)
app.include_router(files_router)
app.include_router(newsletter_router)
app.include_router(feedback_router)
app.include_router(settings_router)

# Initialize openapi_tags if not exists
if app.openapi_tags is None:
    app.openapi_tags = []

# Add router information to OpenAPI with proper tag format
tag_descriptions = {
    "Authentication": "User registration, login, and JWT-based authentication",
    "Search": "Search for flights, hotels, and buses",
    "Bookings": "Manage flight, hotel, and bus bookings",
    "Admin": "Administrative operations and system management",
    "API Keys": "API key management for third-party integrations",
    "Holidays": "Holiday packages, themes, destinations, enquiries and bookings",
    "Visa": "Visa services, applications and document management",
    "Activities": "Tours and activities, slots and bookings",
    "Transfers": "Airport transfers and cab services",
    "CMS": "Content management - sliders, offers, blog, static pages",
    "Settings": "System settings, convenience fees and staff management",
    "Dashboard": "B2C customer dashboard - bookings, amendments, queries, activity logs",
    "Pricing": "Pricing engine - markup rules, discounts, convenience fees",
    "Company": "Company settings - branding, bank accounts, registration, ACL",
    "Health": "Health check endpoints for monitoring",
    "Root": "API root information"
}

existing_tags = set()
for router in [auth_router, search_router, booking_router, admin_router, api_keys_router,
               holidays_router, visa_router, activities_router, transfers_router, 
               cms_router, settings_router, dashboard_router, pricing_router, company_router]:
    if hasattr(router, 'tags') and router.tags:
        for tag in router.tags:
            if isinstance(tag, str) and tag not in existing_tags:
                app.openapi_tags.append({
                    "name": tag,
                    "description": tag_descriptions.get(tag, f"{tag} endpoints")
                })
                existing_tags.add(tag)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
