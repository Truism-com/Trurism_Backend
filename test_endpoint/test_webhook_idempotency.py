import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_duplicate_webhook_event_ignored():
    from app.payments.services import WebhookService
    from app.payments.models import WebhookLog

    mock_db = AsyncMock()
    service = WebhookService(db=mock_db)

    existing = WebhookLog(id=1, razorpay_event_id="evt_001", is_processed=True)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db.execute.return_value = mock_result

    result = await service.process_webhook(
        event_type="payment.captured",
        payload={},
        signature="sig",
        is_verified=True,
        razorpay_event_id="evt_001"  
    )
    
    assert result.id == 1
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_new_webhook_event_is_processed():
    from app.payments.services import WebhookService

    mock_db = AsyncMock()
    service = WebhookService(db=mock_db)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None   
    mock_db.execute.return_value = mock_result

    service._handle_payment_captured = AsyncMock()

    await service.process_webhook(
        event_type="payment.captured",
        payload={},
        signature="sig",
        is_verified=True,
        razorpay_event_id="evt_NEW"
    )

    service._handle_payment_captured.assert_called_once()
    mock_db.add.assert_called_once()