"""
Payment Processor for Bookings

This module provides integrated payment processing for all booking types,
supporting multiple payment methods:
- Wallet balance
- Razorpay (Credit/Debit cards, UPI, Net Banking)
- Wallet + Razorpay (split payment)
- Agent credit (for B2B agents)
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum

from app.wallet.services import (
    WalletService, WalletError, InsufficientBalanceError
)
from app.payments.services import RazorpayService, PaymentError
from app.payments.models import PaymentTransactionStatus as TxnPaymentStatus
from app.booking.models import PaymentStatus, PaymentMethod

logger = logging.getLogger(__name__)


class PaymentMode(str, Enum):
    """Payment mode options."""
    WALLET = "wallet"
    RAZORPAY = "razorpay"
    WALLET_RAZORPAY = "wallet_razorpay"  # Split payment
    AGENT_CREDIT = "agent_credit"


class PaymentProcessingError(Exception):
    """Exception for payment processing failures."""
    pass


class BookingPaymentProcessor:
    """
    Unified payment processor for all booking types.
    
    Handles:
    - Wallet payments (instant debit)
    - Razorpay payments (card, UPI, netbanking)
    - Split payments (wallet + razorpay)
    - Agent credit payments
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = WalletService(db)
        self.razorpay_service = RazorpayService(db)
    
    async def process_payment(
        self,
        user_id: int,
        amount: float,
        payment_mode: PaymentMode,
        booking_id: int,
        booking_type: str,
        razorpay_payment_id: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        razorpay_signature: Optional[str] = None,
        use_wallet_amount: Optional[float] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process payment for a booking.
        
        Args:
            user_id: User making the payment
            amount: Total amount to charge
            payment_mode: Payment method to use
            booking_id: Associated booking ID
            booking_type: Type of booking (flight/hotel/bus)
            razorpay_payment_id: Razorpay payment ID (for razorpay payments)
            razorpay_order_id: Razorpay order ID (for razorpay payments)
            razorpay_signature: Razorpay signature (for razorpay payments)
            use_wallet_amount: Amount to use from wallet (for split payments)
            description: Payment description
            
        Returns:
            Dict with payment result including status, transaction IDs
        """
        try:
            if payment_mode == PaymentMode.WALLET:
                return await self._process_wallet_payment(
                    user_id=user_id,
                    amount=amount,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    description=description
                )
            
            elif payment_mode == PaymentMode.RAZORPAY:
                return await self._process_razorpay_payment(
                    user_id=user_id,
                    amount=amount,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_order_id=razorpay_order_id,
                    razorpay_signature=razorpay_signature,
                    description=description
                )
            
            elif payment_mode == PaymentMode.WALLET_RAZORPAY:
                return await self._process_split_payment(
                    user_id=user_id,
                    total_amount=amount,
                    wallet_amount=use_wallet_amount or 0,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_order_id=razorpay_order_id,
                    razorpay_signature=razorpay_signature,
                    description=description
                )
            
            elif payment_mode == PaymentMode.AGENT_CREDIT:
                return await self._process_agent_credit_payment(
                    user_id=user_id,
                    amount=amount,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    description=description
                )
            
            else:
                raise PaymentProcessingError(f"Unsupported payment mode: {payment_mode}")
                
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            raise PaymentProcessingError(str(e))
    
    async def _process_wallet_payment(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process payment from wallet balance.
        
        Uses auto_commit=False so the caller (booking service) can commit
        both the wallet debit and the booking record atomically.
        """
        try:
            transaction = await self.wallet_service.debit(
                user_id=user_id,
                amount=amount,
                description=description or f"Payment for {booking_type} booking #{booking_id}",
                booking_id=booking_id,
                booking_type=booking_type,
                use_credit=False,  # Only use balance, not credit
                auto_commit=False  # Caller controls commit for atomicity
            )
            
            return {
                "status": PaymentStatus.SUCCESS,
                "payment_method": PaymentMethod.WALLET,
                "transaction_ref": transaction.transaction_ref,
                "wallet_transaction_id": transaction.id,
                "amount_paid": amount,
                "wallet_amount": amount,
                "razorpay_amount": 0,
                "message": "Payment successful via wallet",
                "processed_at": datetime.now(timezone.utc)
            }
            
        except InsufficientBalanceError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "error": str(e),
                "message": "Insufficient wallet balance",
                "processed_at": datetime.now(timezone.utc)
            }
        except WalletError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "error": str(e),
                "message": "Wallet payment failed",
                "processed_at": datetime.now(timezone.utc)
            }
    
    async def _process_razorpay_payment(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        razorpay_payment_id: str,
        razorpay_order_id: str,
        razorpay_signature: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process payment via Razorpay.
        
        Orders use payment_capture=1 (auto-capture), so no manual capture
        needed. We verify signature and update transaction record via
        verify_payment() which handles all DB state transitions.
        """
        try:
            # Verify payment signature (kwarg names: order_id, payment_id, signature)
            is_valid = self.razorpay_service.verify_payment_signature(
                order_id=razorpay_order_id,
                payment_id=razorpay_payment_id,
                signature=razorpay_signature
            )
            
            if not is_valid:
                return {
                    "status": PaymentStatus.FAILED,
                    "payment_method": PaymentMethod.CARD,  # Generic for razorpay
                    "error": "Invalid payment signature",
                    "message": "Payment verification failed",
                    "processed_at": datetime.now(timezone.utc)
                }
            
            # verify_payment() finds the PaymentTransaction by order_id,
            # verifies signature, fetches payment details from Razorpay,
            # updates transaction to CAPTURED, and updates booking status.
            # Auto-capture means payment is already captured by Razorpay.
            payment_txn = await self.razorpay_service.verify_payment(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature
            )
            
            return {
                "status": PaymentStatus.SUCCESS,
                "payment_method": PaymentMethod.CARD,
                "transaction_ref": payment_txn.razorpay_payment_id or razorpay_payment_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id": razorpay_order_id,
                "payment_transaction_id": payment_txn.id,
                "amount_paid": amount,
                "wallet_amount": 0,
                "razorpay_amount": amount,
                "message": "Payment successful via Razorpay",
                "processed_at": datetime.now(timezone.utc)
            }
            
        except PaymentError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.CARD,
                "error": str(e),
                "razorpay_payment_id": razorpay_payment_id,
                "message": "Razorpay payment failed",
                "processed_at": datetime.now(timezone.utc)
            }
    
    async def _process_split_payment(
        self,
        user_id: int,
        total_amount: float,
        wallet_amount: float,
        booking_id: int,
        booking_type: str,
        razorpay_payment_id: str,
        razorpay_order_id: str,
        razorpay_signature: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process split payment (wallet + razorpay) atomically.
        
        Uses hold-confirm pattern to prevent money loss on crash:
        1. Place hold on wallet (reserves funds, no debit yet)
        2. Verify Razorpay payment
        3. If Razorpay OK: convert hold to debit
        4. If Razorpay fails: release hold (funds returned)
        5. If server crashes: hold auto-expires via Redis TTL
        """
        razorpay_amount = total_amount - wallet_amount
        
        if wallet_amount <= 0:
            # No wallet component, process as pure razorpay
            return await self._process_razorpay_payment(
                user_id=user_id,
                amount=total_amount,
                booking_id=booking_id,
                booking_type=booking_type,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
                description=description
            )
        
        if razorpay_amount <= 0:
            # No razorpay component, process as pure wallet
            return await self._process_wallet_payment(
                user_id=user_id,
                amount=total_amount,
                booking_id=booking_id,
                booking_type=booking_type,
                description=description
            )
        
        # Step 1: Place hold on wallet (atomic reservation, no debit)
        hold_id = None
        try:
            hold_result = await self.wallet_service.place_hold(
                user_id=user_id,
                amount=wallet_amount,
                booking_id=booking_id,
                booking_type=booking_type,
                expiry_minutes=30
            )
            hold_id = hold_result["hold_id"]
        except InsufficientBalanceError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "error": str(e),
                "message": "Insufficient wallet balance for split payment",
                "processed_at": datetime.now(timezone.utc)
            }
        except WalletError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "error": str(e),
                "message": "Wallet hold failed",
                "processed_at": datetime.now(timezone.utc)
            }
        
        # Step 2: Verify Razorpay payment
        razorpay_result = await self._process_razorpay_payment(
            user_id=user_id,
            amount=razorpay_amount,
            booking_id=booking_id,
            booking_type=booking_type,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_signature=razorpay_signature,
            description=f"Partial payment for {booking_type} #{booking_id} (card portion)"
        )
        
        if razorpay_result["status"] != PaymentStatus.SUCCESS:
            # Step 2a: Razorpay failed -- release hold (no money lost)
            try:
                await self.wallet_service.release_hold(
                    hold_id=hold_id,
                    convert_to_debit=False
                )
            except Exception as release_err:
                logger.error(f"Failed to release hold {hold_id} after Razorpay failure: {release_err}")
            return razorpay_result
        
        # Step 3: Razorpay OK -- convert hold to actual debit
        try:
            wallet_txn = await self.wallet_service.release_hold(
                hold_id=hold_id,
                convert_to_debit=True,
                description=f"Partial payment for {booking_type} #{booking_id} (wallet portion)"
            )
        except Exception as debit_err:
            logger.error(f"Hold-to-debit failed for hold {hold_id}: {debit_err}")

            rollback_session = None
            for candidate_session in (
                getattr(self.wallet_service, "db", None),
                getattr(self.wallet_service, "session", None),
                getattr(self, "db", None),
                getattr(self, "session", None),
            ):
                if isinstance(candidate_session, AsyncSession):
                    rollback_session = candidate_session
                    break

            if rollback_session is not None:
                try:
                    await rollback_session.rollback()
                except Exception as rollback_err:
                    logger.error(
                        f"Failed to rollback session after hold-to-debit failure for hold {hold_id}: {rollback_err}"
                    )

            # Razorpay was captured but the wallet portion was not debited successfully.
            # Return a degraded result so callers do not treat the booking as fully paid.
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id": razorpay_order_id,
                "amount_paid": razorpay_amount,
                "wallet_amount": 0,
                "razorpay_amount": razorpay_amount,
                "message": "Razorpay captured but wallet debit failed. Manual reconciliation required.",
                "requires_manual_reconciliation": True,
                "processed_at": datetime.now(timezone.utc)
            }
        
        # Both successful
        return {
            "status": PaymentStatus.SUCCESS,
            "payment_method": PaymentMethod.WALLET,  # Combined
            "wallet_transaction_ref": wallet_txn.transaction_ref if wallet_txn else None,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "amount_paid": total_amount,
            "wallet_amount": wallet_amount,
            "razorpay_amount": razorpay_amount,
            "message": "Split payment successful",
            "processed_at": datetime.now(timezone.utc)
        }
    
    async def _process_agent_credit_payment(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process payment using agent credit limit.
        
        Uses auto_commit=False so the caller (booking service) can commit
        both the wallet debit and the booking record atomically.
        """
        try:
            # Debit from wallet using credit
            transaction = await self.wallet_service.debit(
                user_id=user_id,
                amount=amount,
                description=description or f"Credit payment for {booking_type} booking #{booking_id}",
                booking_id=booking_id,
                booking_type=booking_type,
                use_credit=True,  # Allow using credit limit
                auto_commit=False  # Caller controls commit for atomicity
            )
            
            return {
                "status": PaymentStatus.SUCCESS,
                "payment_method": PaymentMethod.AGENT_CREDIT,
                "transaction_ref": transaction.transaction_ref,
                "wallet_transaction_id": transaction.id,
                "amount_paid": amount,
                "wallet_amount": amount,  # Includes credit usage
                "razorpay_amount": 0,
                "message": "Payment successful via agent credit",
                "processed_at": datetime.now(timezone.utc)
            }
            
        except InsufficientBalanceError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.AGENT_CREDIT,
                "error": str(e),
                "message": "Insufficient credit limit",
                "processed_at": datetime.now(timezone.utc)
            }
        except WalletError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.AGENT_CREDIT,
                "error": str(e),
                "message": "Agent credit payment failed",
                "processed_at": datetime.now(timezone.utc)
            }
    
    async def create_payment_order(
        self,
        amount: float,
        booking_id: int,
        booking_type: str,
        user_id: int,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order for payment.
        
        Args:
            amount: Amount to charge
            booking_id: Associated booking ID
            booking_type: Type of booking
            user_id: User making the payment
            currency: Currency code
            
        Returns:
            Dict with Razorpay order details
        """
        # create_order is async -- must await. Correct signature:
        # create_order(booking_id, booking_type, user_id, base_amount, payment_method)
        transaction, order_details = await self.razorpay_service.create_order(
            booking_id=booking_id,
            booking_type=booking_type,
            user_id=user_id,
            base_amount=amount
        )
        
        return {
            "order_id": order_details["order_id"],
            "amount": order_details["total_amount"],
            "currency": order_details.get("currency", currency),
            "key_id": self.razorpay_service.key_id,
            "booking_id": booking_id,
            "booking_type": booking_type,
            "base_amount": order_details["base_amount"],
            "convenience_fee": order_details["convenience_fee"],
            "taxes": order_details["taxes"],
            "transaction_id": transaction.id
        }
    
    async def process_refund(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        original_payment_method: PaymentMethod,
        razorpay_payment_id: Optional[str] = None,
        reason: str = "Booking cancellation refund"
    ) -> Dict[str, Any]:
        """
        Process refund for a cancelled booking.
        
        For wallet payments: Credit back to wallet
        For Razorpay payments: Initiate Razorpay refund via create_refund()
        For agent credit: Credit back to wallet (reduces credit used)
        
        Args:
            user_id: User to refund
            amount: Refund amount
            booking_id: Booking ID
            booking_type: Type of booking
            original_payment_method: Original payment method used
            razorpay_payment_id: Razorpay payment ID (for razorpay refunds)
            reason: Refund reason
            
        Returns:
            Dict with refund result
        """
        try:
            if original_payment_method in [PaymentMethod.WALLET, PaymentMethod.AGENT_CREDIT]:
                # Credit refund to wallet
                transaction = await self.wallet_service.process_refund(
                    user_id=user_id,
                    amount=amount,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    reason=reason
                )
                
                return {
                    "status": "success",
                    "refund_method": "wallet",
                    "transaction_ref": transaction.transaction_ref,
                    "amount": amount,
                    "message": "Refund credited to wallet"
                }
            
            elif original_payment_method in [PaymentMethod.CARD, PaymentMethod.UPI, PaymentMethod.NET_BANKING]:
                if razorpay_payment_id:
                    # Process Razorpay refund via create_refund (correct method name)
                    # First, find the transaction by razorpay_payment_id
                    from sqlalchemy import select
                    from app.payments.models import PaymentTransaction
                    result = await self.db.execute(
                        select(PaymentTransaction).where(
                            PaymentTransaction.razorpay_payment_id == razorpay_payment_id
                        )
                    )
                    txn = result.scalar_one_or_none()
                    
                    if txn:
                        refund = await self.razorpay_service.create_refund(
                            transaction_id=txn.id,
                            amount=amount,
                            reason=reason
                        )
                        
                        return {
                            "status": "success" if refund.status.value == "processed" else "pending",
                            "refund_method": "razorpay",
                            "razorpay_refund_id": refund.razorpay_refund_id,
                            "amount": amount,
                            "message": "Refund initiated via Razorpay"
                        }
                
                # Fallback to wallet refund if no razorpay details or transaction
                transaction = await self.wallet_service.process_refund(
                    user_id=user_id,
                    amount=amount,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    reason=f"{reason} (credited to wallet as fallback)"
                )
                
                return {
                    "status": "success",
                    "refund_method": "wallet",
                    "transaction_ref": transaction.transaction_ref,
                    "amount": amount,
                    "message": "Refund credited to wallet (original payment method unavailable)"
                }
            
            else:
                # Default to wallet refund
                transaction = await self.wallet_service.process_refund(
                    user_id=user_id,
                    amount=amount,
                    booking_id=booking_id,
                    booking_type=booking_type,
                    reason=reason
                )
                
                return {
                    "status": "success",
                    "refund_method": "wallet",
                    "transaction_ref": transaction.transaction_ref,
                    "amount": amount,
                    "message": "Refund credited to wallet"
                }
                
        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Refund processing failed"
            }
    
    async def check_payment_eligibility(
        self,
        user_id: int,
        amount: float,
        payment_mode: PaymentMode
    ) -> Dict[str, Any]:
        """
        Check if user is eligible for the requested payment mode.
        
        Args:
            user_id: User ID
            amount: Payment amount
            payment_mode: Requested payment mode
            
        Returns:
            Dict with eligibility status and details
        """
        try:
            balance = await self.wallet_service.get_balance(user_id)
            
            if payment_mode == PaymentMode.WALLET:
                is_eligible = balance["available_balance"] >= amount
                return {
                    "eligible": is_eligible,
                    "available_balance": balance["available_balance"],
                    "required_amount": amount,
                    "shortfall": max(0, amount - balance["available_balance"]),
                    "message": "Sufficient balance" if is_eligible else "Insufficient wallet balance"
                }
            
            elif payment_mode == PaymentMode.AGENT_CREDIT:
                total_available = balance["available_balance"] + balance["available_credit"]
                is_eligible = total_available >= amount
                return {
                    "eligible": is_eligible,
                    "available_balance": balance["available_balance"],
                    "available_credit": balance["available_credit"],
                    "total_available": total_available,
                    "required_amount": amount,
                    "shortfall": max(0, amount - total_available),
                    "message": "Sufficient credit" if is_eligible else "Insufficient credit limit"
                }
            
            elif payment_mode == PaymentMode.RAZORPAY:
                return {
                    "eligible": True,
                    "required_amount": amount,
                    "message": "Razorpay payment available"
                }
            
            elif payment_mode == PaymentMode.WALLET_RAZORPAY:
                wallet_available = balance["available_balance"]
                razorpay_needed = max(0, amount - wallet_available)
                return {
                    "eligible": True,
                    "available_balance": wallet_available,
                    "wallet_contribution": min(wallet_available, amount),
                    "razorpay_contribution": razorpay_needed,
                    "required_amount": amount,
                    "message": "Split payment available"
                }
            
            return {"eligible": False, "message": "Unknown payment mode"}
            
        except Exception as e:
            return {
                "eligible": False,
                "error": str(e),
                "message": "Error checking payment eligibility"
            }
