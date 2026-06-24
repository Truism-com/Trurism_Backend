# DEPRECATED: XML.Agency SOAP client is no longer the primary flight integration.
# AIR IQ REST client (app/search/airiq_client.py) is the active integration.
# This file is kept as fallback only. Do not use in new code.
# To re-enable: un-comment in services.py and swap _search_flights_airiq back.
"""
XML.Agency Flight API Integration (SOAP 1.2)

Client for AeroSearch, AeroPrebook, AeroBook endpoints per v3.17 spec.
Uses zeep with SqliteCache to avoid repeated WSDL download latency.

DEPRECATED - kept as fallback. See airiq_client.py for active integration.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    import httpx
    from zeep import Client
    from zeep.cache import SqliteCache
    from zeep.transports import Transport
except ImportError:
    logging.getLogger(__name__).error(
        "zeep or httpx not installed. XML.Agency integration will not function."
    )

from app.core.config import settings
from app.search.schemas import FlightResult, FlightSearchRequest, TravelClass

logger = logging.getLogger(__name__)

# XML.Agency class value map per WSDL spec
TRAVEL_CLASS_MAP = {
    "economy": "Econom",
    "premium_economy": "PremiumEconomy",
    "business": "Business",
    "first": "First",
}

# XML.Agency date format for SearchFlight.Date
_DATE_FMT = "%d.%m.%Y"

# XML.Agency datetime format inside segment Departure/Arrival
_DT_FMT = "%d.%m.%Y %H:%M"


class XMLAgencyClient:
    """
    SOAP 1.2 client for XML.Agency Flight API v3.17.

    Credentials: set XML_AGENCY_USERNAME and XML_AGENCY_PASSWORD in .env.
    Sandbox: leave blank to use 'test'/'test' sandbox credentials.
    """

    SANDBOX_WSDL = "http://test-api.xml.agency/SiteCity?wsdl"

    def __init__(self):
        self.api_login = settings.xml_agency_username or "test"
        self.api_password = settings.xml_agency_password or "test"

        # Use sandbox WSDL when no production URL configured
        base_url = settings.xml_agency_base_url
        if base_url and base_url not in ("", "https://api.xmlagency.com"):
            self.wsdl_url = f"{base_url}/SiteCity?wsdl"
        else:
            self.wsdl_url = self.SANDBOX_WSDL

        self._client: Optional[Client] = None

    def _get_client(self) -> "Client":
        """Lazy-load synchronous zeep Client with 24-hour WSDL cache."""
        if self._client is None:
            cache_path = os.path.join(os.path.expanduser("~"), ".zeep_wsdl_cache.db")
            cache = SqliteCache(path=cache_path, timeout=86400)
            transport = Transport(
                operation_timeout=settings.xml_agency_timeout,
                cache=cache,
            )
            self._client = Client(self.wsdl_url, transport=transport)
        return self._client

    def _credentials(self) -> Dict[str, Any]:
        """Build AuthInfo structure per XML.Agency WSDL spec section 1.1."""
        return {
            "ApiLogin": self.api_login,
            "ApiPassword": self.api_password,
            "TokenGuid": "00000000-0000-0000-0000-000000000000",
            "DeviceId": "trurism-backend",
            "Language": "EN",
            "Currency": "USD",
        }

    async def search_flights(
        self, request: FlightSearchRequest
    ) -> Tuple[List[FlightResult], str]:
        """
        AeroSearch call per XML.Agency v3.17 spec section 2.1.

        Builds the exact SOAP structure from the spec:
          aeroSearchParams.SearchFlights = list of SearchFlight
          each SearchFlight has Date (DD.MM.YYYY), IATAFrom, IATATo

        Returns (results, SearchGuid).
        SearchGuid must be forwarded to AeroPrebook and AeroBook.
        """
        import asyncio

        client = self._get_client()

        search_flights = [
            {
                "Date": request.depart_date.strftime(_DATE_FMT),
                "IATAFrom": request.origin.upper(),
                "IATATo": request.destination.upper(),
            }
        ]
        # Round trip: add return leg
        if request.return_date:
            search_flights.append(
                {
                    "Date": request.return_date.strftime(_DATE_FMT),
                    "IATAFrom": request.destination.upper(),
                    "IATATo": request.origin.upper(),
                }
            )

        aero_params = {
            "Adults": request.adults,
            "Childs": request.children or 0,
            "Infants": request.infants or 0,
            "FlightClass": TRAVEL_CLASS_MAP.get(
                request.travel_class.value, "Econom"
            ),
            "SearchFlights": {"SearchFlight": search_flights},
        }

        try:
            response = await asyncio.to_thread(
                client.service.AeroSearch,
                credentials=self._credentials(),
                aeroSearchParams=aero_params,
            )

            # Per spec: check Success field, not ErrorCode
            if not getattr(response, "Success", False):
                error_code = getattr(response, "ErrorCode", None)
                error_str = getattr(response, "ErrorString", "Unknown error")
                logger.error(
                    "AeroSearch failed. ErrorCode=%s ErrorString=%s",
                    error_code,
                    error_str,
                )
                return [], ""

            search_guid = getattr(response, "SearchGuid", "") or ""
            raw_flight_data = getattr(response, "FlightData", None)

            results = self._parse_search_response(raw_flight_data)
            return results, search_guid

        except Exception as exc:
            logger.error("AeroSearch SOAP call raised: %s", exc, exc_info=True)
            return [], ""

    def _parse_search_response(self, raw_flight_data: Any) -> List[FlightResult]:
        """
        Parse AeroSearchResult.FlightData per spec section 2.1.2.

        Structure (zeep returns as objects):
          FlightData (list)
            FlightData.OfferCode
            FlightData.TotalPrice
            FlightData.Offers.OfferInfo (list)
              OfferInfo.Segments.OfferSegment (list)
                OfferSegment.Departure.Date  (DD.MM.YYYY HH:MM)
                OfferSegment.Arrival.Date
                OfferSegment.FlightNum
                OfferSegment.MarketingAirline
                OfferSegment.FlightClass
                OfferSegment.Baggage.Count + BaggageType
                OfferSegment.Rph  (1=outbound, 2=return)
        """
        results: List[FlightResult] = []
        if not raw_flight_data:
            return results

        # Zeep wraps repeated elements; unpack FlightData list
        flight_list = raw_flight_data if isinstance(raw_flight_data, list) else []
        if hasattr(raw_flight_data, "FlightData"):
            flight_list = raw_flight_data.FlightData

        for flight in flight_list:
            try:
                offer_code = getattr(flight, "OfferCode", None)
                if not offer_code:
                    continue

                total_price = float(getattr(flight, "TotalPrice", 0.0))

                # Get first OfferInfo for segment data
                offers_obj = getattr(flight, "Offers", None)
                offer_info_list = []
                if offers_obj and hasattr(offers_obj, "OfferInfo"):
                    offer_info_list = offers_obj.OfferInfo
                if not offer_info_list:
                    continue

                first_offer = offer_info_list[0]
                validating_airline = getattr(first_offer, "ValidatingAirline", "XX")

                segments_obj = getattr(first_offer, "Segments", None)
                segments = []
                if segments_obj and hasattr(segments_obj, "OfferSegment"):
                    segments = segments_obj.OfferSegment
                if not segments:
                    continue

                # Outbound = first segment with Rph==1
                outbound = [s for s in segments if getattr(s, "Rph", 1) == 1]
                if not outbound:
                    outbound = segments

                first_seg = outbound[0]
                last_seg = outbound[-1]

                dep_str = getattr(getattr(first_seg, "Departure", None), "Date", "")
                arr_str = getattr(getattr(last_seg, "Arrival", None), "Date", "")

                try:
                    dep_dt = datetime.strptime(dep_str, _DT_FMT)
                except (ValueError, TypeError):
                    dep_dt = datetime.now(timezone.utc)

                try:
                    arr_dt = datetime.strptime(arr_str, _DT_FMT)
                except (ValueError, TypeError):
                    arr_dt = dep_dt + timedelta(hours=3)

                # Duration from flight minutes (sum outbound segments)
                total_minutes = sum(
                    int(getattr(s, "FlightMinutes", 0)) for s in outbound
                )
                duration = (
                    f"{total_minutes // 60}h {total_minutes % 60}m"
                    if total_minutes
                    else "N/A"
                )

                stops = max(len(outbound) - 1, 0)

                # Baggage from first segment
                baggage_obj = getattr(first_seg, "Baggage", None)
                baggage_count = getattr(baggage_obj, "Count", 0) if baggage_obj else 0
                baggage_type = (
                    getattr(baggage_obj, "BaggageType", "Unknown")
                    if baggage_obj
                    else "Unknown"
                )
                baggage_str = (
                    f"{baggage_count} {baggage_type}"
                    if baggage_count
                    else "No checked baggage"
                )

                flight_class_raw = getattr(first_seg, "FlightClass", "Econom")
                travel_class = (
                    TravelClass.BUSINESS
                    if "Business" in flight_class_raw
                    else TravelClass.FIRST
                    if "First" in flight_class_raw
                    else TravelClass.PREMIUM_ECONOMY
                    if "Premium" in flight_class_raw
                    else TravelClass.ECONOMY
                )

                dep_iata = getattr(getattr(first_seg, "Departure", None), "Iata", "")
                arr_iata = getattr(getattr(last_seg, "Arrival", None), "Iata", "")
                flight_num = getattr(first_seg, "FlightNum", "N/A")

                result = FlightResult(
                    offer_id=offer_code,
                    airline=validating_airline,
                    flight_number=flight_num,
                    origin=dep_iata,
                    destination=arr_iata,
                    departure_time=dep_dt,
                    arrival_time=arr_dt,
                    duration=duration,
                    stops=stops,
                    price=total_price,
                    currency="USD",
                    travel_class=travel_class,
                    baggage_allowance=baggage_str,
                    refundable=False,
                )
                results.append(result)

            except Exception as parse_err:
                logger.warning("Failed to parse FlightData node: %s", parse_err)
                continue

        return results

    async def prebook_flight(self, offer_code: str, search_guid: str) -> bool:
        """
        AeroPrebook call per spec section 2.2.

        Success condition: response.Success == True (not ErrorCode check).
        Returns True if the fare is still valid and bookable.
        """
        import asyncio

        client = self._get_client()
        params = {
            "credentials": self._credentials(),
            "offerCode": offer_code,
            "searchId": search_guid,
        }
        try:
            response = await asyncio.to_thread(
                client.service.AeroPrebook, **params
            )
            if getattr(response, "Success", False):
                return True
            error_code = getattr(response, "ErrorCode", None)
            error_str = getattr(response, "ErrorString", "")
            logger.warning(
                "AeroPrebook rejected. ErrorCode=%s ErrorString=%s",
                error_code,
                error_str,
            )
            return False
        except Exception as exc:
            logger.error("AeroPrebook SOAP call raised: %s", exc, exc_info=True)
            return False

    async def book_flight(
        self, offer_code: str, search_guid: str, passenger_details: List[Any]
    ) -> str:
        """
        AeroBook call per spec section 2.4.

        **NEVER call in production without captured Razorpay payment.**

        Success condition: response.Success == True (not ErrorCode check).
        Returns PNR string on success, empty string on failure.
        """
        import asyncio

        client = self._get_client()

        zeep_passengers = []
        for p in passenger_details:
            p_dict = p.model_dump() if hasattr(p, "model_dump") else (p.dict() if hasattr(p, "dict") else p)

            dob = p_dict.get("dob")
            dob_str = dob.strftime("%d.%m.%Y") if hasattr(dob, "strftime") else str(dob or "01.01.1990")

            zeep_passengers.append(
                {
                    "Title": p_dict.get("title", "Mr"),
                    "FirstName": p_dict.get("first_name", ""),
                    "LastName": p_dict.get("last_name", ""),
                    "DateOfBirth": dob_str,
                    "PassengerType": p_dict.get("type", "ADT"),
                    "DocNum": p_dict.get("passport_number", ""),
                }
            )

        params = {
            "credentials": self._credentials(),
            "offerCode": offer_code,
            "searchId": search_guid,
            "tourists": {"Tourist": zeep_passengers},
        }

        try:
            response = await asyncio.to_thread(
                client.service.AeroBook, **params
            )
            if getattr(response, "Success", False):
                pnr = getattr(response, "BookCode", "") or ""
                logger.info("AeroBook success. PNR=%s", pnr)
                return pnr

            error_code = getattr(response, "ErrorCode", None)
            error_str = getattr(response, "ErrorString", "")
            logger.error(
                "AeroBook failed. ErrorCode=%s ErrorString=%s",
                error_code,
                error_str,
            )
            return ""
        except Exception as exc:
            logger.error("AeroBook SOAP call raised: %s", exc, exc_info=True)
            return ""
