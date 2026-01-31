"""
Wallet Pydantic Schemas

Request and response schemas for wallet operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Import enums from models to avoid duplication
from app.wallet.models import (
    WalletStatus,
    TransactionType,
    TransactionStatus,
    TopupStatus
)

# Re-export for convenience
__all__ = [
    "WalletStatus",
    "TransactionType",
    "TransactionStatus",
    "TopupStatus",
]


# =============================================================================
# Wallet Schemas
# =============================================================================

class WalletBase(BaseModel):
    """Base wallet schema."""
    currency: str = Field(default="INR", max_length=3)


class WalletCreate(WalletBase):
    """Schema for creating a new wallet."""
    user_id: int


class WalletUpdate(BaseModel):
    """Schema for updating wallet settings."""
    daily_transaction_limit: Optional[float] = Field(None, ge=0)
    min_balance: Optional[float] = Field(None, ge=0)


class WalletBalance(BaseModel):
    """Schema for wallet balance response."""
    balance: float = Field(..., description="Current wallet balance")
    hold_amount: float = Field(..., description="Amount on hold for pending transactions")
    available_balance: float = Field(..., description="Available balance (balance - hold)")
    credit_limit: float = Field(..., description="Credit limit for agents")
    credit_used: float = Field(..., description="Credit currently used")
    available_credit: float = Field(..., description="Available credit")
    total_available: float = Field(..., description="Total available (balance + credit)")
    currency: str = Field(..., description="Currency code")
    status: WalletStatus


class WalletResponse(BaseModel):
    """Full wallet response schema."""
    id: int
    user_id: int
    balance: float
    hold_amount: float
    currency: str
    credit_limit: float
    credit_used: float
    status: WalletStatus
    daily_transaction_limit: float
    min_balance: float
    total_credited: float
    total_debited: float
    last_transaction_at: Optional[datetime]
    created_at: datetime
    
    # Computed properties
    available_balance: float
    available_credit: float
    total_available: float
    
    class Config:
        from_attributes = True


class WalletSummary(BaseModel):
    """Wallet summary for dashboard."""
    balance: float
    available_balance: float
    currency: str
    status: WalletStatus
    pending_transactions: int = 0
    today_transactions: float = 0.0
    
    class Config:
        from_attributes = True


# =============================================================================
# Transaction Schemas
# =============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema."""
    amount: float = Field(..., gt=0, description="Transaction amount")
    description: Optional[str] = Field(None, max_length=500)


class CreditRequest(TransactionBase):
    """Schema for crediting wallet."""
    reason: Optional[str] = Field(None, max_length=200)


class DebitRequest(TransactionBase):
    """Schema for debiting wallet."""
    booking_id: Optional[int] = None
    booking_type: Optional[str] = Field(None, pattern="^(flight|hotel|bus)$")


class TransferRequest(BaseModel):
    """Schema for transferring between wallets."""
    to_user_id: int = Field(..., description="User ID to transfer to")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    description: Optional[str] = Field(None, max_length=500)


class RefundRequest(BaseModel):
    """Schema for processing refund to wallet."""
    booking_id: int
    booking_type: str = Field(..., pattern="^(flight|hotel|bus)$")
    amount: float = Field(..., gt=0)
    reason: str = Field(..., max_length=500)


class AdjustmentRequest(BaseModel):
    """Schema for admin manual adjustment."""
    user_id: int
    amount: float = Field(..., description="Positive for credit, negative for debit")
    reason: str = Field(..., min_length=10, max_length=500)


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: int
    transaction_ref: str
    type: TransactionType
    amount: float
    balance_before: float
    balance_after: float
    status: TransactionStatus
    booking_id: Optional[int]
    booking_type: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionFilter(BaseModel):
    """Filter options for transaction history."""
    type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


# =============================================================================
# Top-up Schemas
# =============================================================================

class TopupRequest(BaseModel):
    """Schema for creating a top-up request."""
    amount: float = Field(..., gt=0, description="Amount to top up")
    payment_method: str = Field(..., description="Payment method: online/bank_transfer")
    
    # For bank transfer
    bank_reference: Optional[str] = None
    bank_name: Optional[str] = None
    transfer_date: Optional[datetime] = None
    proof_document_url: Optional[str] = None


class TopupOnlineRequest(BaseModel):
    """Schema for online top-up via Razorpay."""
    amount: float = Field(..., gt=0, ge=100, description="Amount to top up (min INR 100)")


class TopupVerifyRequest(BaseModel):
    """Schema for verifying online top-up payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class TopupApprovalRequest(BaseModel):
    """Schema for admin approval of top-up request."""
    approved: bool
    rejection_reason: Optional[str] = None
    
    @field_validator('rejection_reason')
    @classmethod
    def validate_rejection_reason(cls, v, info):
        if not info.data.get('approved') and not v:
            raise ValueError('Rejection reason is required when rejecting')
        return v


class TopupResponse(BaseModel):
    """Top-up request response schema."""
    id: int
    request_ref: str
    amount: float
    payment_method: Optional[str]
    status: TopupStatus
    bank_reference: Optional[str]
    razorpay_order_id: Optional[str]
    processed_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TopupListResponse(BaseModel):
    """Paginated top-up request list."""
    requests: List[TopupResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Credit Limit Schemas
# =============================================================================

class CreditLimitRequest(BaseModel):
    """Schema for setting/updating credit limit."""
    user_id: int
    new_limit: float = Field(..., ge=0, description="New credit limit")
    reason: str = Field(..., min_length=10, max_length=500)
    effective_until: Optional[datetime] = None  # Null = permanent


class CreditLimitResponse(BaseModel):
    """Credit limit change response."""
    id: int
    wallet_id: int
    previous_limit: float
    new_limit: float
    reason: Optional[str]
    effective_from: datetime
    effective_until: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreditLimitHistory(BaseModel):
    """Credit limit history list."""
    history: List[CreditLimitResponse]
    current_limit: float
    current_used: float
    available_credit: float


# =============================================================================
# Wallet Statement Schemas
# =============================================================================

class StatementRequest(BaseModel):
    """Schema for requesting wallet statement."""
    start_date: datetime
    end_date: datetime
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")


class StatementSummary(BaseModel):
    """Wallet statement summary."""
    period_start: datetime
    period_end: datetime
    opening_balance: float
    closing_balance: float
    total_credits: float
    total_debits: float
    transaction_count: int
    transactions: List[TransactionResponse]


# =============================================================================
# Hold Schemas
# =============================================================================

class HoldRequest(BaseModel):
    """Schema for placing a hold on wallet balance."""
    amount: float = Field(..., gt=0)
    booking_id: int
    booking_type: str = Field(..., pattern="^(flight|hotel|bus)$")
    description: Optional[str] = None
    expiry_minutes: int = Field(default=30, ge=5, le=1440)  # 5 mins to 24 hours


class HoldReleaseRequest(BaseModel):
    """Schema for releasing a hold."""
    hold_id: str
    convert_to_debit: bool = False  # If true, converts hold to actual debit


class HoldResponse(BaseModel):
    """Hold operation response."""
    hold_id: str
    amount: float
    expires_at: datetime
    booking_id: int
    booking_type: str
    status: str
