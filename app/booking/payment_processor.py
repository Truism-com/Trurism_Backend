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
from datetime import datetime
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
        """Process payment from wallet balance."""
        try:
            transaction = await self.wallet_service.debit(
                user_id=user_id,
                amount=amount,
                description=description or f"Payment for {booking_type} booking #{booking_id}",
                booking_id=booking_id,
                booking_type=booking_type,
                use_credit=False  # Only use balance, not credit
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
                "processed_at": datetime.utcnow()
            }
            
        except InsufficientBalanceError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "error": str(e),
                "message": "Insufficient wallet balance",
                "processed_at": datetime.utcnow()
            }
        except WalletError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.WALLET,
                "error": str(e),
                "message": "Wallet payment failed",
                "processed_at": datetime.utcnow()
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
        """Process payment via Razorpay."""
        try:
            # Verify payment signature
            is_valid = self.razorpay_service.verify_payment_signature(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature
            )
            
            if not is_valid:
                return {
                    "status": PaymentStatus.FAILED,
                    "payment_method": PaymentMethod.CARD,  # Generic for razorpay
                    "error": "Invalid payment signature",
                    "message": "Payment verification failed",
                    "processed_at": datetime.utcnow()
                }
            
            # Capture the payment
            payment_details = self.razorpay_service.capture_payment(
                payment_id=razorpay_payment_id,
                amount=amount
            )
            
            # Record the transaction
            payment_txn = await self.razorpay_service.record_payment_success(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature
            )
            
            return {
                "status": PaymentStatus.SUCCESS,
                "payment_method": PaymentMethod.CARD,
                "transaction_ref": payment_txn.transaction_ref if payment_txn else razorpay_payment_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id": razorpay_order_id,
                "payment_transaction_id": payment_txn.id if payment_txn else None,
                "amount_paid": amount,
                "wallet_amount": 0,
                "razorpay_amount": amount,
                "message": "Payment successful via Razorpay",
                "processed_at": datetime.utcnow()
            }
            
        except PaymentError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.CARD,
                "error": str(e),
                "razorpay_payment_id": razorpay_payment_id,
                "message": "Razorpay payment failed",
                "processed_at": datetime.utcnow()
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
        """Process split payment (wallet + razorpay)."""
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
        
        # Process wallet portion first
        wallet_result = await self._process_wallet_payment(
            user_id=user_id,
            amount=wallet_amount,
            booking_id=booking_id,
            booking_type=booking_type,
            description=f"Partial payment for {booking_type} #{booking_id} (wallet portion)"
        )
        
        if wallet_result["status"] != PaymentStatus.SUCCESS:
            return wallet_result
        
        # Then process razorpay portion
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
            # Refund wallet portion
            await self.wallet_service.process_refund(
                user_id=user_id,
                amount=wallet_amount,
                booking_id=booking_id,
                booking_type=booking_type,
                reason="Razorpay payment failed, reversing wallet debit"
            )
            return razorpay_result
        
        # Both successful
        return {
            "status": PaymentStatus.SUCCESS,
            "payment_method": PaymentMethod.WALLET,  # Combined
            "wallet_transaction_ref": wallet_result.get("transaction_ref"),
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "amount_paid": total_amount,
            "wallet_amount": wallet_amount,
            "razorpay_amount": razorpay_amount,
            "message": "Split payment successful",
            "processed_at": datetime.utcnow()
        }
    
    async def _process_agent_credit_payment(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process payment using agent credit limit."""
        try:
            # Debit from wallet using credit
            transaction = await self.wallet_service.debit(
                user_id=user_id,
                amount=amount,
                description=description or f"Credit payment for {booking_type} booking #{booking_id}",
                booking_id=booking_id,
                booking_type=booking_type,
                use_credit=True  # Allow using credit limit
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
                "processed_at": datetime.utcnow()
            }
            
        except InsufficientBalanceError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.AGENT_CREDIT,
                "error": str(e),
                "message": "Insufficient credit limit",
                "processed_at": datetime.utcnow()
            }
        except WalletError as e:
            return {
                "status": PaymentStatus.FAILED,
                "payment_method": PaymentMethod.AGENT_CREDIT,
                "error": str(e),
                "message": "Agent credit payment failed",
                "processed_at": datetime.utcnow()
            }
    
    async def create_payment_order(
        self,
        amount: float,
        booking_id: int,
        booking_type: str,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order for payment.
        
        Args:
            amount: Amount to charge
            booking_id: Associated booking ID
            booking_type: Type of booking
            currency: Currency code
            
        Returns:
            Dict with Razorpay order details
        """
        notes = {
            "booking_id": str(booking_id),
            "booking_type": booking_type,
            "purpose": "booking_payment"
        }
        
        order = self.razorpay_service.create_order(
            amount=amount,
            currency=currency,
            notes=notes
        )
        
        return {
            "order_id": order["id"],
            "amount": order["amount"] / 100,  # Convert from paise
            "currency": order["currency"],
            "key_id": self.razorpay_service.key_id,
            "booking_id": booking_id,
            "booking_type": booking_type
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
        For Razorpay payments: Initiate Razorpay refund
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
                    # Process Razorpay refund
                    refund = await self.razorpay_service.process_refund(
                        payment_id=razorpay_payment_id,
                        amount=amount,
                        reason=reason
                    )
                    
                    return {
                        "status": "success" if refund.get("status") == "processed" else "pending",
                        "refund_method": "razorpay",
                        "razorpay_refund_id": refund.get("id"),
                        "amount": amount,
                        "message": "Refund initiated via Razorpay"
                    }
                else:
                    # Fallback to wallet refund if no razorpay details
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
