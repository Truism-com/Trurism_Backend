"""
Wallet Services

Business logic for wallet operations including:
- Balance management
- Transactions (credit/debit/transfer)
- Top-up processing
- Credit limit management
- Hold/release operations
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, or_
from sqlalchemy.orm import selectinload

from app.wallet.models import (
    Wallet, WalletTransaction, WalletTopupRequest, CreditLimit,
    WalletStatus, TransactionType, TransactionStatus, TopupStatus
)
from app.wallet.schemas import (
    WalletCreate, TransactionFilter, TopupRequest, CreditLimitRequest
)
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)


class WalletError(Exception):
    """Base exception for wallet operations."""
    pass


class InsufficientBalanceError(WalletError):
    """Raised when wallet has insufficient balance."""
    pass


class WalletNotFoundError(WalletError):
    """Raised when wallet is not found."""
    pass


class WalletSuspendedError(WalletError):
    """Raised when wallet is suspended."""
    pass


class TransactionLimitExceededError(WalletError):
    """Raised when transaction limit is exceeded."""
    pass


def generate_transaction_ref() -> str:
    """Generate unique transaction reference."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"TXN{timestamp}{unique_id}"


def generate_topup_ref() -> str:
    """Generate unique top-up reference."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"TOP{timestamp}{unique_id}"


def generate_hold_id() -> str:
    """Generate unique hold ID."""
    return f"HOLD{uuid.uuid4().hex[:12].upper()}"


class WalletService:
    """Service class for wallet operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._holds: Dict[str, Dict[str, Any]] = {}  # In-memory holds (use Redis in production)
    
    # =========================================================================
    # Wallet CRUD Operations
    # =========================================================================
    
    async def create_wallet(self, user_id: int, currency: str = "INR") -> Wallet:
        """
        Create a new wallet for a user.
        
        Args:
            user_id: The user ID to create wallet for
            currency: Currency code (default: INR)
            
        Returns:
            Created Wallet object
        """
        # Check if wallet already exists
        existing = await self.get_wallet_by_user_id(user_id)
        if existing:
            return existing
        
        wallet = Wallet(
            user_id=user_id,
            currency=currency,
            balance=0.0,
            hold_amount=0.0,
            credit_limit=0.0,
            credit_used=0.0,
            status=WalletStatus.ACTIVE
        )
        
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        
        logger.info(f"Created wallet {wallet.id} for user {user_id}")
        return wallet
    
    async def get_wallet(self, wallet_id: int) -> Optional[Wallet]:
        """Get wallet by ID."""
        result = await self.db.execute(
            select(Wallet).where(Wallet.id == wallet_id)
        )
        return result.scalar_one_or_none()
    
    async def get_wallet_by_user_id(self, user_id: int) -> Optional[Wallet]:
        """Get wallet by user ID."""
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_wallet(self, user_id: int) -> Wallet:
        """Get existing wallet or create new one."""
        wallet = await self.get_wallet_by_user_id(user_id)
        if not wallet:
            wallet = await self.create_wallet(user_id)
        return wallet
    
    async def _validate_wallet(self, wallet: Wallet) -> None:
        """Validate wallet is active."""
        if wallet.status == WalletStatus.SUSPENDED:
            raise WalletSuspendedError("Wallet is suspended")
        if wallet.status == WalletStatus.CLOSED:
            raise WalletSuspendedError("Wallet is closed")
    
    # =========================================================================
    # Balance Operations
    # =========================================================================
    
    async def get_balance(self, user_id: int) -> Dict[str, Any]:
        """
        Get wallet balance summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Balance summary dictionary
        """
        wallet = await self.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        return {
            "balance": wallet.balance,
            "hold_amount": wallet.hold_amount,
            "available_balance": wallet.available_balance,
            "credit_limit": wallet.credit_limit,
            "credit_used": wallet.credit_used,
            "available_credit": wallet.available_credit,
            "total_available": wallet.total_available,
            "currency": wallet.currency,
            "status": wallet.status
        }
    
    async def credit(
        self,
        user_id: int,
        amount: float,
        description: str,
        transaction_type: TransactionType = TransactionType.CREDIT,
        booking_id: Optional[int] = None,
        booking_type: Optional[str] = None,
        payment_transaction_id: Optional[int] = None,
        processed_by_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> WalletTransaction:
        """
        Credit amount to wallet.
        
        Args:
            user_id: User ID to credit
            amount: Amount to credit (positive)
            description: Transaction description
            transaction_type: Type of credit transaction
            booking_id: Related booking ID if any
            booking_type: Type of booking (flight/hotel/bus)
            payment_transaction_id: Related payment ID if any
            processed_by_id: Admin who processed this
            metadata: Additional metadata
            
        Returns:
            Created WalletTransaction
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        wallet = await self.get_or_create_wallet(user_id)
        await self._validate_wallet(wallet)
        
        balance_before = wallet.balance
        wallet.balance += amount
        wallet.total_credited += amount
        wallet.last_transaction_at = datetime.utcnow()
        
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_ref=generate_transaction_ref(),
            type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            status=TransactionStatus.COMPLETED,
            booking_id=booking_id,
            booking_type=booking_type,
            payment_transaction_id=payment_transaction_id,
            description=description,
            processed_by_id=processed_by_id,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        logger.info(f"Credited {amount} to wallet {wallet.id}, ref: {transaction.transaction_ref}")
        return transaction
    
    async def debit(
        self,
        user_id: int,
        amount: float,
        description: str,
        booking_id: Optional[int] = None,
        booking_type: Optional[str] = None,
        use_credit: bool = True,
        processed_by_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> WalletTransaction:
        """
        Debit amount from wallet.
        
        Args:
            user_id: User ID to debit
            amount: Amount to debit (positive)
            description: Transaction description
            booking_id: Related booking ID
            booking_type: Type of booking
            use_credit: Whether to use credit if balance insufficient
            processed_by_id: Admin who processed this
            metadata: Additional metadata
            
        Returns:
            Created WalletTransaction
            
        Raises:
            InsufficientBalanceError: If balance is insufficient
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        wallet = await self.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        await self._validate_wallet(wallet)
        
        # Check daily limit
        today_debits = await self._get_today_debits(wallet.id)
        if today_debits + amount > wallet.daily_transaction_limit:
            raise TransactionLimitExceededError(
                f"Daily transaction limit of {wallet.daily_transaction_limit} exceeded"
            )
        
        # Check balance
        available = wallet.available_balance
        if use_credit:
            available += wallet.available_credit
        
        if amount > available:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: {available}, Required: {amount}"
            )
        
        # Check minimum balance
        if wallet.balance - amount < wallet.min_balance and not use_credit:
            raise InsufficientBalanceError(
                f"Transaction would breach minimum balance of {wallet.min_balance}"
            )
        
        balance_before = wallet.balance
        credit_before = wallet.credit_used
        
        # Debit from balance first, then credit
        if amount <= wallet.available_balance:
            wallet.balance -= amount
        else:
            # Use all available balance
            debit_from_balance = wallet.available_balance
            debit_from_credit = amount - debit_from_balance
            wallet.balance -= debit_from_balance
            wallet.credit_used += debit_from_credit
        
        wallet.total_debited += amount
        wallet.last_transaction_at = datetime.utcnow()
        
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_ref=generate_transaction_ref(),
            type=TransactionType.DEBIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            status=TransactionStatus.COMPLETED,
            booking_id=booking_id,
            booking_type=booking_type,
            description=description,
            processed_by_id=processed_by_id,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        logger.info(f"Debited {amount} from wallet {wallet.id}, ref: {transaction.transaction_ref}")
        return transaction
    
    async def _get_today_debits(self, wallet_id: int) -> float:
        """Get total debits for today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.sum(WalletTransaction.amount))
            .where(
                and_(
                    WalletTransaction.wallet_id == wallet_id,
                    WalletTransaction.type == TransactionType.DEBIT,
                    WalletTransaction.status == TransactionStatus.COMPLETED,
                    WalletTransaction.created_at >= today_start
                )
            )
        )
        return result.scalar() or 0.0
    
    # =========================================================================
    # Transfer Operations
    # =========================================================================
    
    async def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: float,
        description: str,
        processed_by_id: Optional[int] = None
    ) -> Tuple[WalletTransaction, WalletTransaction]:
        """
        Transfer amount between wallets.
        
        Args:
            from_user_id: Source user ID
            to_user_id: Destination user ID
            amount: Amount to transfer
            description: Transfer description
            processed_by_id: Admin who processed this
            
        Returns:
            Tuple of (debit_transaction, credit_transaction)
        """
        if from_user_id == to_user_id:
            raise ValueError("Cannot transfer to self")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        from_wallet = await self.get_wallet_by_user_id(from_user_id)
        if not from_wallet:
            raise WalletNotFoundError(f"Source wallet not found for user {from_user_id}")
        
        to_wallet = await self.get_or_create_wallet(to_user_id)
        
        await self._validate_wallet(from_wallet)
        await self._validate_wallet(to_wallet)
        
        # Check balance
        if amount > from_wallet.available_balance:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: {from_wallet.available_balance}, Required: {amount}"
            )
        
        transfer_ref = generate_transaction_ref()
        
        # Debit from source
        from_balance_before = from_wallet.balance
        from_wallet.balance -= amount
        from_wallet.total_debited += amount
        from_wallet.last_transaction_at = datetime.utcnow()
        
        debit_txn = WalletTransaction(
            wallet_id=from_wallet.id,
            transaction_ref=transfer_ref + "-D",
            type=TransactionType.TRANSFER,
            amount=amount,
            balance_before=from_balance_before,
            balance_after=from_wallet.balance,
            status=TransactionStatus.COMPLETED,
            description=f"Transfer to user {to_user_id}: {description}",
            related_wallet_id=to_wallet.id,
            processed_by_id=processed_by_id
        )
        
        # Credit to destination
        to_balance_before = to_wallet.balance
        to_wallet.balance += amount
        to_wallet.total_credited += amount
        to_wallet.last_transaction_at = datetime.utcnow()
        
        credit_txn = WalletTransaction(
            wallet_id=to_wallet.id,
            transaction_ref=transfer_ref + "-C",
            type=TransactionType.TRANSFER,
            amount=amount,
            balance_before=to_balance_before,
            balance_after=to_wallet.balance,
            status=TransactionStatus.COMPLETED,
            description=f"Transfer from user {from_user_id}: {description}",
            related_wallet_id=from_wallet.id,
            processed_by_id=processed_by_id
        )
        
        self.db.add(debit_txn)
        self.db.add(credit_txn)
        await self.db.commit()
        
        logger.info(f"Transfer of {amount} from wallet {from_wallet.id} to {to_wallet.id}")
        return debit_txn, credit_txn
    
    # =========================================================================
    # Refund Operations
    # =========================================================================
    
    async def process_refund(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        reason: str,
        processed_by_id: Optional[int] = None
    ) -> WalletTransaction:
        """
        Process refund to wallet.
        
        Args:
            user_id: User ID to refund
            amount: Refund amount
            booking_id: Related booking ID
            booking_type: Type of booking
            reason: Refund reason
            processed_by_id: Admin who processed
            
        Returns:
            Refund transaction
        """
        return await self.credit(
            user_id=user_id,
            amount=amount,
            description=f"Refund for {booking_type} booking #{booking_id}: {reason}",
            transaction_type=TransactionType.REFUND,
            booking_id=booking_id,
            booking_type=booking_type,
            processed_by_id=processed_by_id,
            metadata={"reason": reason}
        )
    
    # =========================================================================
    # Hold Operations (for booking flow)
    # =========================================================================
    
    async def place_hold(
        self,
        user_id: int,
        amount: float,
        booking_id: int,
        booking_type: str,
        expiry_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Place a hold on wallet balance for pending booking.
        
        Args:
            user_id: User ID
            amount: Amount to hold
            booking_id: Booking ID
            booking_type: Type of booking
            expiry_minutes: Hold expiry in minutes
            
        Returns:
            Hold details
        """
        wallet = await self.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        await self._validate_wallet(wallet)
        
        # Check available balance
        if amount > wallet.available_balance:
            raise InsufficientBalanceError(
                f"Insufficient balance for hold. Available: {wallet.available_balance}"
            )
        
        # Place hold
        hold_id = generate_hold_id()
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        
        wallet.hold_amount += amount
        await self.db.commit()
        
        # Store hold details (use Redis in production)
        self._holds[hold_id] = {
            "wallet_id": wallet.id,
            "user_id": user_id,
            "amount": amount,
            "booking_id": booking_id,
            "booking_type": booking_type,
            "expires_at": expires_at,
            "status": "active"
        }
        
        logger.info(f"Placed hold {hold_id} for {amount} on wallet {wallet.id}")
        
        return {
            "hold_id": hold_id,
            "amount": amount,
            "expires_at": expires_at,
            "booking_id": booking_id,
            "booking_type": booking_type,
            "status": "active"
        }
    
    async def release_hold(
        self,
        hold_id: str,
        convert_to_debit: bool = False,
        description: Optional[str] = None
    ) -> Optional[WalletTransaction]:
        """
        Release a hold on wallet balance.
        
        Args:
            hold_id: Hold ID to release
            convert_to_debit: If True, converts hold to actual debit
            description: Transaction description if converting to debit
            
        Returns:
            WalletTransaction if converted to debit, None otherwise
        """
        hold = self._holds.get(hold_id)
        if not hold:
            raise WalletError(f"Hold {hold_id} not found")
        
        if hold["status"] != "active":
            raise WalletError(f"Hold {hold_id} is not active")
        
        wallet = await self.get_wallet(hold["wallet_id"])
        if not wallet:
            raise WalletNotFoundError("Wallet not found")
        
        # Release hold
        wallet.hold_amount = max(0, wallet.hold_amount - hold["amount"])
        
        transaction = None
        if convert_to_debit:
            # Convert to actual debit
            transaction = await self.debit(
                user_id=hold["user_id"],
                amount=hold["amount"],
                description=description or f"Payment for {hold['booking_type']} booking",
                booking_id=hold["booking_id"],
                booking_type=hold["booking_type"],
                use_credit=False  # Already validated during hold
            )
        
        hold["status"] = "released" if not convert_to_debit else "converted"
        await self.db.commit()
        
        logger.info(f"Released hold {hold_id}, converted to debit: {convert_to_debit}")
        return transaction
    
    # =========================================================================
    # Transaction History
    # =========================================================================
    
    async def get_transactions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[TransactionFilter] = None
    ) -> Dict[str, Any]:
        """
        Get transaction history for a wallet.
        
        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page
            filters: Optional filters
            
        Returns:
            Paginated transaction list
        """
        wallet = await self.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        # Build query
        query = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id
        )
        
        if filters:
            if filters.type:
                query = query.where(WalletTransaction.type == filters.type)
            if filters.status:
                query = query.where(WalletTransaction.status == filters.status)
            if filters.start_date:
                query = query.where(WalletTransaction.created_at >= filters.start_date)
            if filters.end_date:
                query = query.where(WalletTransaction.created_at <= filters.end_date)
            if filters.min_amount:
                query = query.where(WalletTransaction.amount >= filters.min_amount)
            if filters.max_amount:
                query = query.where(WalletTransaction.amount <= filters.max_amount)
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        # Paginate
        query = query.order_by(WalletTransaction.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return {
            "transactions": transactions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def get_transaction_by_ref(self, transaction_ref: str) -> Optional[WalletTransaction]:
        """Get transaction by reference."""
        result = await self.db.execute(
            select(WalletTransaction).where(
                WalletTransaction.transaction_ref == transaction_ref
            )
        )
        return result.scalar_one_or_none()
    
    # =========================================================================
    # Statement Generation
    # =========================================================================
    
    async def get_statement(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate wallet statement for a date range.
        
        Args:
            user_id: User ID
            start_date: Statement start date
            end_date: Statement end date
            
        Returns:
            Statement summary with transactions
        """
        wallet = await self.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        # Get transactions in range
        result = await self.db.execute(
            select(WalletTransaction)
            .where(
                and_(
                    WalletTransaction.wallet_id == wallet.id,
                    WalletTransaction.created_at >= start_date,
                    WalletTransaction.created_at <= end_date,
                    WalletTransaction.status == TransactionStatus.COMPLETED
                )
            )
            .order_by(WalletTransaction.created_at)
        )
        transactions = result.scalars().all()
        
        # Calculate totals
        total_credits = sum(t.amount for t in transactions if t.type in [
            TransactionType.CREDIT, TransactionType.REFUND, 
            TransactionType.TOPUP, TransactionType.BONUS
        ])
        total_debits = sum(t.amount for t in transactions if t.type == TransactionType.DEBIT)
        
        # Get opening balance (balance before first transaction in range)
        opening_balance = transactions[0].balance_before if transactions else wallet.balance
        closing_balance = transactions[-1].balance_after if transactions else wallet.balance
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "transaction_count": len(transactions),
            "transactions": transactions
        }


class TopupService:
    """Service for handling wallet top-ups."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = WalletService(db)
    
    async def create_topup_request(
        self,
        user_id: int,
        amount: float,
        payment_method: str,
        bank_reference: Optional[str] = None,
        bank_name: Optional[str] = None,
        transfer_date: Optional[datetime] = None,
        proof_document_url: Optional[str] = None
    ) -> WalletTopupRequest:
        """
        Create a new top-up request.
        
        Args:
            user_id: User ID
            amount: Top-up amount
            payment_method: Payment method (online/bank_transfer)
            bank_reference: Bank transfer reference
            bank_name: Bank name
            transfer_date: Date of transfer
            proof_document_url: URL to proof document
            
        Returns:
            Created WalletTopupRequest
        """
        wallet = await self.wallet_service.get_or_create_wallet(user_id)
        
        topup_request = WalletTopupRequest(
            wallet_id=wallet.id,
            request_ref=generate_topup_ref(),
            amount=amount,
            payment_method=payment_method,
            bank_reference=bank_reference,
            bank_name=bank_name,
            transfer_date=transfer_date,
            proof_document_url=proof_document_url,
            status=TopupStatus.PENDING
        )
        
        self.db.add(topup_request)
        await self.db.commit()
        await self.db.refresh(topup_request)
        
        logger.info(f"Created top-up request {topup_request.request_ref} for {amount}")
        return topup_request
    
    async def create_online_topup(
        self,
        user_id: int,
        amount: float,
        razorpay_order_id: str
    ) -> WalletTopupRequest:
        """
        Create top-up request for online payment.
        
        Args:
            user_id: User ID
            amount: Top-up amount
            razorpay_order_id: Razorpay order ID
            
        Returns:
            Created WalletTopupRequest
        """
        wallet = await self.wallet_service.get_or_create_wallet(user_id)
        
        topup_request = WalletTopupRequest(
            wallet_id=wallet.id,
            request_ref=generate_topup_ref(),
            amount=amount,
            payment_method="online",
            razorpay_order_id=razorpay_order_id,
            status=TopupStatus.PENDING
        )
        
        self.db.add(topup_request)
        await self.db.commit()
        await self.db.refresh(topup_request)
        
        return topup_request
    
    async def complete_online_topup(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str
    ) -> WalletTopupRequest:
        """
        Complete online top-up after successful payment.
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            
        Returns:
            Updated WalletTopupRequest
        """
        result = await self.db.execute(
            select(WalletTopupRequest).where(
                WalletTopupRequest.razorpay_order_id == razorpay_order_id
            )
        )
        topup_request = result.scalar_one_or_none()
        
        if not topup_request:
            raise WalletError(f"Top-up request not found for order {razorpay_order_id}")
        
        if topup_request.status != TopupStatus.PENDING:
            raise WalletError(f"Top-up request is not pending")
        
        # Update topup request
        topup_request.razorpay_payment_id = razorpay_payment_id
        topup_request.status = TopupStatus.COMPLETED
        topup_request.processed_at = datetime.utcnow()
        
        # Credit wallet
        wallet = await self.wallet_service.get_wallet(topup_request.wallet_id)
        if wallet is None:
            raise WalletNotFoundError(f"Wallet not found for top-up request {topup_request.request_ref}")
        await self.wallet_service.credit(
            user_id=wallet.user_id,
            amount=topup_request.amount,
            description=f"Wallet top-up via online payment",
            transaction_type=TransactionType.TOPUP,
            metadata={
                "topup_ref": topup_request.request_ref,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id
            }
        )
        
        await self.db.commit()
        await self.db.refresh(topup_request)
        
        logger.info(f"Completed online top-up {topup_request.request_ref}")
        return topup_request
    
    async def approve_topup(
        self,
        request_id: int,
        approved_by_id: int
    ) -> WalletTopupRequest:
        """
        Approve a pending bank transfer top-up request.
        
        Args:
            request_id: Top-up request ID
            approved_by_id: Admin user ID who approved
            
        Returns:
            Updated WalletTopupRequest
        """
        result = await self.db.execute(
            select(WalletTopupRequest).where(WalletTopupRequest.id == request_id)
        )
        topup_request = result.scalar_one_or_none()
        
        if not topup_request:
            raise WalletError(f"Top-up request {request_id} not found")
        
        if topup_request.status != TopupStatus.PENDING:
            raise WalletError(f"Top-up request is not pending")
        
        # Update status
        topup_request.status = TopupStatus.APPROVED
        topup_request.processed_by_id = approved_by_id
        topup_request.processed_at = datetime.utcnow()
        
        # Credit wallet
        wallet = await self.wallet_service.get_wallet(topup_request.wallet_id)
        if wallet is None:
            raise WalletNotFoundError(f"Wallet not found for top-up request {topup_request.request_ref}")
        await self.wallet_service.credit(
            user_id=wallet.user_id,
            amount=topup_request.amount,
            description=f"Wallet top-up via bank transfer",
            transaction_type=TransactionType.TOPUP,
            processed_by_id=approved_by_id,
            metadata={
                "topup_ref": topup_request.request_ref,
                "bank_reference": topup_request.bank_reference,
                "bank_name": topup_request.bank_name
            }
        )
        
        topup_request.status = TopupStatus.COMPLETED
        await self.db.commit()
        await self.db.refresh(topup_request)
        
        logger.info(f"Approved top-up request {topup_request.request_ref}")
        return topup_request
    
    async def reject_topup(
        self,
        request_id: int,
        rejected_by_id: int,
        reason: str
    ) -> WalletTopupRequest:
        """
        Reject a pending top-up request.
        
        Args:
            request_id: Top-up request ID
            rejected_by_id: Admin user ID who rejected
            reason: Rejection reason
            
        Returns:
            Updated WalletTopupRequest
        """
        result = await self.db.execute(
            select(WalletTopupRequest).where(WalletTopupRequest.id == request_id)
        )
        topup_request = result.scalar_one_or_none()
        
        if not topup_request:
            raise WalletError(f"Top-up request {request_id} not found")
        
        if topup_request.status != TopupStatus.PENDING:
            raise WalletError(f"Top-up request is not pending")
        
        topup_request.status = TopupStatus.REJECTED
        topup_request.processed_by_id = rejected_by_id
        topup_request.processed_at = datetime.utcnow()
        topup_request.rejection_reason = reason
        
        await self.db.commit()
        await self.db.refresh(topup_request)
        
        logger.info(f"Rejected top-up request {topup_request.request_ref}: {reason}")
        return topup_request
    
    async def get_pending_requests(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get pending top-up requests (for admin)."""
        query = select(WalletTopupRequest).where(
            WalletTopupRequest.status == TopupStatus.PENDING
        )
        
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        query = query.order_by(WalletTopupRequest.created_at)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return {
            "requests": requests,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_user_requests(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get user's top-up requests."""
        wallet = await self.wallet_service.get_wallet_by_user_id(user_id)
        if not wallet:
            return {"requests": [], "total": 0, "page": page, "page_size": page_size}
        
        query = select(WalletTopupRequest).where(
            WalletTopupRequest.wallet_id == wallet.id
        )
        
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        query = query.order_by(WalletTopupRequest.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return {
            "requests": requests,
            "total": total,
            "page": page,
            "page_size": page_size
        }


class CreditLimitService:
    """Service for managing agent credit limits."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = WalletService(db)
    
    async def set_credit_limit(
        self,
        user_id: int,
        new_limit: float,
        reason: str,
        approved_by_id: int,
        effective_until: Optional[datetime] = None
    ) -> CreditLimit:
        """
        Set or update credit limit for an agent.
        
        Args:
            user_id: Agent user ID
            new_limit: New credit limit
            reason: Reason for change
            approved_by_id: Admin who approved
            effective_until: Optional expiry date
            
        Returns:
            Created CreditLimit record
        """
        wallet = await self.wallet_service.get_or_create_wallet(user_id)
        
        previous_limit = wallet.credit_limit
        
        # Create history record
        credit_limit = CreditLimit(
            wallet_id=wallet.id,
            previous_limit=previous_limit,
            new_limit=new_limit,
            reason=reason,
            approved_by_id=approved_by_id,
            effective_until=effective_until
        )
        
        # Update wallet
        wallet.credit_limit = new_limit
        
        # If new limit is less than used, adjust credit_used
        if new_limit < wallet.credit_used:
            wallet.credit_used = new_limit
        
        self.db.add(credit_limit)
        await self.db.commit()
        await self.db.refresh(credit_limit)
        
        logger.info(f"Set credit limit for user {user_id}: {previous_limit} -> {new_limit}")
        return credit_limit
    
    async def get_credit_limit_history(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get credit limit history for a user."""
        wallet = await self.wallet_service.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        result = await self.db.execute(
            select(CreditLimit)
            .where(CreditLimit.wallet_id == wallet.id)
            .order_by(CreditLimit.created_at.desc())
        )
        history = result.scalars().all()
        
        return {
            "history": history,
            "current_limit": wallet.credit_limit,
            "current_used": wallet.credit_used,
            "available_credit": wallet.available_credit
        }
    
    async def repay_credit(
        self,
        user_id: int,
        amount: float,
        description: str = "Credit repayment"
    ) -> WalletTransaction:
        """
        Repay used credit.
        
        Args:
            user_id: User ID
            amount: Repayment amount
            description: Transaction description
            
        Returns:
            WalletTransaction for the repayment
        """
        wallet = await self.wallet_service.get_wallet_by_user_id(user_id)
        if not wallet:
            raise WalletNotFoundError(f"Wallet not found for user {user_id}")
        
        if wallet.credit_used <= 0:
            raise WalletError("No credit to repay")
        
        if amount > wallet.credit_used:
            amount = wallet.credit_used  # Cap at credit used
        
        # Credit the wallet and reduce credit_used
        transaction = await self.wallet_service.credit(
            user_id=user_id,
            amount=amount,
            description=description,
            transaction_type=TransactionType.CREDIT,
            metadata={"type": "credit_repayment"}
        )
        
        # Reduce credit used
        wallet.credit_used = max(0, wallet.credit_used - amount)
        await self.db.commit()
        
        logger.info(f"Credit repayment of {amount} for user {user_id}")
        return transaction
