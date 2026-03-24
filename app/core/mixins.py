"""
Model Mixins

Generic mixins for database models to add common functionality:
- Tenant isolation (tenant_id)
- Timestamps (created_at, updated_at)
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr


class TenantMixin:
    """
    Mixin to add tenant isolation to models.
    
    Adds a mandatory tenant_id column and an index for performance.
    """
    
    @declared_attr
    def tenant_id(cls):
        return Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)

    @declared_attr
    def __table_args__(cls):
        # Ensure we always have an index on tenant_id for faster lookups
        return (
            Index(f"ix_{cls.__tablename__}_tenant_id", "tenant_id"),
        )


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
