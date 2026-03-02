"""Add wallet system tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-XX

This migration creates the wallet system tables:
- wallets: User wallet with balance tracking
- wallet_transactions: Transaction history
- wallet_topup_requests: Top-up request tracking
- credit_limits: Credit limit history for agents
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_add_wallet_system'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create wallet status enum
    wallet_status_enum = postgresql.ENUM(
        'active', 'suspended', 'closed',
        name='walletstatus',
        create_type=True
    )
    wallet_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create transaction type enum
    transaction_type_enum = postgresql.ENUM(
        'credit', 'debit', 'refund', 'topup', 'bonus', 'adjustment', 'transfer',
        name='transactiontype',
        create_type=True
    )
    transaction_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create transaction status enum
    transaction_status_enum = postgresql.ENUM(
        'pending', 'completed', 'failed', 'reversed',
        name='transactionstatus',
        create_type=True
    )
    transaction_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create topup status enum
    topup_status_enum = postgresql.ENUM(
        'pending', 'approved', 'rejected', 'completed',
        name='topupstatus',
        create_type=True
    )
    topup_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False, server_default='0'),
        sa.Column('hold_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='INR'),
        sa.Column('credit_limit', sa.Float(), nullable=False, server_default='0'),
        sa.Column('credit_used', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', wallet_status_enum, nullable=False, server_default='active'),
        sa.Column('daily_transaction_limit', sa.Float(), nullable=False, server_default='100000'),
        sa.Column('min_balance', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_credited', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_debited', sa.Float(), nullable=False, server_default='0'),
        sa.Column('last_transaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_wallets_id', 'wallets', ['id'])
    op.create_index('ix_wallets_user_id', 'wallets', ['user_id'])
    
    # Create wallet_transactions table
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('transaction_ref', sa.String(50), nullable=False),
        sa.Column('type', transaction_type_enum, nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('balance_before', sa.Float(), nullable=False),
        sa.Column('balance_after', sa.Float(), nullable=False),
        sa.Column('status', transaction_status_enum, nullable=False, server_default='completed'),
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('booking_type', sa.String(20), nullable=True),
        sa.Column('payment_transaction_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('related_wallet_id', sa.Integer(), nullable=True),
        sa.Column('processed_by_id', sa.Integer(), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_wallet_id'], ['wallets.id']),
        sa.ForeignKeyConstraint(['processed_by_id'], ['users.id']),
        sa.UniqueConstraint('transaction_ref')
    )
    op.create_index('ix_wallet_transactions_id', 'wallet_transactions', ['id'])
    op.create_index('ix_wallet_transactions_wallet_id', 'wallet_transactions', ['wallet_id'])
    op.create_index('ix_wallet_transactions_transaction_ref', 'wallet_transactions', ['transaction_ref'])
    op.create_index('ix_wallet_transactions_wallet_created', 'wallet_transactions', ['wallet_id', sa.text('created_at DESC')])
    op.create_index('ix_wallet_transactions_type', 'wallet_transactions', ['type'])
    
    # Create wallet_topup_requests table
    op.create_table(
        'wallet_topup_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('request_ref', sa.String(50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_transaction_id', sa.Integer(), nullable=True),
        sa.Column('razorpay_order_id', sa.String(100), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(100), nullable=True),
        sa.Column('bank_reference', sa.String(100), nullable=True),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('transfer_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', topup_status_enum, nullable=False, server_default='pending'),
        sa.Column('processed_by_id', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('proof_document_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['processed_by_id'], ['users.id']),
        sa.UniqueConstraint('request_ref')
    )
    op.create_index('ix_wallet_topup_requests_id', 'wallet_topup_requests', ['id'])
    op.create_index('ix_wallet_topup_requests_wallet_id', 'wallet_topup_requests', ['wallet_id'])
    op.create_index('ix_wallet_topup_requests_request_ref', 'wallet_topup_requests', ['request_ref'])
    op.create_index('ix_wallet_topup_status', 'wallet_topup_requests', ['status'])
    
    # Create credit_limits table
    op.create_table(
        'credit_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('previous_limit', sa.Float(), nullable=False),
        sa.Column('new_limit', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'])
    )
    op.create_index('ix_credit_limits_id', 'credit_limits', ['id'])
    op.create_index('ix_credit_limits_wallet_id', 'credit_limits', ['wallet_id'])


def downgrade():
    # Drop tables
    op.drop_table('credit_limits')
    op.drop_table('wallet_topup_requests')
    op.drop_table('wallet_transactions')
    op.drop_table('wallets')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS topupstatus")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS walletstatus")
