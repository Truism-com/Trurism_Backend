"""
AIR IQ REST API Client

Active flight integration. Replaces XML.Agency SOAP client.

Endpoints used:
- POST /login         - get JWT token
- GET  /sectors       - available IATA routes
- POST /availability  - available dates for a route
- POST /search        - search flights, returns ticket_id
- POST /book          - issue ticket using ticket_id
- GET  /ticket        - fetch booking details by booking_id

Token is cached in Redis with TTL 3300s (55min buffer before 3599s expiry).
Falls back to module-level dict when Redis is not available.
"""

import logging
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.search.schemas import FlightResult, FlightSearchRequest, TravelClass

logger = logging.getLogger(__name__)

# In-process token cache - used when Redis is unavailable
# Structure: {agency_id: {"token": str, "expires_at": float}}
_local_token_cache: Dict[str, Dict[str, Any]] = {}

# AIR IQ token TTL buffer - cache for 55min, token valid for 59min
_TOKEN_CACHE_TTL = 3300


class AirIQAuthError(Exception):
    """Authentication failed with AIR IQ API."""
    pass


class AirIQError(Exception):
    """General AIR IQ API error."""
    pass


class AirIQClient:
    """
    REST client for AIR IQ flight API.

    Uses settings.airiq_base_url (derived from FLIGHT_URL),
    settings.flight_login_id, settings.flight_password,
    settings.flight_api_key.
    """

    def __init__(self):
        self.base_url = settings.airiq_base_url
        self.login_id = settings.flight_login_id
        self.password = settings.flight_password
        self.api_key = settings.flight_api_key
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self._http.aclose()

    def _auth_headers(self, token: str) -> Dict[str, str]:
        return {
            "api-key": self.api_key,
            "Authorization": token,
        }

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _get_cached_token(self) -> Optional[str]:
        """Check in-process token cache. Returns token string or None."""
        entry = _local_token_cache.get(self.login_id)
        if entry and entry["expires_at"] > time.time():
            return entry["token"]
        return None

    def _set_cached_token(self, token: str):
        """Store token in in-process cache with TTL."""
        _local_token_cache[self.login_id] = {
            "token": token,
            "expires_at": time.time() + _TOKEN_CACHE_TTL,
        }

    async def _get_redis_token(self) -> Optional[str]:
        """Try to fetch token from Redis."""
        try:
            from app.core.redis import get_redis_client
            redis = get_redis_client()
            if not redis:
                return None
            key = f"air_iq:token:{self.login_id}"
            value = await redis.get(key)
            return value if value else None
        except Exception as e:
            logger.warning("Redis token fetch failed: %s", e)
            return None

    async def _set_redis_token(self, token: str):
        """Store token in Redis with TTL."""
        try:
            from app.core.redis import get_redis_client
            redis = get_redis_client()
            if not redis:
                return
            key = f"air_iq:token:{self.login_id}"
            await redis.setex(key, _TOKEN_CACHE_TTL, token)
        except Exception as e:
            logger.warning("Redis token store failed: %s", e)

    async def _login(self) -> str:
        """
        POST /login to get Bearer token.
        Returns full token string including 'Bearer ' prefix.
        """
        if not self.base_url:
            raise AirIQAuthError(
                "FLIGHT_URL not configured. Set it in .env to the AIR IQ login URL."
            )
        if not self.login_id or not self.password:
            raise AirIQAuthError(
                "FLIGHT_LOGIN_ID or FLIGHT_PASSWORD not set in .env."
            )

        url = f"{self.base_url}/login"
        try:
            response = await self._http.post(
                url,
                headers={"api-key": self.api_key},
                json={"Username": self.login_id, "Password": self.password},
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("token", "")
            if not token:
                raise AirIQAuthError("Login response missing token field")
            logger.info(
                "AIR IQ login success. agency_id=%s expiration=%s",
                data.get("user", {}).get("agency_id"),
                data.get("expiration"),
            )
            return token
        except httpx.HTTPStatusError as e:
            raise AirIQAuthError(
                f"AIR IQ login failed: {e.response.status_code} {e.response.text}"
            )
        except AirIQAuthError:
            raise
        except Exception as e:
            raise AirIQAuthError(f"AIR IQ login request failed: {e}")

    async def get_token(self) -> str:
        """
        Return valid AIR IQ Bearer token.
        Check Redis -> in-process cache -> re-login.
        """
        # 1. Redis cache
        token = await self._get_redis_token()
        if token:
            logger.debug("AIR IQ token: Redis cache hit")
            return token

        # 2. In-process cache
        token = self._get_cached_token()
        if token:
            logger.debug("AIR IQ token: in-process cache hit")
            return token

        # 3. Login
        token = await self._login()
        await self._set_redis_token(token)
        self._set_cached_token(token)
        return token

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    async def get_sectors(self) -> List[Dict[str, str]]:
        """
        GET /sectors - returns list of {Sector, Origin, Destination}.
        Cached 24h in Redis (routes don't change often).
        """
        try:
            from app.core.redis import get_redis_client
            redis = get_redis_client()
            if redis:
                cached = await redis.get("air_iq:sectors")
                if cached:
                    return json.loads(cached)
        except Exception:
            pass

        token = await self.get_token()
        response = await self._http.get(
            f"{self.base_url}/sectors",
            headers=self._auth_headers(token),
        )
        response.raise_for_status()
        data = response.json().get("data", [])

        try:
            from app.core.redis import get_redis_client
            redis = get_redis_client()
            if redis:
                await redis.setex("air_iq:sectors", 86400, json.dumps(data))
        except Exception:
            pass

        return data

    async def get_availability(self, origin: str, destination: str) -> List[str]:
        """
        POST /availability - returns list of available date strings.
        """
        token = await self.get_token()
        response = await self._http.post(
            f"{self.base_url}/availability",
            headers=self._auth_headers(token),
            json={"origin": origin.upper(), "destination": destination.upper()},
        )
        response.raise_for_status()
        return response.json().get("data", [])

    async def search_flights(
        self, request: FlightSearchRequest
    ) -> Tuple[List[FlightResult], str]:
        """
        POST /search - search available flights.

        Returns (list of FlightResult, search_id).
        search_id is the SHA-based cache key for downstream reference.

        AIR IQ date format: YYYY/MM/DD
        AIR IQ typo in response: 'arival_time' and 'arival_date' (single 'r').
        """
        body: Dict[str, Any] = {
            "origin": request.origin.upper(),
            "destination": request.destination.upper(),
            "departure_date": request.depart_date.strftime("%Y/%m/%d"),
            "adult": request.adults,
            "child": request.children or 0,
            "infant": request.infants or 0,
        }

        try:
            token = await self.get_token()
            response = await self._http.post(
                f"{self.base_url}/search",
                headers=self._auth_headers(token),
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

            logger.info(
                "AIR IQ search raw response: keys=%s code=%s status=%s data_type=%s data_len=%s first_item_keys=%s",
                list(payload.keys()),
                payload.get("code"),
                payload.get("status"),
                type(payload.get("data")).__name__,
                len(payload.get("data") or []) if isinstance(payload.get("data"), (list, dict)) else "N/A",
                list(payload["data"][0].keys()) if isinstance(payload.get("data"), list) and payload["data"] else "empty",
            )

            if str(payload.get("code", "")) != "200" or payload.get("status") != "success":
                logger.error(
                    "AIR IQ search non-success response: code=%s message=%s",
                    payload.get("code"),
                    payload.get("message", ""),
                )
                return [], ""

            raw_results = payload.get("data", []) or []
            results = self._parse_search_response(raw_results, request)
            logger.info(
                "AIR IQ search parsed: raw_count=%s parsed_count=%s",
                len(raw_results),
                len(results),
            )
            return results, ""

        except httpx.HTTPStatusError as e:
            # Token may have expired on the server side before our cache TTL
            if e.response.status_code == 401:
                logger.warning("AIR IQ 401 on search - clearing token cache, retrying once")
                _local_token_cache.pop(self.login_id, None)
                try:
                    from app.core.redis import get_redis_client
                    redis = get_redis_client()
                    if redis:
                        await redis.delete(f"air_iq:token:{self.login_id}")
                except Exception:
                    pass
                # Single retry with fresh token
                token = await self.get_token()
                response = await self._http.post(
                    f"{self.base_url}/search",
                    headers=self._auth_headers(token),
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()
                if str(payload.get("code", "")) != "200" or payload.get("status") != "success":
                    logger.error(
                        "AIR IQ search retry non-success: code=%s message=%s",
                        payload.get("code"),
                        payload.get("message", ""),
                    )
                    return [], ""
                raw_results = payload.get("data", []) or []
                results = self._parse_search_response(raw_results, request)
                return results, ""
            logger.error("AIR IQ search HTTP error: %s %s", e.response.status_code, e.response.text[:200])
            return [], ""
        except Exception as e:
            logger.error("AIR IQ search failed: %s", e, exc_info=True)
            return [], ""

    def _parse_search_response(
        self, raw: List[Dict[str, Any]], request: FlightSearchRequest
    ) -> List[FlightResult]:
        """
        Map AIR IQ search response fields to FlightResult.

        Key mapping notes:
        - ticket_id -> offer_id (used in booking)
        - arival_time / arival_date: AIR IQ typo, single 'r', must match exactly
        - flight_route 'Non - Stop' -> stops=0
        - cabin_baggage + hand_luggage -> baggage_allowance string
        - isinternational stored in metadata for GST calc later
        - price is per-adult from AIR IQ
        """
        results: List[FlightResult] = []

        for item in raw:
            try:
                ticket_id = item.get("ticket_id", "")
                if not ticket_id:
                    continue

                # Build departure and arrival datetimes
                dep_date_str = item.get("departure_date", "")
                dep_time_str = item.get("departure_time", "00:00")
                arr_date_str = item.get("arival_date", dep_date_str)   # AIR IQ typo
                arr_time_str = item.get("arival_time", "00:00")        # AIR IQ typo

                try:
                    dep_dt = datetime.strptime(
                        f"{dep_date_str} {dep_time_str}", "%Y-%m-%d %H:%M"
                    )
                except (ValueError, TypeError):
                    dep_dt = datetime.now(timezone.utc)

                try:
                    arr_dt = datetime.strptime(
                        f"{arr_date_str} {arr_time_str}", "%Y-%m-%d %H:%M"
                    )
                except (ValueError, TypeError):
                    arr_dt = dep_dt

                # Duration
                delta_minutes = int((arr_dt - dep_dt).total_seconds() / 60)
                if delta_minutes < 0:
                    # Overnight flight - add one day
                    delta_minutes += 1440
                hours = delta_minutes // 60
                mins = delta_minutes % 60
                duration = f"{hours}h {mins}m" if delta_minutes > 0 else "N/A"

                # Stops
                flight_route = item.get("flight_route", "")
                stops = 0 if "Non" in flight_route else 1

                # Baggage
                cabin_bag = item.get("cabin_baggage", "")
                hand_bag = item.get("hand_luggage", "")
                baggage_parts = []
                if cabin_bag:
                    baggage_parts.append(f"{cabin_bag}kg cabin")
                if hand_bag:
                    baggage_parts.append(f"{hand_bag}kg hand")
                baggage_str = ", ".join(baggage_parts) if baggage_parts else "Check with airline"

                result = FlightResult(
                    offer_id=ticket_id,
                    airline=item.get("airline", ""),
                    flight_number=item.get("flight_number", ""),
                    origin=item.get("origin", request.origin),
                    destination=item.get("destination", request.destination),
                    departure_time=dep_dt,
                    arrival_time=arr_dt,
                    duration=duration,
                    stops=stops,
                    price=float(item.get("price", 0)),
                    currency="INR",
                    travel_class=TravelClass.ECONOMY,
                    baggage_allowance=baggage_str,
                    refundable=False,
                    is_international=bool(item.get("isinternational")),
                )
                results.append(result)

            except Exception as parse_err:
                logger.warning("Failed to parse AIR IQ flight item: %s", parse_err)
                continue

        return results

    async def book_ticket(
        self,
        ticket_id: str,
        adult_info: List[Dict[str, Any]],
        child_info: List[Dict[str, Any]],
        infant_info: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        POST /book - issue ticket.

        Returns full response dict on success.
        Keys: code, status, message, booking_id, airline_code.

        WARNING: This issues a real ticket and charges the AIR IQ wallet.
        Only call after payment is captured.

        Passenger field requirements:
        - adult_info: title, first_name, last_name (+ passport fields if international)
        - child_info: title, first_name, last_name, dob (YYYY/MM/DD)
        - infant_info: title, first_name, last_name, dob, travel_with (int, adult index)
        """
        token = await self.get_token()

        total_pax = len(adult_info) + len(child_info) + len(infant_info)

        body = {
            "ticket_id": ticket_id,
            "total_pax": str(total_pax),
            "adult": str(len(adult_info)),
            "child": str(len(child_info)),
            "infant": str(len(infant_info)),
            "adult_info": adult_info,
            "child_info": child_info,
            "infant_info": infant_info,
        }

        try:
            response = await self._http.post(
                f"{self.base_url}/book",
                headers=self._auth_headers(token),
                json=body,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "200" or data.get("status") != "success":
                logger.error(
                    "AIR IQ book failed. ticket_id=%s message=%s",
                    ticket_id,
                    data.get("message", ""),
                )
                return {"success": False, "error": data.get("message", "Booking failed")}

            logger.info(
                "AIR IQ ticket booked. booking_id=%s airline_code=%s",
                data.get("booking_id"),
                data.get("airline_code"),
            )
            return {"success": True, **data}

        except httpx.HTTPStatusError as e:
            logger.error(
                "AIR IQ book HTTP error: %s %s", e.response.status_code, e.response.text[:200]
            )
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error("AIR IQ book failed: %s", e, exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_ticket_details(self, booking_id: str) -> Dict[str, Any]:
        """
        GET /ticket?booking_id={booking_id} - fetch booking details and PNR.
        """
        token = await self.get_token()

        try:
            response = await self._http.get(
                f"{self.base_url}/ticket",
                headers=self._auth_headers(token),
                params={"booking_id": booking_id},
            )
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            logger.error("AIR IQ get_ticket_details failed: %s", e, exc_info=True)
            return {}
