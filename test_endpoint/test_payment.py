import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_wallet_insufficient_balance_raises():
    from app.wallet.services import WalletService, InsufficientBalanceError, WalletStatus
    from app.wallet.models import Wallet

    mock_wallet = MagicMock(spec=Wallet)
    mock_wallet.status = WalletStatus.ACTIVE
    mock_wallet.balance = 100.00
    mock_wallet.is_active = True

    mock_db = AsyncMock()
    service = WalletService(db=mock_db)

    async def fake_get_wallet_by_user_id(user_id):
        return mock_wallet

    service.get_wallet_by_user_id = fake_get_wallet_by_user_id

    with pytest.raises(InsufficientBalanceError):
        await service.debit(user_id=1, amount=500.00, description="test")

@pytest.mark.asyncio
async def test_razorpay_signature_verified_before_booking():
    from app.payments.services import RazorpayService

    mock_db = AsyncMock()
    service = RazorpayService(db=mock_db)

    with patch.object(service, "verify_payment_signature", return_value=False) as mock_verify:
        try:
            await service.verify_payment(
                razorpay_order_id="order_fake",
                razorpay_payment_id="pay_fake",
                razorpay_signature="BADSIG",
            )
        except Exception:
            pass 

    mock_verify.assert_called_once()


@pytest.mark.asyncio
async def test_split_payment_wallet_debited_once():
    from app.booking.payment_processor import BookingPaymentProcessor, PaymentMode

    mock_db = AsyncMock()
    processor = BookingPaymentProcessor(db=mock_db)

    processor.wallet_service = AsyncMock()
    processor.wallet_service.place_hold = AsyncMock(return_value={"hold_id": "h1", "status": "held"})
    processor.wallet_service.debit = AsyncMock(return_value={"status": "debited"})
    processor.razorpay_service = AsyncMock()
    processor.razorpay_service.capture_payment = AsyncMock(return_value={"status": "captured"})

    await processor.process_payment(
        user_id=1, amount=1000, payment_mode=PaymentMode.WALLET_RAZORPAY,
        booking_id=99, booking_type="flight",
        razorpay_payment_id="pay_x", razorpay_order_id="ord_x",
        razorpay_signature="sig_x", use_wallet_amount=200
    )

    assert processor.wallet_service.debit.call_count == 1