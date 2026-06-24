"""add_tenant_id_to_wallet_tables

Revision ID: 017_add_tenant_id_to_wallet_tables
Revises: 016_add_agent_credit_enum
Create Date: 2026-06-24

"""
from alembic import op
import sqlalchemy as sa

revision = '017_add_tenant_id_to_wallet_tables'
down_revision = '016_add_agent_credit_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # wallets.tenant_id - fixes 500 on GET /wallet/
    op.add_column('wallets', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index('ix_wallets_tenant_id', 'wallets', ['tenant_id'], unique=False)
    op.create_foreign_key(
        'fk_wallets_tenant_id', 'wallets', 'tenants', ['tenant_id'], ['id']
    )

    # wallet_transactions.tenant_id
    op.add_column('wallet_transactions', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index('ix_wallet_transactions_tenant_id', 'wallet_transactions', ['tenant_id'], unique=False)
    op.create_foreign_key(
        'fk_wallet_transactions_tenant_id', 'wallet_transactions', 'tenants', ['tenant_id'], ['id']
    )

    # wallet_topup_requests.tenant_id
    op.add_column('wallet_topup_requests', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index('ix_wallet_topup_requests_tenant_id', 'wallet_topup_requests', ['tenant_id'], unique=False)
    op.create_foreign_key(
        'fk_wallet_topup_requests_tenant_id', 'wallet_topup_requests', 'tenants', ['tenant_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_wallet_topup_requests_tenant_id', 'wallet_topup_requests', type_='foreignkey')
    op.drop_index('ix_wallet_topup_requests_tenant_id', table_name='wallet_topup_requests')
    op.drop_column('wallet_topup_requests', 'tenant_id')

    op.drop_constraint('fk_wallet_transactions_tenant_id', 'wallet_transactions', type_='foreignkey')
    op.drop_index('ix_wallet_transactions_tenant_id', table_name='wallet_transactions')
    op.drop_column('wallet_transactions', 'tenant_id')

    op.drop_constraint('fk_wallets_tenant_id', 'wallets', type_='foreignkey')
    op.drop_index('ix_wallets_tenant_id', table_name='wallets')
    op.drop_column('wallets', 'tenant_id')
