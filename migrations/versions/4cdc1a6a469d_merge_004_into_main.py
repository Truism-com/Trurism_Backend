"""merge_004_into_main

Revision ID: 4cdc1a6a469d
Revises: 004_add_coupons, 004_merge_heads
Create Date: 2026-04-22 17:48:26.253089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cdc1a6a469d'
down_revision = ('004_add_coupons', '004_merge_heads')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
