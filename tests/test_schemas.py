import pytest
from pydantic import ValidationError
from datetime import date, timedelta
from app.booking.schemas import PassengerSchema
from app.booking.models import PassengerType

def test_valid_adult_passenger():
    data = {
        "title": "Mr",
        "first_name": "John",
        "last_name": "Doe",
        "dob": date(1990, 1, 1),
        "type": PassengerType.ADULT,
        "email": "johndoe@example.com"
    }
    passenger = PassengerSchema(**data)
    assert passenger.first_name == "John"
    assert passenger.last_name == "Doe"

def test_infant_age_validation_fails():
    old_dob = date.today() - timedelta(days=365 * 3)
    data = {
        "title": "Mstr",
        "first_name": "Baby",
        "last_name": "Doe",
        "dob": old_dob,
        "type": PassengerType.INFANT
    }
    with pytest.raises(ValidationError) as exc_info:
        PassengerSchema(**data)
    
    assert "Infants must be beneath 2 years of age" in str(exc_info.value)

def test_adult_age_validation_fails():
    young_dob = date.today() - timedelta(days=365 * 10)
    data = {
        "title": "Mr",
        "first_name": "Child",
        "last_name": "Pretending",
        "dob": young_dob,
        "type": PassengerType.ADULT
    }
    with pytest.raises(ValidationError) as exc_info:
        PassengerSchema(**data)
    
    assert "Adult passengers must be 12 years or older" in str(exc_info.value)

def test_missing_dob_rejected():
    data = {
        "title": "Mr",
        "first_name": "John",
        "last_name": "Doe",
        "type": PassengerType.ADULT
    }
    with pytest.raises(ValidationError) as exc_info:
        PassengerSchema(**data)
        
    assert "Field required" in str(exc_info.value) or "dob" in str(exc_info.value)

def test_name_too_long_rejected():
    data = {
        "title": "Mr",
        "first_name": "A" * 101,  # max_length is 100
        "last_name": "Doe",
        "dob": date(1990, 1, 1),
        "type": PassengerType.ADULT
    }
    with pytest.raises(ValidationError) as exc_info:
        PassengerSchema(**data)
    assert "String should have at most 100 characters" in str(exc_info.value)

def test_name_invalid_characters_rejected():
    data = {
        "title": "Mr",
        "first_name": "John123",  # invalid alpha constraint
        "last_name": "Doe",
        "dob": date(1990, 1, 1),
        "type": PassengerType.ADULT
    }
    with pytest.raises(ValidationError) as exc_info:
        PassengerSchema(**data)
    assert "only letters, spaces, and hyphens" in str(exc_info.value)

def test_invalid_title_rejected():
    data = {
        "title": "Captain",  # not in regex pattern
        "first_name": "John",
        "last_name": "Doe",
        "dob": date(1990, 1, 1),
        "type": PassengerType.ADULT
    }
    with pytest.raises(ValidationError) as exc_info:
        PassengerSchema(**data)
    assert "String should match pattern" in str(exc_info.value)
