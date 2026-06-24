"""Add agent_credit to paymentmethod enum

Revision ID: 016_add_agent_credit_enum
Revises: 015_add_celery_task_id
Create Date: 2026-06-24

The PaymentMethod model defines AGENT_CREDIT = 'agent_credit' but no
migration ever added this value to the PostgreSQL enum.  Any INSERT
with payment_method='agent_credit' crashes with InvalidTextRepresentation.
"""

from typing import Union
from alembic import op

revision: str = "016_add_agent_credit_enum"
down_revision: Union[str, None] = "015_add_celery_task_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'agent_credit'")


def downgrade() -> None:
    pass
