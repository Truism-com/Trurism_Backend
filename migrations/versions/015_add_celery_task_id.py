"""Add celery_task_id and airiq_booking_id to flight_bookings

Revision ID: 015_add_celery_task_id
Revises: 014_add_pnr_to_flight_booking
Create Date: 2026-06-15
"""

from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "015_add_celery_task_id"
down_revision: Union[str, None] = "014_add_pnr_to_flight_booking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "flight_bookings",
        sa.Column("celery_task_id", sa.String(100), nullable=True)
    )
    op.add_column(
        "flight_bookings",
        sa.Column("airiq_booking_id", sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("flight_bookings", "airiq_booking_id")
    op.drop_column("flight_bookings", "celery_task_id")
