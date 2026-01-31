"""
Wallet Module

This module handles all wallet and balance operations including:
- User wallet management (balance, transactions)
- Credit/Debit operations
- Transaction history
- Refund credits
- Agent credit limits
- Wallet-based payments
"""

from app.wallet.models import (
    Wallet, WalletTransaction, WalletTopupRequest, CreditLimit,
    WalletStatus, TransactionType, TransactionStatus, TopupStatus
)
from app.wallet.services import (
    WalletService, TopupService, CreditLimitService,
    WalletError, InsufficientBalanceError, WalletNotFoundError,
    WalletSuspendedError, TransactionLimitExceededError
)
from app.wallet.api import router, admin_router

__all__ = [
    # Models
    "Wallet",
    "WalletTransaction", 
    "WalletTopupRequest",
    "CreditLimit",
    # Enums
    "WalletStatus",
    "TransactionType",
    "TransactionStatus",
    "TopupStatus",
    # Services
    "WalletService",
    "TopupService",
    "CreditLimitService",
    # Exceptions
    "WalletError",
    "InsufficientBalanceError",
    "WalletNotFoundError",
    "WalletSuspendedError",
    "TransactionLimitExceededError",
    # Routers
    "router",
    "admin_router"
]