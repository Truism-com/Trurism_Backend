"""
Wallet API Endpoints

REST API for wallet operations including:
- Balance checking
- Credits and debits
- Transfers
- Top-ups
- Transaction history
- Admin operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User, UserRole
from app.wallet.services import (
    WalletService, TopupService, CreditLimitService,
    WalletError, InsufficientBalanceError, WalletNotFoundError,
    WalletSuspendedError, TransactionLimitExceededError
)
from app.wallet.schemas import (
    WalletResponse, WalletBalance, WalletSummary,
    CreditRequest, DebitRequest, TransferRequest, RefundRequest, AdjustmentRequest,
    TransactionResponse, TransactionListResponse, TransactionFilter,
    TopupRequest, TopupOnlineRequest, TopupVerifyRequest, TopupApprovalRequest,
    TopupResponse, TopupListResponse,
    CreditLimitRequest, CreditLimitResponse, CreditLimitHistory,
    StatementRequest, StatementSummary,
    HoldRequest, HoldReleaseRequest, HoldResponse,
    TransactionType as SchemaTransactionType,
    TransactionStatus as SchemaTransactionStatus
)
from app.wallet.models import TransactionType, TransactionStatus

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


def handle_wallet_error(e: Exception):
    """Convert wallet exceptions to HTTP exceptions."""
    if isinstance(e, WalletNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif isinstance(e, InsufficientBalanceError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif isinstance(e, WalletSuspendedError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    elif isinstance(e, TransactionLimitExceededError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif isinstance(e, WalletError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        logger.error(f"Unexpected wallet error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# =============================================================================
# Balance Endpoints
# =============================================================================

@router.get("/balance", response_model=WalletBalance)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current wallet balance.
    
    Returns the user's wallet balance including:
    - Current balance
    - Hold amount (for pending transactions)
    - Available balance
    - Credit limit and usage (for agents)
    """
    try:
        service = WalletService(db)
        balance = await service.get_balance(int(current_user.id))
        return WalletBalance(**balance)
    except Exception as e:
        handle_wallet_error(e)


@router.get("/summary", response_model=WalletSummary)
async def get_wallet_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get wallet summary for dashboard.
    
    Returns a brief summary suitable for dashboard display.
    """
    try:
        service = WalletService(db)
        wallet = await service.get_wallet_by_user_id(int(current_user.id))
        
        if not wallet:
            # Create wallet if not exists
            wallet = await service.create_wallet(int(current_user.id))
        
        # Get today's transaction total
        today_txns = await service._get_today_debits(int(wallet.id))
        
        return WalletSummary(
            balance=wallet.balance,
            available_balance=wallet.available_balance,
            currency=wallet.currency,
            status=wallet.status,
            pending_transactions=0,  # TODO: Count pending
            today_transactions=today_txns
        )
    except Exception as e:
        handle_wallet_error(e)


@router.get("/", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full wallet details.
    
    Returns complete wallet information including all settings and statistics.
    """
    try:
        service = WalletService(db)
        wallet = await service.get_or_create_wallet(int(current_user.id))
        
        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            balance=wallet.balance,
            hold_amount=wallet.hold_amount,
            currency=wallet.currency,
            credit_limit=wallet.credit_limit,
            credit_used=wallet.credit_used,
            status=wallet.status,
            daily_transaction_limit=wallet.daily_transaction_limit,
            min_balance=wallet.min_balance,
            total_credited=wallet.total_credited,
            total_debited=wallet.total_debited,
            last_transaction_at=wallet.last_transaction_at,
            created_at=wallet.created_at,
            available_balance=wallet.available_balance,
            available_credit=wallet.available_credit,
            total_available=wallet.total_available
        )
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Transaction Endpoints
# =============================================================================

@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[SchemaTransactionType] = None,
    status: Optional[SchemaTransactionStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction history with optional filters.
    
    Supports filtering by:
    - Transaction type (credit, debit, refund, etc.)
    - Status (completed, pending, failed)
    - Date range
    - Amount range
    """
    try:
        service = WalletService(db)
        
        # Convert schema enums to model enums
        filters = TransactionFilter(
            type=TransactionType(type.value) if type else None,
            status=TransactionStatus(status.value) if status else None,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        result = await service.get_transactions(
            user_id=int(current_user.id),
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        return TransactionListResponse(
            transactions=[TransactionResponse.model_validate(t) for t in result["transactions"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        handle_wallet_error(e)


@router.get("/transactions/{transaction_ref}", response_model=TransactionResponse)
async def get_transaction(
    transaction_ref: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transaction by reference."""
    try:
        service = WalletService(db)
        transaction = await service.get_transaction_by_ref(transaction_ref)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_ref} not found"
            )
        
        # Verify ownership
        wallet = await service.get_wallet(int(transaction.wallet_id))
        if wallet is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )
        if int(wallet.user_id) != int(current_user.id) and str(current_user.role) != str(UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this transaction"
            )
        
        return TransactionResponse.model_validate(transaction)
    except HTTPException:
        raise
    except Exception as e:
        handle_wallet_error(e)


@router.post("/transfer", response_model=TransactionResponse)
async def transfer_funds(
    request: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Transfer funds to another user's wallet.
    
    Transfers from your wallet balance to another user.
    Credit limit cannot be used for transfers.
    """
    try:
        service = WalletService(db)
        debit_txn, credit_txn = await service.transfer(
            from_user_id=int(current_user.id),
            to_user_id=request.to_user_id,
            amount=request.amount,
            description=request.description or "Wallet transfer"
        )
        
        return TransactionResponse.model_validate(debit_txn)
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Statement Endpoints
# =============================================================================

@router.post("/statement", response_model=StatementSummary)
async def get_statement(
    request: StatementRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate wallet statement for a date range.
    
    Returns transaction history with opening/closing balances
    and summary statistics.
    """
    try:
        service = WalletService(db)
        statement = await service.get_statement(
            user_id=int(current_user.id),
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return StatementSummary(
            period_start=statement["period_start"],
            period_end=statement["period_end"],
            opening_balance=statement["opening_balance"],
            closing_balance=statement["closing_balance"],
            total_credits=statement["total_credits"],
            total_debits=statement["total_debits"],
            transaction_count=statement["transaction_count"],
            transactions=[TransactionResponse.model_validate(t) for t in statement["transactions"]]
        )
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Top-up Endpoints
# =============================================================================

@router.post("/topup/request", response_model=TopupResponse)
async def create_topup_request(
    request: TopupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a top-up request.
    
    For bank transfers, provide bank details and proof document.
    Admin approval is required for bank transfer top-ups.
    """
    try:
        service = TopupService(db)
        topup = await service.create_topup_request(
            user_id=int(current_user.id),
            amount=request.amount,
            payment_method=request.payment_method,
            bank_reference=request.bank_reference,
            bank_name=request.bank_name,
            transfer_date=request.transfer_date,
            proof_document_url=request.proof_document_url
        )
        
        return TopupResponse.model_validate(topup)
    except Exception as e:
        handle_wallet_error(e)


@router.post("/topup/online", response_model=dict)
async def initiate_online_topup(
    request: TopupOnlineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate online top-up via Razorpay.
    
    Creates a Razorpay order for payment.
    Returns order details to complete payment on client.
    """
    try:
        from app.payments.services import RazorpayService
        
        # Create Razorpay order
        razorpay_service = RazorpayService(db)
        
        # Prepare notes
        notes = {
            "purpose": "wallet_topup",
            "user_id": str(current_user.id)
        }
        
        order = razorpay_service.create_simple_order(
            amount=request.amount,
            currency="INR",
            notes=notes
        )
        
        # Create topup request
        topup_service = TopupService(db)
        topup = await topup_service.create_online_topup(
            user_id=int(current_user.id),
            amount=request.amount,
            razorpay_order_id=order["id"]
        )
        
        return {
            "topup_ref": topup.request_ref,
            "razorpay_order_id": order["id"],
            "amount": order["amount"] / 100,  # Convert from paise
            "currency": order["currency"],
            "key_id": razorpay_service.key_id
        }
    except Exception as e:
        logger.error(f"Failed to initiate online topup: {e}")
        handle_wallet_error(e)


@router.post("/topup/verify", response_model=TopupResponse)
async def verify_online_topup(
    request: TopupVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify and complete online top-up payment.
    
    Verifies Razorpay payment signature and credits wallet.
    """
    try:
        from app.payments.services import RazorpayService
        
        # Verify payment signature
        razorpay_service = RazorpayService(db)
        is_valid = razorpay_service.verify_payment_signature(
            order_id=request.razorpay_order_id,
            payment_id=request.razorpay_payment_id,
            signature=request.razorpay_signature
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature"
            )
        
        # Complete topup
        topup_service = TopupService(db)
        topup = await topup_service.complete_online_topup(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id
        )
        
        return TopupResponse.model_validate(topup)
    except HTTPException:
        raise
    except Exception as e:
        handle_wallet_error(e)


@router.get("/topup/history", response_model=TopupListResponse)
async def get_topup_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's top-up request history."""
    try:
        service = TopupService(db)
        result = await service.get_user_requests(
            user_id=int(current_user.id),
            page=page,
            page_size=page_size
        )
        
        return TopupListResponse(
            requests=[TopupResponse.model_validate(r) for r in result["requests"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Hold Endpoints (for booking integration)
# =============================================================================

@router.post("/hold", response_model=HoldResponse)
async def place_hold(
    request: HoldRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Place a hold on wallet balance for booking.
    
    Used during booking flow to reserve funds before confirmation.
    Hold expires after specified time if not released.
    """
    try:
        service = WalletService(db)
        hold = await service.place_hold(
            user_id=int(current_user.id),
            amount=request.amount,
            booking_id=request.booking_id,
            booking_type=request.booking_type,
            expiry_minutes=request.expiry_minutes
        )
        
        return HoldResponse(**hold)
    except Exception as e:
        handle_wallet_error(e)


@router.post("/hold/release")
async def release_hold(
    request: HoldReleaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Release a hold on wallet balance.
    
    If convert_to_debit is True, converts the hold to an actual debit.
    Otherwise, simply releases the hold back to available balance.
    """
    try:
        service = WalletService(db)
        transaction = await service.release_hold(
            hold_id=request.hold_id,
            convert_to_debit=request.convert_to_debit,
            description=f"Hold converted to payment"
        )
        
        if transaction:
            return {"message": "Hold converted to debit", "transaction_ref": transaction.transaction_ref}
        return {"message": "Hold released successfully"}
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Admin Endpoints
# =============================================================================

admin_router = APIRouter(prefix="/admin/wallet", tags=["Admin - Wallet"])


@admin_router.get("/user/{user_id}", response_model=WalletResponse)
async def admin_get_user_wallet(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get wallet details for a specific user (Admin only)."""
    try:
        service = WalletService(db)
        wallet = await service.get_wallet_by_user_id(user_id)
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wallet not found for user {user_id}"
            )
        
        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            balance=wallet.balance,
            hold_amount=wallet.hold_amount,
            currency=wallet.currency,
            credit_limit=wallet.credit_limit,
            credit_used=wallet.credit_used,
            status=wallet.status,
            daily_transaction_limit=wallet.daily_transaction_limit,
            min_balance=wallet.min_balance,
            total_credited=wallet.total_credited,
            total_debited=wallet.total_debited,
            last_transaction_at=wallet.last_transaction_at,
            created_at=wallet.created_at,
            available_balance=wallet.available_balance,
            available_credit=wallet.available_credit,
            total_available=wallet.total_available
        )
    except HTTPException:
        raise
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/credit", response_model=TransactionResponse)
async def admin_credit_wallet(
    request: CreditRequest,
    user_id: int = Query(..., description="User ID to credit"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Credit a user's wallet (Admin only)."""
    try:
        service = WalletService(db)
        transaction = await service.credit(
            user_id=user_id,
            amount=request.amount,
            description=request.description or request.reason or "Admin credit",
            processed_by_id=int(current_user.id),
            metadata={"credited_by": str(current_user.email)}
        )
        
        return TransactionResponse.model_validate(transaction)
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/debit", response_model=TransactionResponse)
async def admin_debit_wallet(
    request: DebitRequest,
    user_id: int = Query(..., description="User ID to debit"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Debit from a user's wallet (Admin only)."""
    try:
        service = WalletService(db)
        transaction = await service.debit(
            user_id=user_id,
            amount=request.amount,
            description=request.description or "Admin debit",
            booking_id=request.booking_id,
            booking_type=request.booking_type,
            processed_by_id=int(current_user.id),
            metadata={"debited_by": str(current_user.email)}
        )
        
        return TransactionResponse.model_validate(transaction)
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/adjustment", response_model=TransactionResponse)
async def admin_adjust_wallet(
    request: AdjustmentRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Make a manual adjustment to a user's wallet (Admin only).
    
    Positive amount = credit, Negative amount = debit.
    Requires a detailed reason for audit purposes.
    """
    try:
        service = WalletService(db)
        
        if request.amount > 0:
            transaction = await service.credit(
                user_id=request.user_id,
                amount=request.amount,
                description=f"Manual adjustment: {request.reason}",
                transaction_type=TransactionType.ADJUSTMENT,
                processed_by_id=int(current_user.id),
                metadata={"adjusted_by": str(current_user.email), "reason": request.reason}
            )
        else:
            transaction = await service.debit(
                user_id=request.user_id,
                amount=abs(request.amount),
                description=f"Manual adjustment: {request.reason}",
                processed_by_id=int(current_user.id),
                metadata={"adjusted_by": str(current_user.email), "reason": request.reason}
            )
        
        return TransactionResponse.model_validate(transaction)
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/refund", response_model=TransactionResponse)
async def admin_process_refund(
    request: RefundRequest,
    user_id: int = Query(..., description="User ID to refund"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a refund to user's wallet (Admin only)."""
    try:
        service = WalletService(db)
        transaction = await service.process_refund(
            user_id=user_id,
            amount=request.amount,
            booking_id=request.booking_id,
            booking_type=request.booking_type,
            reason=request.reason,
            processed_by_id=int(current_user.id)
        )
        
        return TransactionResponse.model_validate(transaction)
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Credit Limit Admin Endpoints
# =============================================================================

@admin_router.post("/credit-limit", response_model=CreditLimitResponse)
async def set_credit_limit(
    request: CreditLimitRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Set or update credit limit for an agent (Admin only)."""
    try:
        service = CreditLimitService(db)
        credit_limit = await service.set_credit_limit(
            user_id=request.user_id,
            new_limit=request.new_limit,
            reason=request.reason,
            approved_by_id=int(current_user.id),
            effective_until=request.effective_until
        )
        
        return CreditLimitResponse.model_validate(credit_limit)
    except Exception as e:
        handle_wallet_error(e)


@admin_router.get("/credit-limit/{user_id}/history", response_model=CreditLimitHistory)
async def get_credit_limit_history(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get credit limit history for a user (Admin only)."""
    try:
        service = CreditLimitService(db)
        result = await service.get_credit_limit_history(user_id)
        
        return CreditLimitHistory(
            history=[CreditLimitResponse.model_validate(h) for h in result["history"]],
            current_limit=result["current_limit"],
            current_used=result["current_used"],
            available_credit=result["available_credit"]
        )
    except Exception as e:
        handle_wallet_error(e)


# =============================================================================
# Top-up Admin Endpoints
# =============================================================================

@admin_router.get("/topup/pending", response_model=TopupListResponse)
async def get_pending_topups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending top-up requests (Admin only)."""
    try:
        service = TopupService(db)
        result = await service.get_pending_requests(page=page, page_size=page_size)
        
        return TopupListResponse(
            requests=[TopupResponse.model_validate(r) for r in result["requests"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/topup/{request_id}/approve", response_model=TopupResponse)
async def approve_topup(
    request_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending top-up request (Admin only)."""
    try:
        service = TopupService(db)
        topup = await service.approve_topup(
            request_id=request_id,
            approved_by_id=int(current_user.id)
        )
        
        return TopupResponse.model_validate(topup)
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/topup/{request_id}/reject", response_model=TopupResponse)
async def reject_topup(
    request_id: int,
    request: TopupApprovalRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a pending top-up request (Admin only)."""
    try:
        if request.approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use approve endpoint to approve"
            )
        
        service = TopupService(db)
        topup = await service.reject_topup(
            request_id=request_id,
            rejected_by_id=int(current_user.id),
            reason=request.rejection_reason or "Rejected"
        )
        
        return TopupResponse.model_validate(topup)
    except HTTPException:
        raise
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/suspend/{user_id}")
async def suspend_wallet(
    user_id: int,
    reason: str = Query(..., min_length=10),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Suspend a user's wallet (Admin only)."""
    try:
        service = WalletService(db)
        wallet = await service.get_wallet_by_user_id(user_id)
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wallet not found for user {user_id}"
            )
        
        from app.wallet.models import WalletStatus
        wallet.status = WalletStatus.SUSPENDED
        await db.commit()
        
        logger.warning(f"Wallet {wallet.id} suspended by admin {current_user.id}: {reason}")
        
        return {"message": f"Wallet suspended successfully", "reason": reason}
    except HTTPException:
        raise
    except Exception as e:
        handle_wallet_error(e)


@admin_router.post("/activate/{user_id}")
async def activate_wallet(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reactivate a suspended wallet (Admin only)."""
    try:
        service = WalletService(db)
        wallet = await service.get_wallet_by_user_id(user_id)
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wallet not found for user {user_id}"
            )
        
        from app.wallet.models import WalletStatus
        wallet.status = WalletStatus.ACTIVE
        await db.commit()
        
        logger.info(f"Wallet {wallet.id} activated by admin {current_user.id}")
        
        return {"message": "Wallet activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        handle_wallet_error(e)
