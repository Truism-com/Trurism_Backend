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

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time

from app.core.config import settings
from app.core.database import init_database, check_database_health
from app.core.supabase import get_supabase
from app.auth.api import router as auth_router
from app.search.api import router as search_router
from app.booking.api import router as booking_router
from app.admin.api import router as admin_router
from app.api_keys.api import router as api_keys_router
import os
import redis.asyncio as redis_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
                logger.error("Database health check failed")
                raise Exception("Database connection failed")
            logger.info("Database health check passed")
        else:
            logger.info("Skipping database health check due to SKIP_DB_INIT env var")
        # Check Redis (if configured) - Non-blocking, optional service
        try:
            if settings.redis_url and settings.redis_url.lower() != "none" and not settings.redis_url.startswith("redis://localhost"):
                # use a short-lived client to ping Redis
                client = redis_async.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
                pong = await client.ping()
                if pong:
                    logger.info("Redis ping successful")
                await client.close()
            else:
                logger.info("Redis not configured or using localhost - skipping health check")
        except Exception as re:
            logger.warning(f"Redis health check failed (non-critical): {re}")
        
        # TODO: Initialize Redis connection
        # TODO: Initialize external API clients
        # TODO: Start background tasks (Celery workers)
        
        logger.info("Travel Booking Platform API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Travel Booking Platform API...")
    # TODO: Close database connections
    # Close redis connections if any (module-level clients will handle their own cleanup)
    # TODO: Stop background tasks
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
    
    * 🔐 Secure JWT-based authentication with role-based access control
    * ✈️ Flight search and booking with multiple airlines
    * 🏨 Hotel search and booking with filtering and amenities
    * 🚌 Bus search and booking for inter-city travel
    * 💳 Payment processing with multiple payment methods
    * 📊 Admin dashboard with analytics and reporting
    * 🔄 Real-time booking status updates
    * 📱 RESTful API with comprehensive documentation
    
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
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
# Use configured CORS origins, or allow all in debug mode
cors_origins = settings.cors_origins if not settings.debug or settings.cors_origins != ["*"] else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
# Only add if trusted_hosts is configured and not "*" in production
if not settings.debug and settings.trusted_hosts and settings.trusted_hosts != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add processing time to response headers.
    
    This middleware measures request processing time and adds it
    to the response headers for monitoring and debugging.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log HTTP requests.
    
    This middleware logs all incoming requests with method, path,
    and response status for monitoring and debugging.
    """
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
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
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": request.url.path
        }
    )


# Simple Supabase test endpoint
@app.get("/test", tags=["Health"])
async def test_supabase():
    """
    Test Supabase connectivity by selecting from `users` table.
    """
    try:
        sb = get_supabase()
        result = await sb.from_("users").select("*").limit(5).execute()
        data = getattr(result, "data", None)
        if data is None:
            return {"count": 0, "data": []}
        return {"count": len(data), "data": data}
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        raise HTTPException(status_code=500, detail={"detail": "Internal server error", "path": "/test"})


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
    redis_url = os.getenv("REDIS_URL")
    if redis_url and redis_url.lower() != "none" and not skip_checks:
        try:
            await check_redis_health()  # if implemented elsewhere
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


# Include module routers
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(booking_router)
app.include_router(admin_router)
app.include_router(api_keys_router)

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
    "Health": "Health check endpoints for monitoring",
    "Root": "API root information"
}

existing_tags = set()
for router in [auth_router, search_router, booking_router, admin_router, api_keys_router]:
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
