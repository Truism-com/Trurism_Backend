"""
Payment Services

This module contains business logic for payment operations:
- Razorpay order creation and verification
- Payment signature verification
- Webhook handling and processing
- Refund processing
- Convenience fee calculation
"""

import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.payments.models import (
    PaymentTransaction, Refund, WebhookLog,
    PaymentTransactionStatus, RefundStatus, FeeType
)
from app.settings.models import ConvenienceFee
from app.booking.models import FlightBooking, HotelBooking, BusBooking, BookingStatus, PaymentStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Base exception for payment-related errors."""
    
    def __init__(self, message: str, code: str = "PAYMENT_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class RazorpayService:
    """
    Razorpay payment service for payment processing.
    
    This service handles all Razorpay API interactions including
    order creation, payment verification, and refund processing.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Razorpay client."""
        if self._client is None:
            try:
                import razorpay
                self._client = razorpay.Client(
                    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
                )
            except ImportError:
                raise ImportError(
                    "Razorpay package not installed. Run: pip install razorpay"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Razorpay client: {e}")
                raise
        return self._client
    
    @property
    def key_id(self) -> str:
        """Get Razorpay key ID for client-side use."""
        return settings.razorpay_key_id
    
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Public method to verify Razorpay payment signature.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Signature to verify
            
        Returns:
            bool: True if signature is valid
        """
        return self._verify_payment_signature(order_id, payment_id, signature)
    
    def create_simple_order(
        self,
        amount: float,
        currency: str = "INR",
        notes: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a simple Razorpay order without booking association.
        
        Used for wallet top-ups and other non-booking payments.
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            currency: Currency code (default: INR)
            notes: Optional notes dictionary
            
        Returns:
            Dict with order details
        """
        try:
            amount_in_paise = int(amount * 100)
            
            order_data = {
                'amount': amount_in_paise,
                'currency': currency,
                'receipt': f'wallet_topup_{datetime.utcnow().timestamp()}',
                'payment_capture': 1,
                'notes': notes or {}
            }
            
            razorpay_order = self.client.order.create(data=order_data)
            
            logger.info(f"Created simple Razorpay order: {razorpay_order['id']}")
            
            return razorpay_order
            
        except Exception as e:
            logger.error(f"Simple order creation failed: {e}")
            raise
    
    async def create_order(
        self,
        booking_id: int,
        booking_type: str,
        user_id: int,
        base_amount: float,
        payment_method: Optional[str] = None
    ) -> Tuple[PaymentTransaction, Dict[str, Any]]:
        """
        Create Razorpay order for payment.
        
        Args:
            booking_id: Booking ID
            booking_type: Type of booking (flight/hotel/bus)
            user_id: User making the payment
            base_amount: Base booking amount
            payment_method: Payment method for fee calculation
            
        Returns:
            Tuple[PaymentTransaction, Dict]: Transaction record and order details
            
        Raises:
            HTTPException: If order creation fails
        """
        try:
            # Calculate convenience fee
            convenience_fee = await self._calculate_convenience_fee(base_amount, payment_method)
            
            # Calculate GST on convenience fee (18%)
            taxes = convenience_fee * 0.18
            
            # Total amount
            total_amount = base_amount + convenience_fee + taxes
            
            # Convert to paise (Razorpay requires amount in smallest currency unit)
            amount_in_paise = int(total_amount * 100)
            
            # Create order data
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'{booking_type}_{booking_id}_{datetime.utcnow().timestamp()}',
                'payment_capture': 1,  # Auto capture payment
                'notes': {
                    'booking_id': str(booking_id),
                    'booking_type': booking_type,
                    'user_id': str(user_id)
                }
            }
            
            # Create order via Razorpay API
            razorpay_order = self.client.order.create(data=order_data)
            
            # Create transaction record
            transaction = PaymentTransaction(
                booking_id=booking_id,
                booking_type=booking_type,
                user_id=user_id,
                razorpay_order_id=razorpay_order['id'],
                amount=total_amount,
                currency='INR',
                status=PaymentTransactionStatus.CREATED,
                base_amount=base_amount,
                convenience_fee=convenience_fee,
                taxes=taxes,
                gateway_response=razorpay_order
            )
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            
            logger.info(f"Created Razorpay order: {razorpay_order['id']} for booking {booking_id}")
            
            return transaction, {
                'order_id': razorpay_order['id'],
                'amount': amount_in_paise,
                'currency': 'INR',
                'key_id': settings.razorpay_key_id,
                'base_amount': base_amount,
                'convenience_fee': convenience_fee,
                'taxes': taxes,
                'total_amount': total_amount
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Order creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment order creation failed: {str(e)}"
            )
    
    async def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> PaymentTransaction:
        """
        Verify Razorpay payment signature and update transaction.
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Signature to verify
            
        Returns:
            PaymentTransaction: Updated transaction record
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            # Get transaction
            result = await self.db.execute(
                select(PaymentTransaction).where(
                    PaymentTransaction.razorpay_order_id == razorpay_order_id
                )
            )
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found"
                )
            
            # Verify signature
            is_valid = self._verify_payment_signature(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            )
            
            if not is_valid:
                transaction.status = PaymentTransactionStatus.FAILED
                transaction.error_message = "Invalid payment signature"
                await self.db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment verification failed: Invalid signature"
                )
            
            # Fetch payment details from Razorpay
            try:
                payment_details = self.client.payment.fetch(razorpay_payment_id)
                transaction.payment_method = payment_details.get('method', '')
                transaction.gateway_response = payment_details
            except Exception as e:
                logger.warning(f"Failed to fetch payment details: {e}")
            
            # Update transaction
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature
            transaction.status = PaymentTransactionStatus.CAPTURED
            transaction.is_verified = True
            transaction.verified_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Update booking status
            await self._update_booking_status(transaction)
            
            logger.info(f"Payment verified successfully: {razorpay_payment_id}")
            
            try:
                from app.auth.models import User as UserModel
                from sqlalchemy import select as sa_select
                user_result = await self.db.execute(
                    sa_select(UserModel).where(UserModel.id == transaction.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    from app.services.email import email_service
                    await email_service.send_payment_success(
                        to_email=user.email,
                        transaction_id=razorpay_payment_id,
                        amount=transaction.amount,
                        payment_method=transaction.payment_method or "Razorpay",
                        booking_reference=str(transaction.booking_id),
                    )
                    logger.info(f"Payment success email sent to {user.email} for transaction {razorpay_payment_id}")
            except Exception as email_err:
                logger.warning(f"Payment success email failed: {email_err}")
            
            return transaction
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Payment verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment verification failed: {str(e)}"
            )
    
    def _verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature using HMAC SHA256.
        
        Args:
            order_id: Razorpay order ID
            payment_id: Razorpay payment ID
            signature: Signature to verify
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Create message: order_id + "|" + payment_id
            message = f"{order_id}|{payment_id}"
            
            # Generate signature
            generated_signature = hmac.HMAC(
                settings.razorpay_key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(generated_signature, signature)
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def create_refund(
        self,
        transaction_id: int,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
        processed_by_id: Optional[int] = None
    ) -> Refund:
        """
        Create refund for a payment transaction.
        
        Args:
            transaction_id: Payment transaction ID
            amount: Refund amount (None = full refund)
            reason: Refund reason
            processed_by_id: Admin user ID processing refund
            
        Returns:
            Refund: Created refund record
            
        Raises:
            HTTPException: If refund creation fails
        """
        try:
            # Get transaction
            result = await self.db.execute(
                select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found"
                )
            
            if not transaction.razorpay_payment_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot refund: Payment not completed"
                )
            
            # Determine refund amount
            refund_amount = amount if amount else transaction.amount
            
            if refund_amount > transaction.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refund amount exceeds transaction amount"
                )
            
            # Create refund via Razorpay API
            refund_data = {
                'amount': int(refund_amount * 100),  # Convert to paise
            }
            if reason:
                refund_data['notes'] = {'reason': reason}
            
            razorpay_refund = self.client.payment.refund(
                transaction.razorpay_payment_id,
                refund_data
            )
            
            # Create refund record
            refund = Refund(
                transaction_id=transaction_id,
                razorpay_refund_id=razorpay_refund['id'],
                amount=refund_amount,
                reason=reason,
                status=RefundStatus.PROCESSED,
                gateway_response=razorpay_refund,
                processed_by_id=processed_by_id,
                processed_at=datetime.utcnow()
            )
            
            self.db.add(refund)
            
            # Update transaction status
            if refund_amount == transaction.amount:
                transaction.status = PaymentTransactionStatus.REFUNDED
            else:
                transaction.status = PaymentTransactionStatus.PARTIAL_REFUND
            
            await self.db.commit()
            await self.db.refresh(refund)
            
            # Update booking status
            await self._update_booking_refund_status(transaction, refund_amount)
            
            logger.info(f"Refund created: {razorpay_refund['id']} for amount {refund_amount}")
            
            return refund
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Refund creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Refund processing failed: {str(e)}"
            )
    
    async def _calculate_convenience_fee(
        self,
        base_amount: float,
        payment_method: Optional[str] = None
    ) -> float:
        """
        Calculate convenience fee based on payment method and amount.
        
        Args:
            base_amount: Base booking amount
            payment_method: Payment method
            
        Returns:
            float: Calculated convenience fee
        """
        if not payment_method:
            # Default fee if method not specified (e.g., 2% or ₹10, whichever is higher)
            return max(base_amount * 0.02, 10.0)
        
        # Get fee configuration
        result = await self.db.execute(
            select(ConvenienceFee).where(
                and_(
                    ConvenienceFee.payment_method == payment_method,
                    ConvenienceFee.is_active == True
                )
            )
        )
        fee_config = result.scalar_one_or_none()
        
        if not fee_config:
            # Default fee
            return max(base_amount * 0.02, 10.0)
        
        # Calculate fee
        if fee_config.fee_type == FeeType.FIXED:
            fee = fee_config.fee_value
        else:  # PERCENTAGE
            fee = base_amount * (fee_config.fee_value / 100)
        
        # Apply min/max limits
        if fee < fee_config.min_fee:
            fee = fee_config.min_fee
        if fee_config.max_fee and fee > fee_config.max_fee:
            fee = fee_config.max_fee
        
        return round(fee, 2)
    
    async def _update_booking_status(self, transaction: PaymentTransaction):
        """Update booking status after successful payment."""
        try:
            booking_model = {
                'flight': FlightBooking,
                'hotel': HotelBooking,
                'bus': BusBooking
            }.get(transaction.booking_type)
            
            if not booking_model:
                logger.warning(f"Unknown booking type: {transaction.booking_type}")
                return
            
            result = await self.db.execute(
                select(booking_model).where(booking_model.id == transaction.booking_id)
            )
            booking = result.scalar_one_or_none()
            
            if booking:
                booking.payment_status = PaymentStatus.SUCCESS
                booking.status = BookingStatus.CONFIRMED
                booking.confirmation_number = f"{transaction.booking_type.upper()[:2]}{booking.id:06d}"
                await self.db.commit()
                logger.info(f"Updated booking {transaction.booking_id} to CONFIRMED")
                
        except Exception as e:
            logger.error(f"Failed to update booking status: {e}")
    
    async def _update_booking_refund_status(self, transaction: PaymentTransaction, refund_amount: float):
        """Update booking status after refund."""
        try:
            booking_model = {
                'flight': FlightBooking,
                'hotel': HotelBooking,
                'bus': BusBooking
            }.get(transaction.booking_type)
            
            if not booking_model:
                return
            
            result = await self.db.execute(
                select(booking_model).where(booking_model.id == transaction.booking_id)
            )
            booking = result.scalar_one_or_none()
            
            if booking:
                booking.payment_status = PaymentStatus.REFUNDED
                booking.status = BookingStatus.REFUNDED
                booking.refund_amount = refund_amount
                await self.db.commit()
                logger.info(f"Updated booking {transaction.booking_id} to REFUNDED")
                
        except Exception as e:
            logger.error(f"Failed to update booking refund status: {e}")


class WebhookService:
    """
    Webhook service for handling Razorpay webhook events.
    
    This service processes incoming webhook events for payment
    status updates and ensures no payment events are lost.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.razorpay_service = RazorpayService(db)
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature using HMAC SHA256.
        
        Args:
            payload: Webhook payload (raw string)
            signature: Signature from X-Razorpay-Signature header
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if not settings.razorpay_webhook_secret:
                logger.error("RAZORPAY_WEBHOOK_SECRET is not configured")
                return False
            
            expected_signature = hmac.HMAC(
                settings.razorpay_webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False
    
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        signature: str,
        is_verified: bool
    ) -> WebhookLog:
        """
        Process webhook event and log it.
        
        Args:
            event_type: Event type (e.g., payment.captured)
            payload: Event payload
            signature: Webhook signature
            is_verified: Whether signature was verified
            
        Returns:
            WebhookLog: Created webhook log entry
        """
        # Create webhook log
        webhook_log = WebhookLog(
            event_type=event_type,
            razorpay_event_id=payload.get('event', {}).get('id'),
            payload=payload,
            signature=signature,
            is_verified=is_verified
        )
        
        self.db.add(webhook_log)
        
        if not is_verified:
            webhook_log.error_message = "Signature verification failed"
            await self.db.commit()
            return webhook_log
        
        try:
            # Process event based on type
            if event_type == 'payment.captured':
                await self._handle_payment_captured(payload)
            elif event_type == 'payment.failed':
                await self._handle_payment_failed(payload)
            elif event_type == 'order.paid':
                await self._handle_order_paid(payload)
            elif event_type == 'refund.processed':
                await self._handle_refund_processed(payload)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
            
            webhook_log.is_processed = True
            webhook_log.processed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            webhook_log.error_message = str(e)
        
        await self.db.commit()
        return webhook_log
    
    async def _handle_payment_captured(self, payload: Dict[str, Any]):
        """Handle payment.captured event."""
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        if not order_id or not payment_id:
            logger.warning("Missing order_id or payment_id in webhook payload")
            return
        
        # Get transaction
        result = await self.db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.razorpay_order_id == order_id
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            logger.warning(f"Transaction not found for order: {order_id}")
            return
        
        # Update transaction if not already verified
        if not transaction.is_verified:
            transaction.razorpay_payment_id = payment_id
            transaction.status = PaymentTransactionStatus.CAPTURED
            transaction.payment_method = payment_entity.get('method', '')
            transaction.is_verified = True
            transaction.verified_at = datetime.utcnow()
            transaction.gateway_response = payment_entity
            
            await self.razorpay_service._update_booking_status(transaction)
            
            logger.info(f"Payment captured via webhook: {payment_id}")
    
    async def _handle_payment_failed(self, payload: Dict[str, Any]):
        """Handle payment.failed event."""
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        
        if not order_id:
            return
        
        result = await self.db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.razorpay_order_id == order_id
            )
        )
        transaction = result.scalar_one_or_none()
        
        if transaction:
            transaction.status = PaymentTransactionStatus.FAILED
            transaction.error_message = payment_entity.get('error_description', 'Payment failed')
            logger.info(f"Payment failed via webhook: {order_id}")
    
    async def _handle_order_paid(self, payload: Dict[str, Any]):
        """Handle order.paid event (backup for payment.captured)."""
        await self._handle_payment_captured(payload)
    
    async def _handle_refund_processed(self, payload: Dict[str, Any]):
        """Handle refund.processed event."""
        refund_entity = payload.get('payload', {}).get('refund', {}).get('entity', {})
        refund_id = refund_entity.get('id')
        
        if refund_id:
            result = await self.db.execute(
                select(Refund).where(Refund.razorpay_refund_id == refund_id)
            )
            refund = result.scalar_one_or_none()
            
            if refund:
                refund.status = RefundStatus.PROCESSED
                refund.gateway_response = refund_entity
                logger.info(f"Refund processed via webhook: {refund_id}")
