"""
Settings Database Models

SQLAlchemy models for admin settings and staff management.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Enum, Index, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List
import enum

from app.core.database import Base


class PaymentMode(str, enum.Enum):
    """Payment modes for convenience fees."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    NET_BANKING = "net_banking"
    UPI = "upi"
    WALLET = "wallet"
    EMI = "emi"
    PAY_LATER = "pay_later"
    RAZORPAY = "razorpay"


class ConvenienceFee(Base):
    """
    Convenience fees configuration by payment mode and service type.
    """
    __tablename__ = "convenience_fees"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Applicability
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)  # flights, hotels, holidays, etc. or 'all'
    payment_mode: Mapped[PaymentMode] = mapped_column(
        Enum(PaymentMode),
        nullable=False
    )
    
    # Fee structure
    fee_type: Mapped[str] = mapped_column(String(20), default="percentage")  # percentage, fixed, both
    percentage: Mapped[float] = mapped_column(Float, default=0)
    fixed_amount: Mapped[float] = mapped_column(Float, default=0)
    min_fee: Mapped[float] = mapped_column(Float, default=0)  # Minimum fee
    max_fee: Mapped[Optional[float]] = mapped_column(Float)  # Cap on fee
    
    # GST on convenience fee
    gst_percentage: Mapped[float] = mapped_column(Float, default=18.0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Tenant (for white-label)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fee_service_payment', 'service_type', 'payment_mode'),
        Index('idx_fee_tenant', 'tenant_id'),
    )


class StaffRole(Base):
    """
    Staff roles with permission sets.
    """
    __tablename__ = "staff_roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Permissions (JSON array of permission codes)
    permissions: Mapped[Optional[str]] = mapped_column(JSON)
    
    # System role (cannot be deleted)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Tenant
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    staff_members: Mapped[List["StaffMember"]] = relationship("StaffMember", back_populates="role")
    
    __table_args__ = (
        Index('idx_role_tenant', 'tenant_id'),
    )


class StaffPermission(Base):
    """
    Available permissions in the system.
    """
    __tablename__ = "staff_permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Grouping
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # bookings, users, settings, etc.
    
    # Order for display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_permission_module', 'module'),
    )


class StaffMember(Base):
    """
    Staff members with role-based access.
    """
    __tablename__ = "staff_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Link to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Staff info
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    designation: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Role
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff_roles.id"), nullable=False)
    
    # Additional permissions (beyond role)
    additional_permissions: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Restrictions
    restricted_permissions: Mapped[Optional[str]] = mapped_column(JSON)  # Denied permissions
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Access control
    can_access_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    ip_whitelist: Mapped[Optional[str]] = mapped_column(JSON)  # Allowed IPs
    
    # Tenant
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    role: Mapped["StaffRole"] = relationship("StaffRole", back_populates="staff_members")
    
    __table_args__ = (
        Index('idx_staff_user', 'user_id'),
        Index('idx_staff_role', 'role_id'),
        Index('idx_staff_tenant', 'tenant_id'),
    )


class SystemSetting(Base):
    """
    System-wide settings and configurations.
    """
    __tablename__ = "system_settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Setting key
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Value (stored as JSON for flexibility)
    value: Mapped[Optional[str]] = mapped_column(JSON)
    
    # Type hint for parsing
    value_type: Mapped[str] = mapped_column(String(20), default="string")  # string, number, boolean, json
    
    # Metadata
    category: Mapped[str] = mapped_column(String(50), default="general")
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Visibility
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # Visible to frontend
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Tenant (for tenant-specific settings)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    updated_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_setting_key_tenant', 'key', 'tenant_id', unique=True),
        Index('idx_setting_category', 'category'),
    )


# Import for type hints
from app.auth.models import User
