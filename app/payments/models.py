"""
Payment Database Models

This module defines database models for payment operations:
- Payment transactions with Razorpay integration
- Refund records and tracking
- Convenience fee configuration
- Webhook event logging
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base


class PaymentTransactionStatus(str, enum.Enum):
    """Payment transaction status enumeration."""
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"


class RefundStatus(str, enum.Enum):
    """Refund status enumeration."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class PaymentMethodType(str, enum.Enum):
    """Payment method types."""
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class FeeType(str, enum.Enum):
    """Convenience fee types."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class PaymentTransaction(Base):
    """
    Payment transaction model for Razorpay payments.
    
    This model stores all payment transaction details including
    Razorpay order ID, payment ID, and signature for verification.
    """
    __tablename__ = "payment_transactions"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Booking reference
    booking_id = Column(Integer, nullable=False, index=True)
    booking_type = Column(String(20), nullable=False)  # 'flight', 'hotel', 'bus'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Razorpay identifiers
    razorpay_order_id = Column(String(100), unique=True, index=True, nullable=False)
    razorpay_payment_id = Column(String(100), unique=True, index=True, nullable=True)
    razorpay_signature = Column(String(255), nullable=True)
    
    # Payment details
    amount = Column(Float, nullable=False)  # In INR
    currency = Column(String(3), default="INR", nullable=False)
    status = Column(Enum(PaymentTransactionStatus), default=PaymentTransactionStatus.CREATED, nullable=False)
    payment_method = Column(String(50), nullable=True)  # Populated after payment
    
    # Pricing breakdown
    base_amount = Column(Float, nullable=False)
    convenience_fee = Column(Float, default=0.0, nullable=False)
    taxes = Column(Float, default=0.0, nullable=False)
    
    # Gateway response
    gateway_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    refunds = relationship("Refund", back_populates="transaction")
    
    def __repr__(self):
        return f"<PaymentTransaction(id={self.id}, order_id={self.razorpay_order_id}, status={self.status})>"


class Refund(Base):
    """
    Refund model for tracking refund operations.
    
    This model stores refund details for cancelled bookings
    and payment reversals.
    """
    __tablename__ = "refunds"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("payment_transactions.id"), nullable=False, index=True)
    
    # Razorpay refund ID
    razorpay_refund_id = Column(String(100), unique=True, index=True, nullable=True)
    
    # Refund details
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    
    # Gateway response
    gateway_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Processing details
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transaction = relationship("PaymentTransaction", back_populates="refunds")
    processed_by = relationship("User", foreign_keys=[processed_by_id])
    
    def __repr__(self):
        return f"<Refund(id={self.id}, amount={self.amount}, status={self.status})>"


class WebhookLog(Base):
    """
    Webhook event log model.
    
    This model logs all webhook events received from Razorpay
    for debugging and audit purposes.
    """
    __tablename__ = "webhook_logs"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    razorpay_event_id = Column(String(100), unique=True, nullable=True)
    
    # Payload
    payload = Column(JSON, nullable=False)
    signature = Column(String(255), nullable=True)
    
    # Processing
    is_verified = Column(Boolean, default=False, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, event={self.event_type}, processed={self.is_processed})>"
