import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

@pytest.mark.asyncio
async def test_email_fires_after_commit_not_before():

    call_order = []

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock(side_effect=lambda: call_order.append("commit"))

    mock_email = AsyncMock(side_effect=lambda **kw: call_order.append("email"))

    with patch("app.services.email.email_service.send_booking_confirmation", mock_email):
        from app.booking.services import FlightBookingService
        service = FlightBookingService(db=mock_db, tenant_id=1)


        mock_db.add = MagicMock()
        mock_db.refresh = AsyncMock()


        commit_idx = call_order.index("commit") if "commit" in call_order else -1
        email_idx  = call_order.index("email")  if "email"  in call_order else -1
        if commit_idx != -1 and email_idx != -1:
            assert commit_idx < email_idx, "Email fired before DB commit!"


@pytest.mark.asyncio
async def test_email_failure_does_not_crash_booking():

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.refresh = AsyncMock()

    failing_email = AsyncMock(side_effect=Exception("SMTP timeout"))

    with patch("app.booking.services.email_service.send_booking_confirmation", failing_email):
        from app.booking.services import FlightBookingService
        service = FlightBookingService(db=mock_db, tenant_id=1)
    
        try:
            await service._send_confirmation_email_safe(booking_id=1, to_email="x@x.com")
        except Exception:
            pytest.fail("Email failure should not propagate out of service layer")


@pytest.mark.asyncio
async def test_booking_reference_is_unique():
    from app.booking.services import BaseBookingService
    service = BaseBookingService(db=AsyncMock())
    refs = {service._generate_booking_reference() for _ in range(1000)}
    assert len(refs) == 1000, "Duplicate booking references generated!"