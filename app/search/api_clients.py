"""
External API Clients

This module provides clients for integrating with external travel APIs:
- XML.Agency for flights
- Supplier APIs for hotels
- Bus operator APIs

These clients handle authentication, request formatting, response parsing,
and error handling for external API calls.
"""

import httpx
import xmltodict
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from abc import ABC, abstractmethod
import hashlib
import hmac
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""
    pass


class AuthenticationError(APIClientError):
    """Authentication failed with external API."""
    pass


class RateLimitError(APIClientError):
    """API rate limit exceeded."""
    pass


class SupplierError(APIClientError):
    """Error from supplier API."""
    pass


# =============================================================================
# Base API Client
# =============================================================================

class BaseAPIClient(ABC):
    """Base class for external API clients."""
    
    def __init__(self, base_url: str, api_key: str, api_secret: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @abstractmethod
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with the API."""
        pass
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        pass
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.get_headers()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Try to parse as JSON, fall back to XML
            content_type = response.headers.get("content-type", "")
            if "xml" in content_type:
                return xmltodict.parse(response.text)
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            else:
                raise APIClientError(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise APIClientError(f"Request failed: {str(e)}")


# =============================================================================
# Flight API Client (XML.Agency Style)
# =============================================================================

class FlightAPIClient(BaseAPIClient):
    """
    Client for flight search APIs (XML.Agency/Amadeus style).
    
    This client handles:
    - Authentication with credentials
    - Flight search (one-way, round-trip, multi-city)
    - Flight pricing and availability
    - Booking creation and PNR management
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.flight_api_url or "https://api.example.com",
            api_key=settings.flight_api_key or "",
            api_secret=settings.flight_api_secret or ""
        )
        self.session_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    def get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.session_token}" if self.session_token else "",
            "X-API-Key": self.api_key
        }
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate and get session token."""
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/token",
                json={
                    "api_key": self.api_key,
                    "api_secret": self.api_secret
                }
            )
            response.raise_for_status()
            data = response.json()
            
            self.session_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return data
        except Exception as e:
            logger.error(f"Flight API authentication failed: {e}")
            raise AuthenticationError(str(e))
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid session token."""
        if not self.session_token or (self.token_expiry and datetime.utcnow() >= self.token_expiry):
            await self.authenticate()
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_class: str = "ECONOMY"
    ) -> Dict[str, Any]:
        """
        Search for available flights.
        
        Args:
            origin: Origin airport code (IATA)
            destination: Destination airport code (IATA)
            departure_date: Departure date
            return_date: Return date for round-trip
            adults: Number of adult passengers
            children: Number of child passengers
            infants: Number of infant passengers
            cabin_class: Cabin class (ECONOMY, BUSINESS, FIRST)
            
        Returns:
            Dict with flight search results
        """
        await self._ensure_authenticated()
        
        search_request = {
            "search_type": "round_trip" if return_date else "one_way",
            "segments": [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date.isoformat()
                }
            ],
            "passengers": {
                "adults": adults,
                "children": children,
                "infants": infants
            },
            "cabin_class": cabin_class,
            "direct_only": False,
            "include_baggage": True
        }
        
        if return_date:
            search_request["segments"].append({
                "origin": destination,
                "destination": origin,
                "departure_date": return_date.isoformat()
            })
        
        return await self._make_request("POST", "/flights/search", data=search_request)
    
    async def get_flight_pricing(self, offer_id: str) -> Dict[str, Any]:
        """
        Get detailed pricing for a flight offer.
        
        Args:
            offer_id: Flight offer ID from search results
            
        Returns:
            Dict with detailed pricing information
        """
        await self._ensure_authenticated()
        return await self._make_request("GET", f"/flights/pricing/{offer_id}")
    
    async def create_booking(
        self,
        offer_id: str,
        passengers: List[Dict[str, Any]],
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a flight booking.
        
        Args:
            offer_id: Flight offer ID
            passengers: List of passenger details
            contact_info: Contact information
            
        Returns:
            Dict with booking confirmation and PNR
        """
        await self._ensure_authenticated()
        
        booking_request = {
            "offer_id": offer_id,
            "passengers": passengers,
            "contact": contact_info,
            "remarks": []
        }
        
        return await self._make_request("POST", "/flights/booking", data=booking_request)
    
    async def get_booking(self, pnr: str) -> Dict[str, Any]:
        """Get booking details by PNR."""
        await self._ensure_authenticated()
        return await self._make_request("GET", f"/flights/booking/{pnr}")
    
    async def cancel_booking(self, pnr: str, reason: str) -> Dict[str, Any]:
        """Cancel a flight booking."""
        await self._ensure_authenticated()
        return await self._make_request(
            "POST",
            f"/flights/booking/{pnr}/cancel",
            data={"reason": reason}
        )


# =============================================================================
# Bus API Client
# =============================================================================

class BusAPIClient(BaseAPIClient):
    """
    Client for bus booking APIs.
    
    This client handles:
    - Bus route search
    - Seat availability and selection
    - Bus booking creation
    - Ticket management
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.bus_api_url or "https://bus-api.example.com",
            api_key=settings.bus_api_key or "",
            api_secret=settings.bus_api_secret or ""
        )
    
    def get_headers(self) -> Dict[str, str]:
        # Generate signature for authentication
        timestamp = datetime.utcnow().isoformat()
        signature = self._generate_signature(timestamp)
        
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }
    
    def _generate_signature(self, timestamp: str) -> str:
        """Generate HMAC signature for API authentication."""
        if not self.api_secret:
            return ""
        message = f"{self.api_key}{timestamp}"
        return hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def authenticate(self) -> Dict[str, Any]:
        """Bus API typically uses signature-based auth, no separate token needed."""
        return {"authenticated": True}
    
    async def search_buses(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        bus_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for available buses.
        
        Args:
            origin: Origin city/station
            destination: Destination city/station
            travel_date: Travel date
            bus_type: Optional bus type filter (AC/NON-AC, SLEEPER, SEATER)
            
        Returns:
            Dict with available buses and schedules
        """
        params = {
            "origin": origin,
            "destination": destination,
            "date": travel_date.isoformat()
        }
        
        if bus_type:
            params["bus_type"] = bus_type
        
        return await self._make_request("GET", "/buses/search", params=params)
    
    async def get_seat_layout(self, bus_id: str, travel_date: date) -> Dict[str, Any]:
        """
        Get seat layout and availability for a bus.
        
        Args:
            bus_id: Bus ID from search results
            travel_date: Travel date
            
        Returns:
            Dict with seat layout and availability
        """
        return await self._make_request(
            "GET",
            f"/buses/{bus_id}/seats",
            params={"date": travel_date.isoformat()}
        )
    
    async def get_boarding_points(self, bus_id: str, origin: str) -> Dict[str, Any]:
        """Get available boarding points for a bus."""
        return await self._make_request(
            "GET",
            f"/buses/{bus_id}/boarding-points",
            params={"city": origin}
        )
    
    async def get_dropping_points(self, bus_id: str, destination: str) -> Dict[str, Any]:
        """Get available dropping points for a bus."""
        return await self._make_request(
            "GET",
            f"/buses/{bus_id}/dropping-points",
            params={"city": destination}
        )
    
    async def create_booking(
        self,
        bus_id: str,
        travel_date: date,
        seats: List[str],
        passengers: List[Dict[str, Any]],
        boarding_point_id: str,
        dropping_point_id: str,
        contact_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a bus booking.
        
        Args:
            bus_id: Bus ID
            travel_date: Travel date
            seats: List of selected seat numbers
            passengers: Passenger details
            boarding_point_id: Boarding point ID
            dropping_point_id: Dropping point ID
            contact_info: Contact information
            
        Returns:
            Dict with booking confirmation
        """
        booking_request = {
            "bus_id": bus_id,
            "date": travel_date.isoformat(),
            "seats": seats,
            "passengers": passengers,
            "boarding_point": boarding_point_id,
            "dropping_point": dropping_point_id,
            "contact": contact_info
        }
        
        return await self._make_request("POST", "/buses/booking", data=booking_request)
    
    async def get_booking(self, ticket_id: str) -> Dict[str, Any]:
        """Get bus booking details."""
        return await self._make_request("GET", f"/buses/booking/{ticket_id}")
    
    async def cancel_booking(self, ticket_id: str, reason: str) -> Dict[str, Any]:
        """Cancel a bus booking."""
        return await self._make_request(
            "POST",
            f"/buses/booking/{ticket_id}/cancel",
            data={"reason": reason}
        )


# =============================================================================
# Hotel API Client
# =============================================================================

class HotelAPIClient(BaseAPIClient):
    """
    Client for hotel booking APIs.
    
    This client handles:
    - Hotel search and availability
    - Room pricing and packages
    - Hotel booking creation
    - Booking modifications
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.hotel_api_url or "https://hotel-api.example.com",
            api_key=settings.hotel_api_key or "",
            api_secret=settings.hotel_api_secret or ""
        )
        self.access_token: Optional[str] = None
    
    def get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "X-API-Key": self.api_key
        }
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with hotel API."""
        try:
            response = await self.client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                }
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token")
            return data
        except Exception as e:
            logger.error(f"Hotel API authentication failed: {e}")
            raise AuthenticationError(str(e))
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token:
            await self.authenticate()
    
    async def search_hotels(
        self,
        city: str,
        checkin_date: date,
        checkout_date: date,
        rooms: int = 1,
        adults: int = 2,
        children: int = 0,
        star_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for available hotels.
        
        Args:
            city: City name or code
            checkin_date: Check-in date
            checkout_date: Check-out date
            rooms: Number of rooms
            adults: Number of adults
            children: Number of children
            star_rating: Optional star rating filter
            
        Returns:
            Dict with hotel search results
        """
        await self._ensure_authenticated()
        
        search_request = {
            "city": city,
            "checkin": checkin_date.isoformat(),
            "checkout": checkout_date.isoformat(),
            "rooms": rooms,
            "adults": adults,
            "children": children
        }
        
        if star_rating:
            search_request["star_rating"] = star_rating
        
        return await self._make_request("POST", "/hotels/search", data=search_request)
    
    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Get detailed hotel information."""
        await self._ensure_authenticated()
        return await self._make_request("GET", f"/hotels/{hotel_id}")
    
    async def get_room_availability(
        self,
        hotel_id: str,
        checkin_date: date,
        checkout_date: date,
        rooms: int = 1
    ) -> Dict[str, Any]:
        """Get room availability and pricing."""
        await self._ensure_authenticated()
        return await self._make_request(
            "GET",
            f"/hotels/{hotel_id}/rooms",
            params={
                "checkin": checkin_date.isoformat(),
                "checkout": checkout_date.isoformat(),
                "rooms": rooms
            }
        )
    
    async def create_booking(
        self,
        hotel_id: str,
        room_id: str,
        checkin_date: date,
        checkout_date: date,
        guests: List[Dict[str, Any]],
        contact_info: Dict[str, Any],
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a hotel booking.
        
        Args:
            hotel_id: Hotel ID
            room_id: Room type ID
            checkin_date: Check-in date
            checkout_date: Check-out date
            guests: Guest details
            contact_info: Contact information
            special_requests: Special requests
            
        Returns:
            Dict with booking confirmation
        """
        await self._ensure_authenticated()
        
        booking_request = {
            "hotel_id": hotel_id,
            "room_id": room_id,
            "checkin": checkin_date.isoformat(),
            "checkout": checkout_date.isoformat(),
            "guests": guests,
            "contact": contact_info,
            "special_requests": special_requests or ""
        }
        
        return await self._make_request("POST", "/hotels/booking", data=booking_request)
    
    async def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """Get hotel booking details."""
        await self._ensure_authenticated()
        return await self._make_request("GET", f"/hotels/booking/{booking_id}")
    
    async def cancel_booking(self, booking_id: str, reason: str) -> Dict[str, Any]:
        """Cancel a hotel booking."""
        await self._ensure_authenticated()
        return await self._make_request(
            "POST",
            f"/hotels/booking/{booking_id}/cancel",
            data={"reason": reason}
        )


# =============================================================================
# Factory Functions
# =============================================================================

def get_flight_client() -> FlightAPIClient:
    """Get flight API client instance."""
    return FlightAPIClient()


def get_bus_client() -> BusAPIClient:
    """Get bus API client instance."""
    return BusAPIClient()


def get_hotel_client() -> HotelAPIClient:
    """Get hotel API client instance."""
    return HotelAPIClient()
