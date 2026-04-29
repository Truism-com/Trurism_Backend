import pytest
from unittest.mock import AsyncMock, MagicMock
from app.payments.services import WebhookService
from app.payments.models import WebhookLog

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_process_webhook_idempotent_early_exit(mock_db_session):
    service = WebhookService(db=mock_db_session)
    
    # Mock that the DB query returns an existing log
    existing_log = WebhookLog(id=1, razorpay_event_id="evt_test123", is_processed=True)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_log
    mock_db_session.execute.return_value = mock_result
    
    # Process the webhook
    result = await service.process_webhook(
        event_type="payment.captured",
        payload={"dummy": "data"},
        signature="test_signature",
        is_verified=True,
        razorpay_event_id="evt_test123"
    )
    
    # It should return the existing log and NOT add a new one
    assert result.id == 1
    assert result.razorpay_event_id == "evt_test123"
    mock_db_session.add.assert_not_called()

@pytest.mark.asyncio
async def test_process_webhook_new_event(mock_db_session):
    service = WebhookService(db=mock_db_session)
    
    # Mock that the DB query returns None (no existing log)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    # We must mock the event handler methods that process_webhook calls internally
    service._handle_payment_captured = AsyncMock()
    
    # Process the webhook
    result = await service.process_webhook(
        event_type="payment.captured",
        payload={"dummy": "data"},
        signature="test_signature",
        is_verified=True,
        razorpay_event_id="evt_new456"
    )
    
    # It should add a new log to the session
    assert mock_db_session.add.call_count == 1
    
    # Validate the log was set as processed
    assert result.is_processed is True
    assert result.event_type == "payment.captured"
