"""
Search API Endpoints

This module defines FastAPI endpoints for search operations:
- Flight search with filtering and sorting
- Hotel search with location and amenity filters
- Bus search for inter-city travel
- Search result caching and optimization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_database_session
from app.search.schemas import (
    FlightSearchRequest, HotelSearchRequest, BusSearchRequest,
    SearchResponse, SearchCacheRequest
)
from app.search.services import FlightSearchService, HotelSearchService, BusSearchService

# Router for search endpoints
router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/flights", response_model=SearchResponse)
async def search_flights(
    origin: str = Query(..., min_length=3, max_length=3, description="Origin airport IATA code"),
    destination: str = Query(..., min_length=3, max_length=3, description="Destination airport IATA code"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD)"),
    adults: int = Query(..., ge=1, le=9, description="Number of adult passengers"),
    children: int = Query(0, ge=0, le=9, description="Number of child passengers"),
    infants: int = Query(0, ge=0, le=9, description="Number of infant passengers"),
    travel_class: str = Query("economy", description="Travel class (economy, business, first)"),
    max_results: int = Query(50, ge=1, le=100, description="Maximum search results"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for available flights.
    
    This endpoint searches for flights based on origin, destination, dates,
    passenger count, and travel preferences. Results are cached for performance.
    
    Args:
        origin: Origin airport IATA code (e.g., "DEL")
        destination: Destination airport IATA code (e.g., "BOM")
        depart_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date for round trip
        adults: Number of adult passengers (1-9)
        children: Number of child passengers (0-9)
        infants: Number of infant passengers (0-9)
        travel_class: Travel class preference
        max_results: Maximum number of results to return
        db: Database session
        
    Returns:
        SearchResponse: Flight search results with metadata
        
    Raises:
        HTTPException: If search parameters are invalid
    """
    try:
        from datetime import datetime
        
        # Parse dates
        depart_date_obj = datetime.strptime(depart_date, "%Y-%m-%d").date()
        return_date_obj = None
        if return_date:
            return_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()
        
        # Create search request
        search_request = FlightSearchRequest(
            origin=origin.upper(),
            destination=destination.upper(),
            depart_date=depart_date_obj,
            return_date=return_date_obj,
            adults=adults,
            children=children,
            infants=infants,
            travel_class=travel_class,
            max_results=max_results
        )
        
        # Perform search
        flight_service = FlightSearchService(db)
        results = await flight_service.search_flights(search_request)
        
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/flights", response_model=SearchResponse)
async def search_flights_post(
    search_request: FlightSearchRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for flights using POST method with request body.
    
    This endpoint provides an alternative to GET method for complex search
    parameters that might be too long for URL parameters.
    
    Args:
        search_request: Flight search parameters in request body
        db: Database session
        
    Returns:
        SearchResponse: Flight search results with metadata
    """
    try:
        flight_service = FlightSearchService(db)
        results = await flight_service.search_flights(search_request)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/hotels", response_model=SearchResponse)
async def search_hotels(
    location: str = Query(..., min_length=2, description="Hotel location or city"),
    checkin: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    checkout: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    rooms: int = Query(..., ge=1, le=9, description="Number of rooms"),
    adults: int = Query(..., ge=1, le=18, description="Number of adult guests"),
    children: int = Query(0, ge=0, le=18, description="Number of child guests"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price per night"),
    rating: Optional[float] = Query(None, ge=1, le=5, description="Minimum hotel rating"),
    amenities: Optional[str] = Query(None, description="Comma-separated amenities"),
    max_results: int = Query(50, ge=1, le=100, description="Maximum search results"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for available hotels.
    
    This endpoint searches for hotels based on location, dates, room requirements,
    and preferences. Supports filtering by price range, rating, and amenities.
    
    Args:
        location: Hotel location or city name
        checkin: Check-in date in YYYY-MM-DD format
        checkout: Check-out date in YYYY-MM-DD format
        rooms: Number of rooms required
        adults: Number of adult guests
        children: Number of child guests
        min_price: Minimum price per night filter
        max_price: Maximum price per night filter
        rating: Minimum hotel rating filter
        amenities: Comma-separated list of required amenities
        max_results: Maximum number of results to return
        db: Database session
        
    Returns:
        SearchResponse: Hotel search results with metadata
    """
    try:
        from datetime import datetime
        
        # Parse dates
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
        
        # Parse amenities
        amenities_list = []
        if amenities:
            amenities_list = [amenity.strip() for amenity in amenities.split(",")]
        
        # Create search request
        search_request = HotelSearchRequest(
            location=location,
            checkin=checkin_date,
            checkout=checkout_date,
            rooms=rooms,
            adults=adults,
            children=children,
            min_price=min_price,
            max_price=max_price,
            rating=rating,
            amenities=amenities_list,
            max_results=max_results
        )
        
        # Perform search
        hotel_service = HotelSearchService(db)
        results = await hotel_service.search_hotels(search_request)
        
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/hotels", response_model=SearchResponse)
async def search_hotels_post(
    search_request: HotelSearchRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for hotels using POST method with request body.
    
    This endpoint provides an alternative to GET method for complex search
    parameters and better handling of amenity lists.
    
    Args:
        search_request: Hotel search parameters in request body
        db: Database session
        
    Returns:
        SearchResponse: Hotel search results with metadata
    """
    try:
        hotel_service = HotelSearchService(db)
        results = await hotel_service.search_hotels(search_request)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/buses", response_model=SearchResponse)
async def search_buses(
    origin: str = Query(..., min_length=2, description="Origin city or location"),
    destination: str = Query(..., min_length=2, description="Destination city or location"),
    travel_date: str = Query(..., description="Travel date (YYYY-MM-DD)"),
    passengers: int = Query(..., ge=1, le=9, description="Number of passengers"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD)"),
    max_results: int = Query(50, ge=1, le=100, description="Maximum search results"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for available buses.
    
    This endpoint searches for inter-city bus options based on origin,
    destination, travel date, and passenger count.
    
    Args:
        origin: Origin city or location
        destination: Destination city or location
        travel_date: Travel date in YYYY-MM-DD format
        passengers: Number of passengers
        return_date: Optional return date for round trip
        max_results: Maximum number of results to return
        db: Database session
        
    Returns:
        SearchResponse: Bus search results with metadata
    """
    try:
        from datetime import datetime
        
        # Parse dates
        travel_date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()
        return_date_obj = None
        if return_date:
            return_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()
        
        # Create search request
        search_request = BusSearchRequest(
            origin=origin,
            destination=destination,
            travel_date=travel_date_obj,
            passengers=passengers,
            return_date=return_date_obj,
            max_results=max_results
        )
        
        # Perform search
        bus_service = BusSearchService(db)
        results = await bus_service.search_buses(search_request)
        
        return results
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/buses", response_model=SearchResponse)
async def search_buses_post(
    search_request: BusSearchRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for buses using POST method with request body.
    
    This endpoint provides an alternative to GET method for complex search
    parameters and better handling of search criteria.
    
    Args:
        search_request: Bus search parameters in request body
        db: Database session
        
    Returns:
        SearchResponse: Bus search results with metadata
    """
    try:
        bus_service = BusSearchService(db)
        results = await bus_service.search_buses(search_request)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.delete("/cache")
async def clear_search_cache(
    cache_request: SearchCacheRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Clear search result cache.
    
    This endpoint allows clearing cached search results for cache management
    and testing purposes.
    
    Args:
        cache_request: Cache management request
        db: Database session
        
    Returns:
        Dict: Cache clearing confirmation
    """
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        
        if settings.redis_url and settings.redis_url.lower() != "none":
            redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        else:
            return {
                "message": "Redis is not configured",
                "search_type": cache_request.search_type,
                "reason": cache_request.reason
            }
        
        try:
            # Clear specific cache key or all search cache
            if cache_request.cache_key:
                await redis_client.delete(cache_request.cache_key)
                message = f"Cache key {cache_request.cache_key} cleared"
            else:
                # Clear all search cache for the specified type
                pattern = f"search:{cache_request.search_type}:*"
                keys = []
                async for key in redis_client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await redis_client.delete(*keys)
                    message = f"Cleared {len(keys)} cache entries for {cache_request.search_type}"
                else:
                    message = f"No cache entries found for {cache_request.search_type}"
        finally:
            await redis_client.aclose()
        
        return {
            "message": message,
            "search_type": cache_request.search_type,
            "reason": cache_request.reason
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache clearing failed: {str(e)}"
        )
