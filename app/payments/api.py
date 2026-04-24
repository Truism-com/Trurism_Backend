"""
Payment API Endpoints

This module defines FastAPI endpoints for payment operations:
- Order creation for Razorpay checkout
- Payment verification after checkout
- Webhook handling for payment events
- Refund processing
- Convenience fee management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging
import json

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.payments.schemas import (
    OrderCreateRequest, OrderCreateResponse,
    PaymentVerifyRequest, PaymentVerifyResponse,
    RefundCreateRequest, RefundResponse,
    ConvenienceFeeCreate, ConvenienceFeeResponse,
    TransactionResponse, ConvenienceFeeCalculation
)
from app.payments.services import RazorpayService, WebhookService
from app.payments.models import PaymentTransaction, Refund
from app.settings.models import ConvenienceFee

logger = logging.getLogger(__name__)

# Router for payment endpoints
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order", response_model=OrderCreateResponse)
async def create_payment_order(
    order_request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create Razorpay order for payment.
    
    This endpoint creates a Razorpay order with calculated convenience fees
    and returns order details for frontend Razorpay checkout.
    
    **Steps:**
    1. Calculate convenience fee based on payment method
    2. Add GST (18%) on convenience fee
    3. Create Razorpay order
    4. Return order details to frontend
    
    **Frontend Usage:**
    ```javascript
    const options = {
        key: response.key_id,
        amount: response.amount,
        currency: response.currency,
        order_id: response.order_id,
        handler: function(response) {
            // Send to /payments/verify endpoint
            verifyPayment(response);
        }
    };
    const rzp = new Razorpay(options);
    rzp.open();
    ```
    
    Args:
        order_request: Order creation request
        current_user: Authenticated user
        db: Database session
        
    Returns:
        OrderCreateResponse: Razorpay order details
    """
    razorpay_service = RazorpayService(db)
    
    transaction, order_details = await razorpay_service.create_order(
        booking_id=order_request.booking_id,
        booking_type=order_request.booking_type,
        user_id=current_user.id,
        base_amount=order_request.base_amount,
        payment_method=order_request.payment_method.value if order_request.payment_method else None
    )
    
    return OrderCreateResponse(**order_details)


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    verify_request: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Verify payment after Razorpay checkout.
    
    This endpoint verifies the payment signature from Razorpay
    and updates the booking status to CONFIRMED.
    
    **Called from frontend after payment:**
    ```javascript
    function verifyPayment(razorpayResponse) {
        fetch('/payments/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + accessToken
            },
            body: JSON.stringify({
                razorpay_order_id: razorpayResponse.razorpay_order_id,
                razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                razorpay_signature: razorpayResponse.razorpay_signature
            })
        });
    }
    ```
    
    Args:
        verify_request: Payment verification request
        current_user: Authenticated user
        db: Database session
        
    Returns:
        PaymentVerifyResponse: Verification result
    """
    razorpay_service = RazorpayService(db)
    
    try:
        transaction = await razorpay_service.verify_payment(
            razorpay_order_id=verify_request.razorpay_order_id,
            razorpay_payment_id=verify_request.razorpay_payment_id,
            razorpay_signature=verify_request.razorpay_signature
        )
        
        return PaymentVerifyResponse(
            success=True,
            transaction_id=transaction.id,
            booking_id=transaction.booking_id,
            booking_type=transaction.booking_type,
            message="Payment verified successfully"
        )
        
    except HTTPException as e:
        return PaymentVerifyResponse(
            success=False,
            message=e.detail
        )


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Handle Razorpay webhook events.

    This endpoint receives webhook notifications from Razorpay
    for payment events (captured, failed, etc.) to ensure no
    payment is lost even if user closes browser.

    **Webhook Configuration in Razorpay Dashboard:**
    - URL: https://yourdomain.com/payments/webhook
    - Events: payment.captured, payment.failed, order.paid, refund.processed
    - Secret: Generate and store in RAZORPAY_WEBHOOK_SECRET env var

    **Events Handled:**
    - payment.captured: Update booking to CONFIRMED
    - payment.failed: Mark payment as FAILED
    - order.paid: Backup for payment.captured
    - refund.processed: Update refund status

    Args:
        request: FastAPI request with webhook payload
        x_razorpay_signature: Signature header for verification
        db: Database session

    Returns:
        dict: Status response
    """
    webhook_service = WebhookService(db)

    try:
        # CRITICAL SECURITY: Reject if signature header is missing
        if not x_razorpay_signature:
            logger.warning(f"Webhook rejected: Missing X-Razorpay-Signature header from {request.client.host if request.client else 'unknown'}")
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature header")

        # Get raw body for signature verification
        body = await request.body()
        payload_str = body.decode('utf-8')
        payload = json.loads(payload_str)

        # Verify webhook signature
        is_verified = webhook_service.verify_webhook_signature(
            payload_str,
            x_razorpay_signature
        )

        # CRITICAL SECURITY: Reject if signature verification fails
        if not is_verified:
            logger.warning(f"Webhook rejected: Signature verification failed from {request.client.host if request.client else 'unknown'} for event {payload.get('event', 'unknown')}")
            return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signature verification failed")

        # Get event type
        event_type = payload.get('event', '')

        # Process webhook only after successful verification
        webhook_log = await webhook_service.process_webhook(
            event_type=event_type,
            payload=payload,
            signature=x_razorpay_signature,
            is_verified=True
        )

        logger.info(f"Webhook processed successfully: {event_type}")

        return {
            "status": "ok",
            "event": event_type,
            "verified": True,
            "processed": webhook_log.is_processed
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
    refund_request: RefundCreateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Process refund for a payment transaction.
    
    This endpoint creates a refund via Razorpay API and updates
    the booking status. Only admins can process refunds.
    
    **Refund Types:**
    - Full refund: amount = None (refunds entire transaction amount)
    - Partial refund: amount = specific amount to refund
    
    **Process:**
    1. Verify transaction exists and payment was captured
    2. Call Razorpay refund API
    3. Update transaction status
    4. Update booking status to REFUNDED
    5. Generate credit note (if implemented)
    
    Args:
        refund_request: Refund request details
        current_admin: Authenticated admin user
        db: Database session
        
    Returns:
        RefundResponse: Refund details
    """
    razorpay_service = RazorpayService(db)
    
    refund = await razorpay_service.create_refund(
        transaction_id=refund_request.transaction_id,
        amount=refund_request.amount,
        reason=refund_request.reason,
        processed_by_id=current_admin.id
    )
    
    return RefundResponse(
        refund_id=refund.id,
        razorpay_refund_id=refund.razorpay_refund_id,
        amount=refund.amount,
        status=refund.status.value,
        message="Refund processed successfully"
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get payment transaction details.
    
    Users can only view their own transactions.
    
    Args:
        transaction_id: Transaction ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        TransactionResponse: Transaction details
    """
    from sqlalchemy import select, and_
    
    result = await db.execute(
        select(PaymentTransaction).where(
            and_(
                PaymentTransaction.id == transaction_id,
                PaymentTransaction.user_id == current_user.id
            )
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return TransactionResponse.model_validate(transaction)


@router.get("/transactions", response_model=List[TransactionResponse])
async def list_user_transactions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    List user's payment transactions.
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List[TransactionResponse]: List of transactions
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(PaymentTransaction)
        .where(PaymentTransaction.user_id == current_user.id)
        .order_by(PaymentTransaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    return [TransactionResponse.model_validate(t) for t in transactions]


# Admin endpoints for convenience fee management

@router.post("/admin/convenience-fees", response_model=ConvenienceFeeResponse)
async def create_convenience_fee(
    fee_data: ConvenienceFeeCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create convenience fee configuration.
    
    **Admin Only** - Configure fees for different payment methods.
    
    **Examples:**
    - Credit Card: 2% of amount (min ₹10, max ₹500)
    - UPI: ₹10 fixed
    - Net Banking: ₹15 fixed
    
    Args:
        fee_data: Fee configuration
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        ConvenienceFeeResponse: Created fee configuration
    """
    # Check if fee already exists
    from sqlalchemy import select
    
    result = await db.execute(
        select(ConvenienceFee).where(
            ConvenienceFee.payment_method == fee_data.payment_method
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Convenience fee already exists for {fee_data.payment_method}"
        )
    
    fee = ConvenienceFee(
        payment_method=fee_data.payment_method,
        fee_type=fee_data.fee_type,
        fee_value=fee_data.fee_value,
        min_fee=fee_data.min_fee,
        max_fee=fee_data.max_fee,
        description=fee_data.description
    )
    
    db.add(fee)
    await db.commit()
    await db.refresh(fee)
    
    return ConvenienceFeeResponse.model_validate(fee)


@router.get("/admin/convenience-fees", response_model=List[ConvenienceFeeResponse])
async def list_convenience_fees(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    List all convenience fee configurations.
    
    **Admin Only**
    
    Args:
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        List[ConvenienceFeeResponse]: List of fee configurations
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(ConvenienceFee).order_by(ConvenienceFee.payment_method)
    )
    fees = result.scalars().all()
    
    return [ConvenienceFeeResponse.model_validate(f) for f in fees]


@router.put("/admin/convenience-fees/{fee_id}", response_model=ConvenienceFeeResponse)
async def update_convenience_fee(
    fee_id: int,
    fee_data: ConvenienceFeeCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update convenience fee configuration.
    
    **Admin Only**
    
    Args:
        fee_id: Fee configuration ID
        fee_data: Updated fee configuration
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        ConvenienceFeeResponse: Updated fee configuration
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(ConvenienceFee).where(ConvenienceFee.id == fee_id)
    )
    fee = result.scalar_one_or_none()
    
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convenience fee not found"
        )
    
    fee.payment_method = fee_data.payment_method
    fee.fee_type = fee_data.fee_type
    fee.fee_value = fee_data.fee_value
    fee.min_fee = fee_data.min_fee
    fee.max_fee = fee_data.max_fee
    fee.description = fee_data.description
    
    await db.commit()
    await db.refresh(fee)
    
    return ConvenienceFeeResponse.model_validate(fee)


@router.delete("/admin/convenience-fees/{fee_id}")
async def delete_convenience_fee(
    fee_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete convenience fee configuration.
    
    **Admin Only**
    
    Args:
        fee_id: Fee configuration ID
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        dict: Status message
    """
    from sqlalchemy import select, delete
    
    result = await db.execute(
        select(ConvenienceFee).where(ConvenienceFee.id == fee_id)
    )
    fee = result.scalar_one_or_none()
    
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convenience fee not found"
        )
    
    await db.execute(
        delete(ConvenienceFee).where(ConvenienceFee.id == fee_id)
    )
    await db.commit()
    
    return {"status": "ok", "message": "Convenience fee deleted"}


@router.post("/calculate-fee", response_model=ConvenienceFeeCalculation)
async def calculate_convenience_fee(
    base_amount: float,
    payment_method: str,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Calculate convenience fee for a given amount and payment method.
    
    **Public endpoint** - Used by frontend to show fee breakdown
    before payment.
    
    Args:
        base_amount: Base booking amount
        payment_method: Payment method
        db: Database session
        
    Returns:
        ConvenienceFeeCalculation: Fee calculation details
    """
    razorpay_service = RazorpayService(db)
    
    convenience_fee = await razorpay_service._calculate_convenience_fee(
        base_amount, payment_method
    )
    
    taxes = convenience_fee * 0.18  # 18% GST
    total_amount = base_amount + convenience_fee + taxes
    
    return ConvenienceFeeCalculation(
        payment_method=payment_method,
        base_amount=base_amount,
        convenience_fee=convenience_fee,
        taxes=taxes,
        total_amount=total_amount
    )
