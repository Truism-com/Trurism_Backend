"""Add payment system tables

Revision ID: 002
Revises: 001
Create Date: 2026-01-21

Creates payment-related tables:
- payment_transactions: Razorpay payment records
- refunds: Refund tracking
- convenience_fees: Payment method fee configuration
- webhook_logs: Webhook event logging
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add payment system tables."""
    
    # Create enums
    payment_transaction_status_enum = sa.Enum(
        "created", "authorized", "captured", "failed", "refunded", "partial_refund",
        name="paymenttransactionstatus"
    )
    refund_status_enum = sa.Enum("pending", "processed", "failed", name="refundstatus")
    fee_type_enum = sa.Enum("fixed", "percentage", name="feetype")
    
    # payment_transactions table
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False, index=True),
        sa.Column("booking_type", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("razorpay_order_id", sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True, unique=True, index=True),
        sa.Column("razorpay_signature", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", payment_transaction_status_enum, nullable=False, server_default="created"),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("base_amount", sa.Float(), nullable=False),
        sa.Column("convenience_fee", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("taxes", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("gateway_response", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    
    # refunds table
    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False, index=True),
        sa.Column("razorpay_refund_id", sa.String(length=100), nullable=True, unique=True, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", refund_status_enum, nullable=False, server_default="pending"),
        sa.Column("gateway_response", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_by_id", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["payment_transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["processed_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    
    # convenience_fees table
    op.create_table(
        "convenience_fees",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False, unique=True),
        sa.Column("fee_type", fee_type_enum, nullable=False),
        sa.Column("fee_value", sa.Float(), nullable=False),
        sa.Column("min_fee", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("max_fee", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # webhook_logs table
    op.create_table(
        "webhook_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("razorpay_event_id", sa.String(length=100), nullable=True, unique=True),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("signature", sa.String(length=255), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index("ix_payment_transactions_booking", "payment_transactions", ["booking_id", "booking_type"])
    op.create_index("ix_payment_transactions_status", "payment_transactions", ["status"])
    op.create_index("ix_payment_transactions_created", "payment_transactions", ["created_at"])
    op.create_index("ix_refunds_transaction", "refunds", ["transaction_id"])
    op.create_index("ix_webhook_logs_event_type", "webhook_logs", ["event_type"])
    op.create_index("ix_webhook_logs_created", "webhook_logs", ["created_at"])


def downgrade() -> None:
    """Remove payment system tables."""
    
    # Drop indexes
    op.drop_index("ix_webhook_logs_created", table_name="webhook_logs")
    op.drop_index("ix_webhook_logs_event_type", table_name="webhook_logs")
    op.drop_index("ix_refunds_transaction", table_name="refunds")
    op.drop_index("ix_payment_transactions_created", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_status", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_booking", table_name="payment_transactions")
    
    # Drop tables
    op.drop_table("webhook_logs")
    op.drop_table("convenience_fees")
    op.drop_table("refunds")
    op.drop_table("payment_transactions")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS paymenttransactionstatus")
    op.execute("DROP TYPE IF EXISTS refundstatus")
    op.execute("DROP TYPE IF EXISTS feetype")
