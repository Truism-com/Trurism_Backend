import pytest
from pydantic import ValidationError
from datetime import date
from app.booking.schemas import FlightBookingRequest
from app.booking.models import PaymentMethod

def test_too_many_passengers_rejected(valid_adult_passenger_data):
    passengers = [valid_adult_passenger_data for _ in range(10)]
    data = {
        "offer_id": "OFFER123",
        "passengers": passengers,
        "payment_details": {"method": PaymentMethod.UPI, "upi_id": "test@upi"},
        "contact_email": "test@example.com",
        "contact_phone": "+1234567890"
    }
    with pytest.raises(ValidationError) as exc_info:
        FlightBookingRequest(**data)
    assert "at most 9 items" in str(exc_info.value)

def test_infant_to_adult_ratio_rejected(valid_adult_passenger_data):
    infant_data = valid_adult_passenger_data.copy()
    infant_data["type"] = "INF"
    infant_data["dob"] = date(2025, 1, 1)

    # 1 Adult, 2 Infants -> Invalid via validate_passengers classmethod
    passengers = [valid_adult_passenger_data, infant_data, infant_data]
    
    data = {
        "offer_id": "OFFER123",
        "passengers": passengers,
        "payment_details": {"method": PaymentMethod.UPI, "upi_id": "test@upi"},
        "contact_email": "test@example.com",
        "contact_phone": "+1234567890"
    }
    with pytest.raises(ValidationError) as exc_info:
        FlightBookingRequest(**data)
    assert "Number of infants cannot exceed number of adults" in str(exc_info.value)

def test_missing_adult_rejected():
    infant_data = {
        "title": "Mstr",
        "first_name": "Baby",
        "last_name": "Doe",
        "dob": date(2025, 1, 1),
        "type": "INF"
    }
    data = {
        "offer_id": "OFFER123",
        "passengers": [infant_data],
        "payment_details": {"method": PaymentMethod.UPI, "upi_id": "test@upi"},
        "contact_email": "test@example.com",
        "contact_phone": "+1234567890"
    }
    with pytest.raises(ValidationError) as exc_info:
        FlightBookingRequest(**data)
    assert "At least one adult passenger is required" in str(exc_info.value)
