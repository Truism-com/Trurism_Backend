"""Convert Float columns to Numeric(14,2) for monetary values

Revision ID: 013_convert_float_to_numeric
Revises: 012_composite_unique_booking_ref
Create Date: 2026-05-15

Converts all monetary Float columns to Numeric(14,2) Decimal across
wallet, payments, and booking models to prevent floating-point precision
drift and ensure accurate financial calculations.

Idempotent: skips columns that do not exist or are already Numeric.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013_convert_float_to_numeric'
down_revision = '012_composite_unique_booking_ref'
branch_labels = None
depends_on = None


def _col_is_float(conn, table: str, column: str) -> bool:
    """Return True if column exists and is a float/double precision type."""
    result = conn.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    if result is None:
        return False
    return result[0].lower() in ("real", "double precision", "float", "float4", "float8")


def _alter_if_float(conn, table: str, column: str) -> None:
    """ALTER column to Numeric(14,2) only if it currently exists as a float."""
    if _col_is_float(conn, table, column):
        conn.execute(
            sa.text(
                f"ALTER TABLE {table} ALTER COLUMN {column} TYPE NUMERIC(14, 2)"
            )
        )


def upgrade() -> None:
    """Convert Float columns to Numeric(14,2) for monetary values."""
    conn = op.get_bind()

    # wallets
    for col in ("balance", "hold_amount", "credit_limit", "credit_used",
                "daily_transaction_limit", "min_balance", "total_credited", "total_debited"):
        _alter_if_float(conn, "wallets", col)

    # payment_transactions
    for col in ("amount", "base_amount", "convenience_fee", "taxes"):
        _alter_if_float(conn, "payment_transactions", col)

    # flight_bookings
    for col in ("total_amount", "base_fare", "taxes", "refund_amount"):
        _alter_if_float(conn, "flight_bookings", col)

    # hotel_bookings
    for col in ("total_amount", "room_rate", "base_amount", "taxes", "refund_amount"):
        _alter_if_float(conn, "hotel_bookings", col)

    # bus_bookings
    for col in ("total_amount", "fare_per_passenger", "base_amount", "taxes", "refund_amount"):
        _alter_if_float(conn, "bus_bookings", col)


def downgrade() -> None:
    """Revert Numeric(14,2) columns back to Float."""
    conn = op.get_bind()

    tables_cols = {
        "bus_bookings": ("total_amount", "fare_per_passenger", "base_amount", "taxes", "refund_amount"),
        "hotel_bookings": ("total_amount", "room_rate", "base_amount", "taxes", "refund_amount"),
        "flight_bookings": ("total_amount", "base_fare", "taxes", "refund_amount"),
        "payment_transactions": ("amount", "base_amount", "convenience_fee", "taxes"),
        "wallets": ("balance", "hold_amount", "credit_limit", "credit_used",
                    "daily_transaction_limit", "min_balance", "total_credited", "total_debited"),
    }
    for table, cols in tables_cols.items():
        for col in cols:
            result = conn.execute(
                sa.text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = :t AND column_name = :c"
                ),
                {"t": table, "c": col},
            ).fetchone()
            if result:
                conn.execute(
                    sa.text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE DOUBLE PRECISION")
                )
