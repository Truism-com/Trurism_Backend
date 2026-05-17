"""Replace global unique constraint on booking_reference with composite unique (booking_reference, tenant_id)

Revision ID: 012_composite_unique_booking_ref
Revises: 011_add_booking_tax_columns
Create Date: 2026-05-15

Bug 10 fix: booking_reference was globally unique. With multi-tenant
architecture, uniqueness should be scoped per tenant. This prevents
cross-tenant collisions from causing raw 500 errors.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_composite_unique_booking_ref'
down_revision = '011_add_booking_tax_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Replace per-column unique with composite unique constraint."""

    # FlightBooking: drop old unique, add composite
    # Use batch mode for safety with existing data
    # Use raw SQL with IF EXISTS for robustness across environments
    op.execute("""
        ALTER TABLE flight_bookings 
        DROP CONSTRAINT IF EXISTS flight_bookings_booking_reference_key
    """)
    with op.batch_alter_table('flight_bookings') as batch_op:
        batch_op.create_unique_constraint(
            'uq_flight_booking_ref_tenant',
            ['booking_reference', 'tenant_id']
        )

    # HotelBooking: drop old unique, add composite
    op.execute("""
        ALTER TABLE hotel_bookings 
        DROP CONSTRAINT IF EXISTS hotel_bookings_booking_reference_key
    """)
    with op.batch_alter_table('hotel_bookings') as batch_op:
        batch_op.create_unique_constraint(
            'uq_hotel_booking_ref_tenant',
            ['booking_reference', 'tenant_id']
        )

    # BusBooking: drop old unique, add composite
    op.execute("""
        ALTER TABLE bus_bookings 
        DROP CONSTRAINT IF EXISTS bus_bookings_booking_reference_key
    """)
    with op.batch_alter_table('bus_bookings') as batch_op:
        batch_op.create_unique_constraint(
            'uq_bus_booking_ref_tenant',
            ['booking_reference', 'tenant_id']
        )


def downgrade() -> None:
    """Revert to per-column unique constraint."""

    with op.batch_alter_table('bus_bookings') as batch_op:
        batch_op.drop_constraint('uq_bus_booking_ref_tenant', type_='unique')
        batch_op.create_unique_constraint(
            'bus_bookings_booking_reference_key',
            ['booking_reference']
        )

    with op.batch_alter_table('hotel_bookings') as batch_op:
        batch_op.drop_constraint('uq_hotel_booking_ref_tenant', type_='unique')
        batch_op.create_unique_constraint(
            'hotel_bookings_booking_reference_key',
            ['booking_reference']
        )

    with op.batch_alter_table('flight_bookings') as batch_op:
        batch_op.drop_constraint('uq_flight_booking_ref_tenant', type_='unique')
        batch_op.create_unique_constraint(
            'flight_bookings_booking_reference_key',
            ['booking_reference']
        )
