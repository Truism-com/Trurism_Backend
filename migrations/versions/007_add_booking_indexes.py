"""Add indexes on booking query columns

Revision ID: 007
Revises: 006
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Flight Bookings Indexes
    op.create_index('ix_flight_bookings_user_id', 'flight_bookings', ['user_id'], unique=False)
    op.create_index('ix_flight_bookings_created_at', 'flight_bookings', ['created_at'], unique=False)
    
    # Hotel Bookings Indexes
    op.create_index('ix_hotel_bookings_user_id', 'hotel_bookings', ['user_id'], unique=False)
    op.create_index('ix_hotel_bookings_created_at', 'hotel_bookings', ['created_at'], unique=False)
    
    # Bus Bookings Indexes
    op.create_index('ix_bus_bookings_user_id', 'bus_bookings', ['user_id'], unique=False)
    op.create_index('ix_bus_bookings_created_at', 'bus_bookings', ['created_at'], unique=False)

def downgrade() -> None:
    # Flight Bookings Indexes
    op.drop_index('ix_flight_bookings_user_id', table_name='flight_bookings')
    op.drop_index('ix_flight_bookings_created_at', table_name='flight_bookings')
    
    # Hotel Bookings Indexes
    op.drop_index('ix_hotel_bookings_user_id', table_name='hotel_bookings')
    op.drop_index('ix_hotel_bookings_created_at', table_name='hotel_bookings')
    
    # Bus Bookings Indexes
    op.drop_index('ix_bus_bookings_user_id', table_name='bus_bookings')
    op.drop_index('ix_bus_bookings_created_at', table_name='bus_bookings')
