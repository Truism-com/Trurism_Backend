"""
Search Module Schemas

This module defines Pydantic schemas for search operations:
- Search request parameters for flights, hotels, and buses
- Search result schemas with pricing and availability
- Filtering and sorting options
- Search cache management schemas
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class TravelClass(str, Enum):
    """Travel class options for flights."""
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class PassengerType(str, Enum):
    """Passenger type for booking calculations."""
    ADULT = "ADT"
    CHILD = "CHD"
    INFANT = "INF"


class FlightSearchRequest(BaseModel):
    """
    Schema for flight search requests.
    
    Validates flight search parameters including origin, destination,
    dates, passenger count, and travel preferences.
    """
    origin: str = Field(..., min_length=3, max_length=3, description="Origin airport IATA code")
    destination: str = Field(..., min_length=3, max_length=3, description="Destination airport IATA code")
    depart_date: date = Field(..., description="Departure date")
    return_date: Optional[date] = Field(None, description="Return date for round trip")
    adults: int = Field(..., ge=1, le=9, description="Number of adult passengers")
    children: Optional[int] = Field(0, ge=0, le=9, description="Number of child passengers")
    infants: Optional[int] = Field(0, ge=0, le=9, description="Number of infant passengers")
    travel_class: TravelClass = Field(TravelClass.ECONOMY, description="Travel class")
    max_results: Optional[int] = Field(50, ge=1, le=100, description="Maximum search results")
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate return date is after departure date."""
        depart_date = info.data.get('depart_date')
        if v and depart_date and v <= depart_date:
            raise ValueError('Return date must be after departure date')
        return v
    
    @field_validator('origin', 'destination')
    @classmethod
    def validate_airport_codes(cls, v: str) -> str:
        """Validate airport codes are uppercase."""
        return v.upper()
    
    @field_validator('infants')
    @classmethod
    def validate_infants(cls, v: int, info) -> int:
        """Validate infant count doesn't exceed adult count."""
        adults = info.data.get('adults', 0)
        if v > adults:
            raise ValueError('Number of infants cannot exceed number of adults')
        return v


class HotelSearchRequest(BaseModel):
    """
    Schema for hotel search requests.
    
    Validates hotel search parameters including location, dates,
    room requirements, and guest preferences.
    """
    location: str = Field(..., min_length=2, description="Hotel location or city")
    checkin: date = Field(..., description="Check-in date")
    checkout: date = Field(..., description="Check-out date")
    rooms: int = Field(..., ge=1, le=9, description="Number of rooms")
    adults: int = Field(..., ge=1, le=18, description="Number of adult guests")
    children: Optional[int] = Field(0, ge=0, le=18, description="Number of child guests")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price per night")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price per night")
    rating: Optional[float] = Field(None, ge=1, le=5, description="Minimum hotel rating")
    amenities: Optional[List[str]] = Field(None, description="Required amenities")
    max_results: Optional[int] = Field(50, ge=1, le=100, description="Maximum search results")
    
    @field_validator('checkout')
    @classmethod
    def validate_checkout(cls, v: date, info) -> date:
        """Validate checkout date is after checkin date."""
        checkin = info.data.get('checkin')
        if checkin and v <= checkin:
            raise ValueError('Checkout date must be after checkin date')
        return v
    
    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v: Optional[float], info) -> Optional[float]:
        """Validate max price is greater than min price."""
        min_price = info.data.get('min_price')
        if min_price and v and v <= min_price:
            raise ValueError('Maximum price must be greater than minimum price')
        return v


class BusSearchRequest(BaseModel):
    """
    Schema for bus search requests.
    
    Validates bus search parameters including origin, destination,
    travel date, and passenger count.
    """
    origin: str = Field(..., min_length=2, description="Origin city or location")
    destination: str = Field(..., min_length=2, description="Destination city or location")
    travel_date: date = Field(..., description="Travel date")
    passengers: int = Field(..., ge=1, le=9, description="Number of passengers")
    return_date: Optional[date] = Field(None, description="Return date for round trip")
    max_results: Optional[int] = Field(50, ge=1, le=100, description="Maximum search results")
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate return date is after travel date."""
        travel_date = info.data.get('travel_date')
        if v and travel_date and v <= travel_date:
            raise ValueError('Return date must be after travel date')
        return v


class FlightResult(BaseModel):
    """
    Schema for flight search results.
    
    Represents a single flight option with pricing, timing,
    and airline information.
    """
    offer_id: str = Field(..., description="Unique flight offer identifier")
    airline: str = Field(..., description="Airline name")
    flight_number: str = Field(..., description="Flight number")
    origin: str = Field(..., description="Origin airport code")
    destination: str = Field(..., description="Destination airport code")
    departure_time: datetime = Field(..., description="Departure date and time")
    arrival_time: datetime = Field(..., description="Arrival date and time")
    duration: str = Field(..., description="Flight duration (e.g., '3h 30m')")
    stops: int = Field(0, description="Number of stops")
    aircraft: Optional[str] = Field(None, description="Aircraft type")
    price: float = Field(..., ge=0, description="Total price for all passengers")
    currency: str = Field("INR", description="Currency code")
    travel_class: TravelClass = Field(..., description="Travel class")
    baggage_allowance: Optional[str] = Field(None, description="Baggage allowance")
    refundable: bool = Field(False, description="Whether booking is refundable")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class HotelResult(BaseModel):
    """
    Schema for hotel search results.
    
    Represents a single hotel option with pricing, amenities,
    and location information.
    """
    hotel_id: str = Field(..., description="Unique hotel identifier")
    name: str = Field(..., description="Hotel name")
    address: str = Field(..., description="Hotel address")
    city: str = Field(..., description="City name")
    rating: float = Field(..., ge=1, le=5, description="Hotel rating")
    price_per_night: float = Field(..., ge=0, description="Price per night")
    currency: str = Field("INR", description="Currency code")
    amenities: List[str] = Field([], description="Available amenities")
    room_types: List[str] = Field([], description="Available room types")
    distance_from_center: Optional[float] = Field(None, description="Distance from city center in km")
    cancellation_policy: str = Field(..., description="Cancellation policy")
    images: List[str] = Field([], description="Hotel image URLs")
    description: Optional[str] = Field(None, description="Hotel description")


class BusResult(BaseModel):
    """
    Schema for bus search results.
    
    Represents a single bus option with pricing, timing,
    and operator information.
    """
    bus_id: str = Field(..., description="Unique bus identifier")
    operator: str = Field(..., description="Bus operator name")
    bus_type: str = Field(..., description="Type of bus (AC, Non-AC, Sleeper, etc.)")
    origin: str = Field(..., description="Origin location")
    destination: str = Field(..., description="Destination location")
    departure_time: datetime = Field(..., description="Departure date and time")
    arrival_time: datetime = Field(..., description="Arrival date and time")
    duration: str = Field(..., description="Journey duration (e.g., '8h 30m')")
    seats_available: int = Field(..., ge=0, description="Number of seats available")
    price: float = Field(..., ge=0, description="Price per passenger")
    currency: str = Field("INR", description="Currency code")
    amenities: List[str] = Field([], description="Bus amenities")
    boarding_points: List[str] = Field([], description="Available boarding points")
    dropping_points: List[str] = Field([], description="Available dropping points")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class SearchResponse(BaseModel):
    """
    Generic search response schema.
    
    Provides a consistent structure for all search responses
    with metadata and results.
    """
    search_id: str = Field(..., description="Unique search identifier")
    total_results: int = Field(..., ge=0, description="Total number of results found")
    results: List[dict] = Field(..., description="Search results")
    search_time: float = Field(..., description="Search execution time in seconds")
    cached: bool = Field(False, description="Whether results were served from cache")
    expires_at: Optional[datetime] = Field(None, description="Cache expiration time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchCacheRequest(BaseModel):
    """
    Schema for search cache management requests.
    
    Used for cache invalidation and management operations.
    """
    search_type: str = Field(..., description="Type of search (flight, hotel, bus)")
    cache_key: str = Field(..., description="Cache key to invalidate")
    reason: Optional[str] = Field(None, description="Reason for cache invalidation")
