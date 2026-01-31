"""
Payment Pydantic Schemas

This module defines Pydantic schemas for request/response validation:
- Order creation requests and responses
- Payment verification schemas
- Refund request schemas
- Convenience fee schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PaymentMethodEnum(str, Enum):
    """Payment method enumeration for convenience fee calculation."""
    CARD = "card"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class OrderCreateRequest(BaseModel):
    """Schema for creating a Razorpay order."""
    booking_id: int = Field(..., description="Booking ID")
    booking_type: str = Field(..., description="Booking type (flight/hotel/bus)")
    base_amount: float = Field(..., gt=0, description="Base booking amount")
    payment_method: Optional[PaymentMethodEnum] = Field(None, description="Payment method for fee calculation")


class OrderCreateResponse(BaseModel):
    """Schema for order creation response."""
    order_id: str = Field(..., description="Razorpay order ID")
    amount: int = Field(..., description="Total amount in paise")
    currency: str = Field(..., description="Currency code")
    key_id: str = Field(..., description="Razorpay key ID for checkout")
    base_amount: float = Field(..., description="Base amount in INR")
    convenience_fee: float = Field(..., description="Convenience fee in INR")
    taxes: float = Field(..., description="Taxes in INR")
    total_amount: float = Field(..., description="Total amount in INR")


class PaymentVerifyRequest(BaseModel):
    """Schema for payment verification."""
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID")
    razorpay_signature: str = Field(..., description="Razorpay signature for verification")


class PaymentVerifyResponse(BaseModel):
    """Schema for payment verification response."""
    success: bool = Field(..., description="Whether payment was verified")
    transaction_id: Optional[int] = Field(None, description="Internal transaction ID")
    booking_id: Optional[int] = Field(None, description="Booking ID")
    booking_type: Optional[str] = Field(None, description="Booking type")
    message: str = Field(..., description="Status message")


class RefundCreateRequest(BaseModel):
    """Schema for refund creation."""
    transaction_id: int = Field(..., description="Payment transaction ID")
    amount: Optional[float] = Field(None, description="Refund amount (None = full refund)")
    reason: Optional[str] = Field(None, description="Reason for refund")


class RefundResponse(BaseModel):
    """Schema for refund response."""
    refund_id: int = Field(..., description="Internal refund ID")
    razorpay_refund_id: Optional[str] = Field(None, description="Razorpay refund ID")
    amount: float = Field(..., description="Refunded amount")
    status: str = Field(..., description="Refund status")
    message: str = Field(..., description="Status message")


class ConvenienceFeeCreate(BaseModel):
    """Schema for creating convenience fee configuration."""
    payment_method: str = Field(..., description="Payment method")
    fee_type: str = Field(..., description="Fee type: fixed or percentage")
    fee_value: float = Field(..., gt=0, description="Fee value")
    min_fee: float = Field(0.0, ge=0, description="Minimum fee amount")
    max_fee: Optional[float] = Field(None, description="Maximum fee amount")
    description: Optional[str] = Field(None, description="Fee description")


class ConvenienceFeeResponse(BaseModel):
    """Schema for convenience fee response."""
    id: int
    payment_method: str
    fee_type: str
    fee_value: float
    min_fee: float
    max_fee: Optional[float]
    is_active: bool
    description: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConvenienceFeeCalculation(BaseModel):
    """Schema for convenience fee calculation result."""
    payment_method: str = Field(..., description="Payment method")
    base_amount: float = Field(..., description="Base amount")
    convenience_fee: float = Field(..., description="Calculated convenience fee")
    taxes: float = Field(..., description="GST on convenience fee")
    total_amount: float = Field(..., description="Total amount including fees")


class TransactionResponse(BaseModel):
    """Schema for transaction details response."""
    id: int
    booking_id: int
    booking_type: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str]
    amount: float
    currency: str
    status: str
    payment_method: Optional[str]
    base_amount: float
    convenience_fee: float
    taxes: float
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WebhookEvent(BaseModel):
    """Schema for webhook event payload."""
    event: str = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    created_at: int = Field(..., description="Event timestamp")
