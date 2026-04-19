"""Add token blacklist table for logout functionality

Revision ID: 005
Revises: 004_merge_heads
Create Date: 2026-04-17

Creates:
- token_blacklist table for revoking tokens when Redis is unavailable
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # token_blacklist table
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("token_jti", sa.String(length=500), nullable=False, unique=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("blacklisted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("token_blacklist")
