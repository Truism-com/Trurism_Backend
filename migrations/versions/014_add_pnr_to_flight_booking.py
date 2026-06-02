"""Add pnr column to flight_bookings

Revision ID: 014_add_pnr_to_flight_booking
Revises: 013_convert_float_to_numeric
Create Date: 2026-06-02
"""

from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "014_add_pnr_to_flight_booking"
down_revision: Union[str, None] = "013_convert_float_to_numeric"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "flight_bookings",
        sa.Column("pnr", sa.String(10), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("flight_bookings", "pnr")