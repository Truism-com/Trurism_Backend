"""Add API keys table and salesperson tracking to bookings

Revision ID: 001
Revises: 
Create Date: 2025-01-15

This migration adds:
1. API keys table for partner integrations
2. Salesperson tracking (created_by_id) to booking tables
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add API keys table and salesperson tracking columns.
    """
    # Create API keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scopes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    
    # Create indexes for API keys
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False)
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'], unique=False)
    
    # Add created_by_id to flight_bookings
    op.add_column('flight_bookings', 
        sa.Column('created_by_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_flight_bookings_created_by_id',
        'flight_bookings', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_flight_bookings_created_by_id', 'flight_bookings', ['created_by_id'], unique=False)
    
    # Add created_by_id to hotel_bookings
    op.add_column('hotel_bookings',
        sa.Column('created_by_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_hotel_bookings_created_by_id',
        'hotel_bookings', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_hotel_bookings_created_by_id', 'hotel_bookings', ['created_by_id'], unique=False)
    
    # Add created_by_id to bus_bookings
    op.add_column('bus_bookings',
        sa.Column('created_by_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_bus_bookings_created_by_id',
        'bus_bookings', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_bus_bookings_created_by_id', 'bus_bookings', ['created_by_id'], unique=False)


def downgrade() -> None:
    """
    Remove API keys table and salesperson tracking columns.
    """
    # Remove created_by_id from bus_bookings
    op.drop_index('ix_bus_bookings_created_by_id', table_name='bus_bookings')
    op.drop_constraint('fk_bus_bookings_created_by_id', 'bus_bookings', type_='foreignkey')
    op.drop_column('bus_bookings', 'created_by_id')
    
    # Remove created_by_id from hotel_bookings
    op.drop_index('ix_hotel_bookings_created_by_id', table_name='hotel_bookings')
    op.drop_constraint('fk_hotel_bookings_created_by_id', 'hotel_bookings', type_='foreignkey')
    op.drop_column('hotel_bookings', 'created_by_id')
    
    # Remove created_by_id from flight_bookings
    op.drop_index('ix_flight_bookings_created_by_id', table_name='flight_bookings')
    op.drop_constraint('fk_flight_bookings_created_by_id', 'flight_bookings', type_='foreignkey')
    op.drop_column('flight_bookings', 'created_by_id')
    
    # Drop API keys indexes and table
    op.drop_index('ix_api_keys_is_active', table_name='api_keys')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')
