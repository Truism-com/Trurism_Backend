"""Convert Float columns to Numeric(14,2) for monetary values

Revision ID: 013_convert_float_to_numeric
Revises: 012_composite_unique_booking_ref
Create Date: 2026-05-15

Converts all monetary Float columns to Numeric(14,2) Decimal across
wallet, payments, and booking models to prevent floating-point precision
drift and ensure accurate financial calculations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_convert_float_to_numeric'
down_revision = '012_composite_unique_booking_ref'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert Float columns to Numeric(14,2) for monetary values."""
    
    # Wallet table conversions
    with op.batch_alter_table('wallets') as batch_op:
        batch_op.alter_column('balance',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('hold_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('credit_limit',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('credit_used',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('daily_transaction_limit',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('min_balance',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('total_credited',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('total_debited',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
    
    # Payment transactions table conversions
    with op.batch_alter_table('payment_transactions') as batch_op:
        batch_op.alter_column('amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('base_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('convenience_fee',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('taxes',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
    
    # Flight bookings table conversions
    with op.batch_alter_table('flight_bookings') as batch_op:
        batch_op.alter_column('total_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('base_fare',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('taxes',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('refund_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=True)
    
    # Hotel bookings table conversions
    with op.batch_alter_table('hotel_bookings') as batch_op:
        batch_op.alter_column('total_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('room_rate',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('base_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('taxes',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('refund_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=True)
    
    # Bus bookings table conversions
    with op.batch_alter_table('bus_bookings') as batch_op:
        batch_op.alter_column('total_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('fare_per_passenger',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('base_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('taxes',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('refund_amount',
                              type_=sa.Numeric(14, 2),
                              existing_type=sa.Float(),
                              existing_nullable=True)


def downgrade() -> None:
    """Revert Numeric(14,2) columns back to Float."""
    
    # Bus bookings table reversions
    with op.batch_alter_table('bus_bookings') as batch_op:
        batch_op.alter_column('refund_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=True)
        batch_op.alter_column('taxes',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('base_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('fare_per_passenger',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('total_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
    
    # Hotel bookings table reversions
    with op.batch_alter_table('hotel_bookings') as batch_op:
        batch_op.alter_column('refund_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=True)
        batch_op.alter_column('taxes',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('base_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('room_rate',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('total_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
    
    # Flight bookings table reversions
    with op.batch_alter_table('flight_bookings') as batch_op:
        batch_op.alter_column('refund_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=True)
        batch_op.alter_column('taxes',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('base_fare',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('total_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
    
    # Payment transactions table reversions
    with op.batch_alter_table('payment_transactions') as batch_op:
        batch_op.alter_column('taxes',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('convenience_fee',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('base_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
    
    # Wallet table reversions
    with op.batch_alter_table('wallets') as batch_op:
        batch_op.alter_column('total_debited',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('total_credited',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('min_balance',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('daily_transaction_limit',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('credit_used',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('credit_limit',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('hold_amount',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
        batch_op.alter_column('balance',
                              type_=sa.Float(),
                              existing_type=sa.Numeric(14, 2),
                              existing_nullable=False)
