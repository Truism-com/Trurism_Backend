"""Create base auth and booking tables

Revision ID: 000
Revises: None
Create Date: 2025-11-27

Creates:
- users
- refresh_tokens
- passengers
- flight_bookings
- flight_booking_passengers (association)
- hotel_bookings
- bus_bookings
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users table
    user_role_enum = sa.Enum("customer", "agent", "admin", name="userrole")
    agent_status_enum = sa.Enum("pending", "approved", "rejected", "suspended", name="agentapprovalstatus")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("role", user_role_enum, nullable=False, server_default="customer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("pan_number", sa.String(length=20), nullable=True),
        sa.Column("approval_status", agent_status_enum, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    )
    # Indexes omitted to avoid duplicate creation; rely on constraints

    # refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    # Indexes omitted; can be added later if needed

    # passengers
    passenger_type_enum = sa.Enum("ADT", "CHD", "INF", name="passengertype")
    op.create_table(
        "passengers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("type", passenger_type_enum, nullable=False),
        sa.Column("passport_number", sa.String(length=20), nullable=True),
        sa.Column("nationality", sa.String(length=3), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # enums for bookings
    booking_status_enum = sa.Enum("pending", "confirmed", "cancelled", "refunded", "expired", name="bookingstatus")
    payment_status_enum = sa.Enum("pending", "success", "failed", "refunded", "partial_refund", name="paymentstatus")
    payment_method_enum = sa.Enum("card", "upi", "net_banking", "wallet", "cash", name="paymentmethod")

    # flight_bookings
    op.create_table(
        "flight_bookings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("booking_reference", sa.String(length=20), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("offer_id", sa.String(length=50), nullable=False),
        sa.Column("airline", sa.String(length=100), nullable=False),
        sa.Column("flight_number", sa.String(length=20), nullable=False),
        sa.Column("origin", sa.String(length=3), nullable=False),
        sa.Column("destination", sa.String(length=3), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("travel_class", sa.String(length=20), nullable=False),
        sa.Column("passenger_count", sa.Integer(), nullable=False),
        sa.Column("passenger_details", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("base_fare", sa.Float(), nullable=False),
        sa.Column("taxes", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("payment_status", payment_status_enum, nullable=False, server_default="pending"),
        sa.Column("status", booking_status_enum, nullable=False, server_default="pending"),
        sa.Column("confirmation_number", sa.String(length=50), nullable=True),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("refund_amount", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    # Indexes omitted; booking_reference has unique constraint

    # association table flight_booking_passengers
    op.create_table(
        "flight_booking_passengers",
        sa.Column("booking_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("passenger_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("seat_number", sa.String(length=10), nullable=True),
        sa.Column("meal_preference", sa.String(length=50), nullable=True),
        sa.Column("special_assistance", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["flight_bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["passenger_id"], ["passengers.id"], ondelete="CASCADE"),
    )

    # hotel_bookings
    op.create_table(
        "hotel_bookings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("booking_reference", sa.String(length=20), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("hotel_id", sa.String(length=50), nullable=False),
        sa.Column("hotel_name", sa.String(length=255), nullable=False),
        sa.Column("hotel_address", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("checkin_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checkout_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False),
        sa.Column("rooms", sa.Integer(), nullable=False),
        sa.Column("adults", sa.Integer(), nullable=False),
        sa.Column("children", sa.Integer(), nullable=False),
        sa.Column("guest_details", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("room_rate", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("payment_status", payment_status_enum, nullable=False, server_default="pending"),
        sa.Column("status", booking_status_enum, nullable=False, server_default="pending"),
        sa.Column("confirmation_number", sa.String(length=50), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("refund_amount", sa.Float(), nullable=True),
        sa.Column("cancellation_policy", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    # bus_bookings
    op.create_table(
        "bus_bookings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("booking_reference", sa.String(length=20), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("bus_id", sa.String(length=50), nullable=False),
        sa.Column("operator", sa.String(length=100), nullable=False),
        sa.Column("bus_type", sa.String(length=50), nullable=False),
        sa.Column("origin", sa.String(length=100), nullable=False),
        sa.Column("destination", sa.String(length=100), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("travel_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("passengers", sa.Integer(), nullable=False),
        sa.Column("seat_numbers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("passenger_details", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("fare_per_passenger", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("payment_status", payment_status_enum, nullable=False, server_default="pending"),
        sa.Column("status", booking_status_enum, nullable=False, server_default="pending"),
        sa.Column("confirmation_number", sa.String(length=50), nullable=True),
        sa.Column("boarding_point", sa.String(length=255), nullable=True),
        sa.Column("dropping_point", sa.String(length=255), nullable=True),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("refund_amount", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("bus_bookings")
    op.drop_table("hotel_bookings")
    op.drop_table("flight_booking_passengers")
    op.drop_table("flight_bookings")
    op.drop_table("passengers")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS agentapprovalstatus")
    op.execute("DROP TYPE IF EXISTS passengertype")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS paymentmethod")
