"""Add superadmin role to UserRole enum

Revision ID: 006
Revises: 005
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add 'superadmin' to the userrole ENUM
    # Note: ALTER TYPE ADD VALUE cannot be executed inside a transaction block in PostgreSQL.
    # Therefore, we need to commit the current transaction before executing it.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'superadmin'")

def downgrade() -> None:
    # PostgreSQL does not easily support removing values from an ENUM type.
    # We leave the downgrade as a no-op for enum values.
    pass
