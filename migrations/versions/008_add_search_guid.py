"""Add search_guid to flight_bookings

Revision ID: 008
Revises: 007
Create Date: 2026-04-28 21:58:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add search_guid column to flight_bookings table to store the XML.Agency identifier
    op.add_column('flight_bookings', sa.Column('search_guid', sa.String(length=100), nullable=True))

def downgrade() -> None:
    op.drop_column('flight_bookings', 'search_guid')
