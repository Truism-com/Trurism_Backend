# tests/test_booking_schema.py
import pytest
from datetime import date
from pydantic import ValidationError
from app.booking.schemas import FlightBookingRequest
from app.booking.models import PaymentMethod

ADULT = {
    "title": "Mr", "first_name": "John", "last_name": "Doe",
    "dob": date(1990, 1, 1), "type": "ADT", "email": "j@j.com"
}
INFANT = {**ADULT, "type": "INF", "dob": date(2025, 6, 1)}

BASE = {
    "offer_id": "OF1",
    "search_id": "SR1",
    "payment_details": {"method": PaymentMethod.UPI, "upi_id": "x@upi"},
    "contact_email": "t@t.com",
    "contact_phone": "+910000000000",
}

def test_too_many_passengers_rejected():
    with pytest.raises(ValidationError, match="at most 9"):
        FlightBookingRequest(**BASE, passengers=[ADULT] * 10)

def test_more_infants_than_adults_rejected():
    # 1 adult, 2 infants
    with pytest.raises(ValidationError, match="infants cannot exceed"):
        FlightBookingRequest(**BASE, passengers=[ADULT, INFANT, INFANT])

def test_no_adult_rejected():
    with pytest.raises(ValidationError, match="At least one adult"):
        FlightBookingRequest(**BASE, passengers=[INFANT])

def test_valid_booking_passes():
    req = FlightBookingRequest(**BASE, passengers=[ADULT])
    assert req.offer_id == "OF1"

def test_missing_offer_id_rejected():
    bad = {**BASE}
    bad.pop("offer_id", None)
    with pytest.raises(ValidationError):
        FlightBookingRequest(**bad, passengers=[ADULT])