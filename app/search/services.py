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
redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


class SearchService:
    """
    Base search service for common search functionality.
    
    This service provides shared functionality for all search types
    including caching, result formatting, and common utilities.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = redis_client
    
    def _generate_search_id(self) -> str:
        """Generate unique search identifier."""
        return str(uuid.uuid4())
    
    def _get_cache_key(self, search_type: str, search_params: Dict[str, Any]) -> str:
        """Generate cache key for search parameters."""
        # Create a deterministic key from search parameters
        params_str = json.dumps(search_params, sort_keys=True, default=str)
        return f"search:{search_type}:{hash(params_str)}"
    
    async def _get_cached_results(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results."""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache read error: {e}")
        return None
    
    async def _cache_results(self, cache_key: str, results: Dict[str, Any], ttl: int):
        """Cache search results with TTL."""
        try:
            results["cached_at"] = datetime.utcnow().isoformat()
            # use setex for TTL
            await self.redis.setex(cache_key, ttl, json.dumps(results))
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def _calculate_search_time(self, start_time: datetime) -> float:
        """Calculate search execution time."""
        return (datetime.utcnow() - start_time).total_seconds()


class FlightSearchService(SearchService):
    """
    Flight search service for finding available flights.
    
    This service handles flight search operations including external API
    integration with XML.Agency and mock data generation for development.
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.api_client = None  # Will be initialized with XML.Agency client
    
    async def search_flights(self, search_request: FlightSearchRequest) -> SearchResponse:
        """
        Search for available flights.
        
        Args:
            search_request: Flight search parameters
            
        Returns:
            SearchResponse: Flight search results with metadata
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
        
        # Perform search (mock data for now)
        flight_results = await self._search_flights_mock(search_request)
        
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
        Generate mock flight results for development.
        
        Args:
            search_request: Flight search parameters
            
        Returns:
            List[FlightResult]: Mock flight search results
        """
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
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
            
            # Calculate arrival time (1-8 hours later)
            flight_duration = random.randint(1, 8)
            arrival_time = departure_time + timedelta(hours=flight_duration)
            
            # Calculate base price
            base_price = random.randint(3000, 15000)
            if search_request.travel_class == "business":
                base_price *= 2.5
            elif search_request.travel_class == "first":
                base_price *= 4
            
            # Apply passenger count
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
        
        # Sort by price
        results.sort(key=lambda x: x.price)
        
        return results[:search_request.max_results]
    
    async def _search_flights_xml_agency(self, search_request: FlightSearchRequest) -> List[FlightResult]:
        """
        Search flights using XML.Agency API (to be implemented).
        
        Args:
            search_request: Flight search parameters
            
        Returns:
            List[FlightResult]: Flight search results from XML.Agency
        """
        # TODO: Implement XML.Agency integration
        # This will be implemented when connecting to the actual API
        pass


class HotelSearchService(SearchService):
    """
    Hotel search service for finding available accommodations.
    
    This service handles hotel search operations with location-based
    filtering, price ranges, and amenity requirements.
    """
    
    async def search_hotels(self, search_request: HotelSearchRequest) -> SearchResponse:
        """
        Search for available hotels.
        
        Args:
            search_request: Hotel search parameters
            
        Returns:
            SearchResponse: Hotel search results with metadata
        """
        start_time = datetime.utcnow()
        search_id = self._generate_search_id()
        
        # Generate cache key
        cache_key = self._get_cache_key("hotel", search_request.dict())
        
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
        
        # Perform search (mock data for now)
        hotel_results = await self._search_hotels_mock(search_request)
        
        # Apply filters
        filtered_results = self._apply_hotel_filters(hotel_results, search_request)
        
        # Prepare response
        response_data = {
            "total_results": len(filtered_results),
            "results": [result.dict() for result in filtered_results]
        }
        
        # Cache results
        await self._cache_results(cache_key, response_data, settings.search_cache_ttl)
        
        return SearchResponse(
            search_id=search_id,
            total_results=len(filtered_results),
            results=[result.dict() for result in filtered_results],
            search_time=self._calculate_search_time(start_time),
            cached=False
        )
    
    async def _search_hotels_mock(self, search_request: HotelSearchRequest) -> List[HotelResult]:
        """
        Generate mock hotel results for development.
        
        Args:
            search_request: Hotel search parameters
            
        Returns:
            List[HotelResult]: Mock hotel search results
        """
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.3, 1.5))
        
        hotel_names = [
            "Grand Plaza", "City Inn", "Royal Hotel", "Garden View", "Business Center",
            "Comfort Suites", "Luxury Resort", "Budget Stay", "Heritage Palace", "Modern Tower"
        ]
        
        amenities_pool = [
            "WiFi", "Pool", "Gym", "Restaurant", "Spa", "Parking", "Airport Shuttle",
            "Room Service", "Business Center", "Laundry", "Pet Friendly", "Breakfast"
        ]
        
        room_types = ["Standard", "Deluxe", "Suite", "Executive", "Family"]
        
        results = []
        num_results = random.randint(8, 25)
        
        for i in range(num_results):
            hotel_name = random.choice(hotel_names)
            rating = round(random.uniform(2.5, 5.0), 1)
            price_per_night = random.randint(1500, 8000)
            
            # Random amenities
            num_amenities = random.randint(3, 8)
            amenities = random.sample(amenities_pool, num_amenities)
            
            hotel_result = HotelResult(
                hotel_id=f"HTL{random.randint(10000, 99999)}",
                name=f"{hotel_name} {search_request.location}",
                address=f"{random.randint(1, 999)} {random.choice(['Main St', 'Park Ave', 'Central Rd'])}",
                city=search_request.location,
                rating=rating,
                price_per_night=price_per_night,
                amenities=amenities,
                room_types=random.sample(room_types, random.randint(2, 4)),
                distance_from_center=round(random.uniform(0.5, 15.0), 1),
                cancellation_policy=random.choice(["Free cancellation", "Moderate cancellation", "Strict cancellation"]),
                images=[f"https://example.com/hotel_{i}_{j}.jpg" for j in range(random.randint(3, 6))],
                description=f"Comfortable accommodation in {search_request.location} with modern amenities."
            )
            
            results.append(hotel_result)
        
        # Sort by price
        results.sort(key=lambda x: x.price_per_night)
        
        return results
    
    def _apply_hotel_filters(self, results: List[HotelResult], search_request: HotelSearchRequest) -> List[HotelResult]:
        """
        Apply filters to hotel search results.
        
        Args:
            results: List of hotel results
            search_request: Search parameters with filters
            
        Returns:
            List[HotelResult]: Filtered hotel results
        """
        filtered_results = results
        
        # Price filter
        if search_request.min_price:
            filtered_results = [r for r in filtered_results if r.price_per_night >= search_request.min_price]
        
        if search_request.max_price:
            filtered_results = [r for r in filtered_results if r.price_per_night <= search_request.max_price]
        
        # Rating filter
        if search_request.rating:
            filtered_results = [r for r in filtered_results if r.rating >= search_request.rating]
        
        # Amenities filter
        if search_request.amenities:
            filtered_results = [
                r for r in filtered_results
                if all(amenity in r.amenities for amenity in search_request.amenities)
            ]
        
        return filtered_results[:search_request.max_results]


class BusSearchService(SearchService):
    """
    Bus search service for finding inter-city bus options.
    
    This service handles bus search operations with operator information,
    bus types, and journey details.
    """
    
    async def search_buses(self, search_request: BusSearchRequest) -> SearchResponse:
        """
        Search for available buses.
        
        Args:
            search_request: Bus search parameters
            
        Returns:
            SearchResponse: Bus search results with metadata
        """
        start_time = datetime.utcnow()
        search_id = self._generate_search_id()
        
        # Generate cache key
        cache_key = self._get_cache_key("bus", search_request.dict())
        
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
        
        # Perform search (mock data for now)
        bus_results = await self._search_buses_mock(search_request)
        
        # Prepare response
        response_data = {
            "total_results": len(bus_results),
            "results": [result.dict() for result in bus_results]
        }
        
        # Cache results
        await self._cache_results(cache_key, response_data, settings.search_cache_ttl)
        
        return SearchResponse(
            search_id=search_id,
            total_results=len(bus_results),
            results=[result.dict() for result in bus_results],
            search_time=self._calculate_search_time(start_time),
            cached=False
        )
    
    async def _search_buses_mock(self, search_request: BusSearchRequest) -> List[BusResult]:
        """
        Generate mock bus results for development.
        
        Args:
            search_request: Bus search parameters
            
        Returns:
            List[BusResult]: Mock bus search results
        """
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.2, 1.0))
        
        operators = ["GoBus", "RedBus", "Travel Express", "City Transport", "Metro Lines"]
        bus_types = ["AC Sleeper", "Non-AC Sleeper", "AC Semi-Sleeper", "Non-AC Semi-Sleeper", "AC Seater", "Non-AC Seater"]
        amenities_pool = ["WiFi", "Charging Points", "Blanket", "Water Bottle", "Snacks", "Entertainment"]
        
        results = []
        num_results = random.randint(5, 12)
        
        for i in range(num_results):
            operator = random.choice(operators)
            bus_type = random.choice(bus_types)
            
            # Journey timing (evening to morning typically)
            departure_time = datetime.combine(
                search_request.travel_date,
                datetime.min.time().replace(
                    hour=random.randint(18, 23),
                    minute=random.choice([0, 15, 30, 45])
                )
            )
            
            # Journey duration (4-12 hours)
            journey_duration = random.randint(4, 12)
            arrival_time = departure_time + timedelta(hours=journey_duration)
            
            # Price based on bus type
            base_price = random.randint(800, 3000)
            if "AC" in bus_type:
                base_price *= 1.5
            if "Sleeper" in bus_type:
                base_price *= 1.3
            
            # Random amenities
            num_amenities = random.randint(2, 5)
            amenities = random.sample(amenities_pool, num_amenities)
            
            bus_result = BusResult(
                bus_id=f"BUS{random.randint(10000, 99999)}",
                operator=operator,
                bus_type=bus_type,
                origin=search_request.origin,
                destination=search_request.destination,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=f"{journey_duration}h {random.randint(0, 59)}m",
                seats_available=random.randint(5, 45),
                price=round(base_price, 2),
                amenities=amenities,
                boarding_points=[f"Bus Stand {j}" for j in range(random.randint(2, 4))],
                dropping_points=[f"Bus Stop {j}" for j in range(random.randint(2, 4))]
            )
            
            results.append(bus_result)
        
        # Sort by price
        results.sort(key=lambda x: x.price)
        
        return results[:search_request.max_results]
