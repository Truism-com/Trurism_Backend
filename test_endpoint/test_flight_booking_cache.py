import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_booking_without_cached_search_returns_400(client, auth_header):

    with patch("app.core.redis.get_redis_client") as mock_get:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None) 
        mock_get.return_value = mock_redis

        resp = await client.post("/bookings/flights", headers=auth_header, json={
            "offer_id": "OF_FAKE",
            "search_id": "SR_FAKE",
            "passengers": [{
                "title": "Mr", "first_name": "A", "last_name": "B",
                "dob": "1990-01-01", "type": "ADT"
            }],
            "payment_details": {"method": "upi", "upi_id": "x@upi"},
            "contact_email": "a@b.com", "contact_phone": "+910000000000"
        })

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_booking_when_redis_unavailable_returns_503(client, auth_header):

    with patch("app.core.redis.get_redis_client", return_value=None):
        resp = await client.post("/bookings/flights", headers=auth_header, json={
            "offer_id": "OF1", "search_id": "SR1",
            "passengers": [{"title": "Mr", "first_name": "A", "last_name": "B",
                            "dob": "1990-01-01", "type": "ADT"}],
            "payment_details": {"method": "upi", "upi_id": "x@upi"},
            "contact_email": "a@b.com", "contact_phone": "+910000000000"
        })

    assert resp.status_code == 503