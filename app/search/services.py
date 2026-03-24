"""
Search Services

This module contains business logic for search operations:
- Flight search with external API integration
- Hotel search with filtering and caching
- Bus search functionality
- Search result caching and optimization
- Mock data generation for development
"""

import asyncio
import json
import redis.asyncio as redis
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import random
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.search.schemas import (
    FlightSearchRequest, HotelSearchRequest, BusSearchRequest,
    FlightResult, HotelResult, BusResult, SearchResponse
)
from app.core.config import settings

# Redis client for search result caching (async)
if settings.redis_url and settings.redis_url.lower() != "none":
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
else:
    redis_client = None


from app.markup.services import MarkupService
from app.markup.models import ServiceType

class BaseSearchService:
    """
    Base search service for common search functionality.
    
    This service provides shared functionality for all search types
    including caching, result formatting, and common utilities.
    """
    
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        self.db = db
        self.redis = redis_client
        self.tenant_id = tenant_id
        self.markup_service = MarkupService(db)
    
    def _generate_search_id(self) -> str:
        """Generate unique search identifier."""
        return str(uuid.uuid4())
    
    def _get_cache_key(self, search_type: str, search_params: Dict[str, Any]) -> str:
        """Generate cache key for search parameters."""
        # Include tenant_id in cache key for brand-specific results/pricing
        search_params["tenant_id"] = self.tenant_id
        params_str = json.dumps(search_params, sort_keys=True, default=str)
        return f"search:{search_type}:{hash(params_str)}"
    
    async def _get_cached_results(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results."""
        if not self.redis:
            return None
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None
    
    async def _cache_results(self, cache_key: str, results: Dict[str, Any], ttl: int):
        """Cache search results with TTL."""
        if not self.redis or not results:
            return
        try:
            results["cached_at"] = datetime.utcnow().isoformat()
            await self.redis.setex(cache_key, ttl, json.dumps(results))
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    async def _apply_markup(self, service_type: ServiceType, base_price: float, search_params: Dict[str, Any]) -> float:
        """
        Apply tenant-specific markup to base price.
        """
        try:
            breakdown = await self.markup_service.calculate_price_with_markup(
                service_type=service_type,
                base_price=base_price,
                search_params=search_params,
                tenant_id=self.tenant_id
            )
            return breakdown.total_price
        except Exception as e:
            logger.error(f"Error applying markup: {e}")
            return base_price * 1.15  # Fallback 15% markup + taxes if rule fails
    
    def _calculate_search_time(self, start_time: datetime) -> float:
        """Calculate search execution time."""
        return (datetime.utcnow() - start_time).total_seconds()


class FlightSearchService(BaseSearchService):
    """
    Flight search service for finding available flights.
    """
    
    async def search_flights(self, search_request: FlightSearchRequest) -> SearchResponse:
        """
        Search for available flights.
        """
        start_time = datetime.utcnow()
        search_id = self._generate_search_id()
        
        # Generate cache key
        cache_key = self._get_cache_key("flight", search_request.dict())
        
        # Try to get cached results
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            return SearchResponse(
                search_id=search_id,
                total_results=cached_results["total_results"],
                results=cached_results["results"],
                search_time=self._calculate_search_time(start_time),
                cached=True,
                expires_at=datetime.fromisoformat(cached_results["cached_at"]) + timedelta(seconds=settings.search_cache_ttl)
            )
        
        # Perform search
        # In a real scenario, this would call _search_flights_xml_agency
        # For now, we use the mock generator but remove the artificial delay
        flight_results = await self._search_flights_mock(search_request)
        
        # Apply markups per result
        for result in flight_results:
            result.price = await self._apply_markup(
                ServiceType.FLIGHT, 
                result.price, 
                {"airline": result.airline, "origin": result.origin, "destination": result.destination}
            )
        
        # Prepare response
        response_data = {
            "total_results": len(flight_results),
            "results": [result.dict() for result in flight_results]
        }
        
        # Cache results
        await self._cache_results(cache_key, response_data, settings.search_cache_ttl)
        
        return SearchResponse(
            search_id=search_id,
            total_results=len(flight_results),
            results=[result.dict() for result in flight_results],
            search_time=self._calculate_search_time(start_time),
            cached=False
        )
    
    async def _search_flights_mock(self, search_request: FlightSearchRequest) -> List[FlightResult]:
        """
        Generate mock flight results without artificial delay.
        """
        airlines = ["AirFast", "SkyWings", "JetExpress", "FlyHigh", "AirConnect"]
        aircraft_types = ["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]
        
        results = []
        num_results = random.randint(5, 15)
        
        for i in range(num_results):
            airline = random.choice(airlines)
            departure_time = datetime.combine(
                search_request.depart_date,
                datetime.min.time().replace(
                    hour=random.randint(6, 22),
                    minute=random.choice([0, 15, 30, 45])
                )
            )
            
            flight_duration = random.randint(1, 8)
            arrival_time = departure_time + timedelta(hours=flight_duration)
            
            base_price = random.randint(3000, 15000)
            if search_request.travel_class == "business":
                base_price *= 2.5
            elif search_request.travel_class == "first":
                base_price *= 4
            
            total_price = base_price * (search_request.adults + search_request.children * 0.75)
            
            flight_result = FlightResult(
                offer_id=f"FL{random.randint(10000, 99999)}",
                airline=airline,
                flight_number=f"{airline[:2]}{random.randint(100, 999)}",
                origin=search_request.origin,
                destination=search_request.destination,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=f"{flight_duration}h {random.randint(0, 59)}m",
                stops=random.randint(0, 2),
                aircraft=random.choice(aircraft_types),
                price=round(total_price, 2),
                travel_class=search_request.travel_class,
                baggage_allowance=f"{random.randint(15, 25)}kg",
                refundable=random.choice([True, False])
            )
            results.append(flight_result)
        
        results.sort(key=lambda x: x.price)
        return results[:search_request.max_results]
    
    async def _search_flights_xml_agency(self, search_request: FlightSearchRequest) -> List[FlightResult]:
        """Search flights using XML.Agency API (stub)."""
        # TODO: Implement actual XML.Agency integration
        return await self._search_flights_mock(search_request)


class HotelSearchService(BaseSearchService):
    """
    Hotel search service for finding available accommodations.
    """
    
    async def search_hotels(self, search_request: HotelSearchRequest) -> SearchResponse:
        """
        Search for available hotels.
        """
        start_time = datetime.utcnow()
        search_id = self._generate_search_id()
        
        cache_key = self._get_cache_key("hotel", search_request.dict())
        
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            return SearchResponse(
                search_id=search_id,
                total_results=cached_results["total_results"],
                results=cached_results["results"],
                search_time=self._calculate_search_time(start_time),
                cached=True,
                expires_at=datetime.fromisoformat(cached_results["cached_at"]) + timedelta(seconds=settings.search_cache_ttl)
            )
        
        hotel_results = await self._search_hotels_mock(search_request)
        filtered_results = self._apply_hotel_filters(hotel_results, search_request)
        
        # Apply markups
        for result in filtered_results:
            result.price_per_night = await self._apply_markup(
                ServiceType.HOTEL, 
                result.price_per_night, 
                {"hotel_name": result.name, "city": result.city, "rating": result.rating}
            )
        
        response_data = {
            "total_results": len(filtered_results),
            "results": [result.dict() for result in filtered_results]
        }
        
        await self._cache_results(cache_key, response_data, settings.search_cache_ttl)
        
        return SearchResponse(
            search_id=search_id,
            total_results=len(filtered_results),
            results=[result.dict() for result in filtered_results],
            search_time=self._calculate_search_time(start_time),
            cached=False
        )
    
    async def _search_hotels_mock(self, search_request: HotelSearchRequest) -> List[HotelResult]:
        """Generate mock hotel results without delay."""
        hotel_names = ["Grand Plaza", "City Inn", "Royal Hotel", "Garden View", "Comfort Suites"]
        amenities_pool = ["WiFi", "Pool", "Gym", "Restaurant", "Spa", "Parking"]
        room_types = ["Standard", "Deluxe", "Suite"]
        
        results = []
        num_results = random.randint(8, 25)
        
        for i in range(num_results):
            hotel_result = HotelResult(
                hotel_id=f"HTL{random.randint(10000, 99999)}",
                name=f"{random.choice(hotel_names)} {search_request.location}",
                address=f"{random.randint(1, 999)} Main St",
                city=search_request.location,
                rating=round(random.uniform(3.0, 5.0), 1),
                price_per_night=random.randint(1500, 8000),
                amenities=random.sample(amenities_pool, random.randint(2, 5)),
                room_types=random.sample(room_types, random.randint(1, 3)),
                distance_from_center=round(random.uniform(0.5, 10.0), 1),
                cancellation_policy="Free cancellation",
                images=[],
                description="Comfortable stay"
            )
            results.append(hotel_result)
        
        results.sort(key=lambda x: x.price_per_night)
        return results

    def _apply_hotel_filters(self, results: List[HotelResult], search_request: HotelSearchRequest) -> List[HotelResult]:
        """Apply filters to hotel search results."""
        filtered = results
        if search_request.min_price:
            filtered = [r for r in filtered if r.price_per_night >= search_request.min_price]
        if search_request.max_price:
            filtered = [r for r in filtered if r.price_per_night <= search_request.max_price]
        if search_request.rating:
            filtered = [r for r in filtered if r.rating >= search_request.rating]
        return filtered[:search_request.max_results]


class BusSearchService(BaseSearchService):
    """
    Bus search service for finding inter-city bus options.
    """
    
    async def search_buses(self, search_request: BusSearchRequest) -> SearchResponse:
        """
        Search for available buses.
        """
        start_time = datetime.utcnow()
        search_id = self._generate_search_id()
        
        cache_key = self._get_cache_key("bus", search_request.dict())
        
        cached_results = await self._get_cached_results(cache_key)
        if cached_results:
            return SearchResponse(
                search_id=search_id,
                total_results=cached_results["total_results"],
                results=cached_results["results"],
                search_time=self._calculate_search_time(start_time),
                cached=True,
                expires_at=datetime.fromisoformat(cached_results["cached_at"]) + timedelta(seconds=settings.search_cache_ttl)
            )
        
        bus_results = await self._search_buses_mock(search_request)
        
        # Apply markups
        for result in bus_results:
            result.price = await self._apply_markup(
                ServiceType.BUS, 
                result.price, 
                {"operator": result.operator, "type": result.bus_type}
            )
        
        response_data = {
            "total_results": len(bus_results),
            "results": [result.dict() for result in bus_results]
        }
        
        await self._cache_results(cache_key, response_data, settings.search_cache_ttl)
        
        return SearchResponse(
            search_id=search_id,
            total_results=len(bus_results),
            results=[result.dict() for result in bus_results],
            search_time=self._calculate_search_time(start_time),
            cached=False
        )
    
    async def _search_buses_mock(self, search_request: BusSearchRequest) -> List[BusResult]:
        """Generate mock bus results without delay."""
        operators = ["GoBus", "RedBus", "Metro Lines"]
        bus_types = ["AC Sleeper", "AC Seater", "Non-AC Seater"]
        
        results = []
        num_results = random.randint(5, 12)
        
        for i in range(num_results):
            bus_type = random.choice(bus_types)
            departure_time = datetime.combine(search_request.travel_date, datetime.min.time().replace(hour=random.randint(18, 23)))
            duration = random.randint(4, 12)
            
            base_price = random.randint(800, 3000)
            if "AC" in bus_type: base_price *= 1.5
            
            bus_result = BusResult(
                bus_id=f"BUS{random.randint(10000, 99999)}",
                operator=random.choice(operators),
                bus_type=bus_type,
                origin=search_request.origin,
                destination=search_request.destination,
                departure_time=departure_time,
                arrival_time=departure_time + timedelta(hours=duration),
                duration=f"{duration}h 0m",
                seats_available=random.randint(5, 45),
                price=round(base_price, 2),
                amenities=["WiFi"],
                boarding_points=["Main Stand"],
                dropping_points=["Central Station"]
            )
            results.append(bus_result)
        
        results.sort(key=lambda x: x.price)
        return results[:search_request.max_results]
