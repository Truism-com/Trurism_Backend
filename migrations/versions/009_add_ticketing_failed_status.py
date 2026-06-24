"""Add ticketing_failed value to bookingstatus enum

Revision ID: 009
Revises: 008
Create Date: 2026-04-28 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'ticketing_failed'")


def downgrade() -> None:
    # Postgres does not support removing enum values natively.
    # Downgrade is a no-op; the value becomes unused when reverting the code.
    pass
