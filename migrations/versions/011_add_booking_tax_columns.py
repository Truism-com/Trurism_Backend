"""Add tax and base_amount columns to hotel and bus bookings

Revision ID: 011_add_booking_tax_columns
Revises: 010_email_tenant_composite_unique
Create Date: 2026-05-15
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011_add_booking_tax_columns"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hotel_bookings", sa.Column("base_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("hotel_bookings", sa.Column("taxes", sa.Float(), nullable=False, server_default="0"))
    op.add_column("bus_bookings", sa.Column("base_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("bus_bookings", sa.Column("taxes", sa.Float(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("hotel_bookings", "taxes")
    op.drop_column("hotel_bookings", "base_amount")
    op.drop_column("bus_bookings", "taxes")
    op.drop_column("bus_bookings", "base_amount")
