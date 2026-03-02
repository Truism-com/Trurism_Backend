"""
Merge heads: unify two parallel migration chains

Revision ID: 004_merge_heads
Revises: 003_add_dashboard_pricing_company, 003_add_wallet_system
Create Date: 2026-02-27
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '004_merge_heads'
down_revision = ('003_add_dashboard_pricing_company', '003_add_wallet_system')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Nothing to do -- just merging two heads into one."""
    pass


def downgrade() -> None:
    """Nothing to undo."""
    pass
