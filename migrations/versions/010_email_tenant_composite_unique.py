"""Replace global email uniqueness with composite (email, tenant_id) unique index.

The original schema has unique=True on users.email, which prevents the same
email from appearing in two different tenants.  For a white-label platform
this is incorrect: john@gmail.com under Agency A and Agency B must coexist.

Revision ID: 010
Revises: 009
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop the unique index on email.  In this schema the uniqueness was
    #    enforced via a UNIQUE INDEX (ix_users_email), not a separate constraint.
    op.drop_index('ix_users_email', table_name='users')

    # 2. Create a composite unique index on (email, tenant_id).
    #    NULLs in tenant_id do NOT compare equal in Postgres, so NULL + same
    #    email will still pass.  That is acceptable for the single-tenant
    #    bootstrap case.  When multi-tenant goes live, every user must have a
    #    tenant_id.
    op.create_index(
        'uq_users_email_tenant',
        'users',
        ['email', 'tenant_id'],
        unique=True,
    )

    # 3. Keep a non-unique index on email alone for fast lookups.
    op.create_index('ix_users_email', 'users', ['email'], unique=False)


def downgrade() -> None:
    # Reverse: drop the non-unique and composite indexes, restore original unique index.
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('uq_users_email_tenant', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
