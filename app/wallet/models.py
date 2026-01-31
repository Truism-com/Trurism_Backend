"""
Wallet Database Models

This module defines database models for wallet operations:
- Wallet: User wallet with balance tracking
- WalletTransaction: Transaction history for credits/debits
- CreditLimit: Agent credit limits for B2B operations
- WalletTopupRequest: Top-up requests for approval
"""

from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
import enum
from datetime import datetime

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User


class WalletStatus(str, enum.Enum):
    """Wallet status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class TransactionType(str, enum.Enum):
    """Wallet transaction types."""
    CREDIT = "credit"      # Money added to wallet
    DEBIT = "debit"        # Money deducted from wallet
    REFUND = "refund"      # Refund credited to wallet
    TOPUP = "topup"        # Top-up via payment
    BONUS = "bonus"        # Promotional bonus
    ADJUSTMENT = "adjustment"  # Manual adjustment by admin
    TRANSFER = "transfer"  # Transfer between wallets


class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class TopupStatus(str, enum.Enum):
    """Top-up request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Wallet(Base):
    """
    User wallet model for balance management.
    
    Each user has one wallet that tracks their balance,
    holds transactions, and manages credits.
    """
    __tablename__ = "wallets"
    
    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    
    # Balance fields
    balance: Mapped[float] = mapped_column(default=0.0)
    hold_amount: Mapped[float] = mapped_column(default=0.0)  # Amount on hold for pending transactions
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    
    # Credit limit (for agents)
    credit_limit: Mapped[float] = mapped_column(default=0.0)
    credit_used: Mapped[float] = mapped_column(default=0.0)
    
    # Status
    status: Mapped[WalletStatus] = mapped_column(default=WalletStatus.ACTIVE)
    
    # Limits
    daily_transaction_limit: Mapped[float] = mapped_column(default=100000.0)  # Max daily transactions
    min_balance: Mapped[float] = mapped_column(default=0.0)  # Minimum balance to maintain
    
    # Statistics
    total_credited: Mapped[float] = mapped_column(default=0.0)
    total_debited: Mapped[float] = mapped_column(default=0.0)
    last_transaction_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallet")
    transactions: Mapped[List["WalletTransaction"]] = relationship(
        "WalletTransaction", 
        back_populates="wallet", 
        order_by="desc(WalletTransaction.created_at)",
        foreign_keys="WalletTransaction.wallet_id"
    )
    topup_requests: Mapped[List["WalletTopupRequest"]] = relationship("WalletTopupRequest", back_populates="wallet")
    
    @property
    def available_balance(self) -> float:
        """Get available balance (balance - hold_amount)."""
        return float(self.balance) - float(self.hold_amount)
    
    @property
    def available_credit(self) -> float:
        """Get available credit limit."""
        return max(0.0, float(self.credit_limit) - float(self.credit_used))
    
    @property
    def total_available(self) -> float:
        """Get total available amount (balance + available credit)."""
        return self.available_balance + self.available_credit
    
    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>"


class WalletTransaction(Base):
    """
    Wallet transaction model for tracking all wallet operations.
    
    Every credit/debit operation is logged as a transaction
    for auditing and reconciliation.
    """
    __tablename__ = "wallet_transactions"
    
    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    
    # Transaction reference
    transaction_ref: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Transaction details
    type: Mapped[TransactionType] = mapped_column()
    amount: Mapped[float] = mapped_column()
    balance_before: Mapped[float] = mapped_column()
    balance_after: Mapped[float] = mapped_column()
    
    # Status
    status: Mapped[TransactionStatus] = mapped_column(default=TransactionStatus.COMPLETED)
    
    # Reference to related entities
    booking_id: Mapped[Optional[int]] = mapped_column(nullable=True)  # If related to a booking
    booking_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # flight/hotel/bus
    payment_transaction_id: Mapped[Optional[int]] = mapped_column(nullable=True)  # If related to payment
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Internal notes
    
    # For transfers
    related_wallet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wallets.id"), nullable=True)
    
    # Processing details
    processed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # Admin who processed
    
    # Metadata (renamed to avoid conflict with SQLAlchemy's MetaData)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for additional data
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions", foreign_keys=[wallet_id])
    related_wallet: Mapped[Optional["Wallet"]] = relationship("Wallet", foreign_keys=[related_wallet_id])
    processed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[processed_by_id])
    
    def __repr__(self):
        return f"<WalletTransaction(id={self.id}, ref={self.transaction_ref}, type={self.type}, amount={self.amount})>"


class WalletTopupRequest(Base):
    """
    Wallet top-up request model for adding funds.
    
    Users can request top-ups which need admin approval
    or can be processed automatically via payment gateway.
    """
    __tablename__ = "wallet_topup_requests"
    
    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    request_ref: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Request details
    amount: Mapped[float] = mapped_column()
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # bank_transfer, upi, etc.
    
    # Payment reference (if paid online)
    payment_transaction_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Bank transfer details (if bank transfer)
    bank_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transfer_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Status
    status: Mapped[TopupStatus] = mapped_column(default=TopupStatus.PENDING)
    
    # Processing
    processed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Proof document
    proof_document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    
    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="topup_requests")
    processed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[processed_by_id])
    
    def __repr__(self):
        return f"<WalletTopupRequest(id={self.id}, amount={self.amount}, status={self.status})>"


class CreditLimit(Base):
    """
    Credit limit configuration for agents.
    
    This model tracks credit limit assignments and history
    for B2B agent operations.
    """
    __tablename__ = "credit_limits"
    
    # Primary identification
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    
    # Credit limit change
    previous_limit: Mapped[float] = mapped_column()
    new_limit: Mapped[float] = mapped_column()
    
    # Reason and approval
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Validity
    effective_from: Mapped[datetime] = mapped_column(server_default=func.now())
    effective_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)  # Null = permanent
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet")
    approved_by: Mapped["User"] = relationship("User", foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f"<CreditLimit(wallet_id={self.wallet_id}, limit={self.new_limit})>"


# Indexes for better query performance
Index('ix_wallet_transactions_wallet_created', WalletTransaction.wallet_id, WalletTransaction.created_at.desc())
Index('ix_wallet_transactions_type', WalletTransaction.type)
Index('ix_wallet_topup_status', WalletTopupRequest.status)
