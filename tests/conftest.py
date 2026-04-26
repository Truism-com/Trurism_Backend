import pytest
from datetime import date
from httpx import AsyncClient

# This file sets up test fixtures that automatically inject data into your tests.

@pytest.fixture
def valid_adult_passenger_data():
    return {
        "title": "Mr",
        "first_name": "John",
        "last_name": "Doe",
        "dob": date(1990, 1, 1),
        "type": "ADT", # Depending on Enum value
        "email": "john@example.com"
    }
