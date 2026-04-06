"""
Company Settings Models

Models for company branding, bank accounts, business registration, and ACL.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Numeric, Enum as SQLEnum, JSON, Date, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import enum

from app.core.database import Base


# =============================================================================
# COMPANY PROFILE & BRANDING
# =============================================================================

class CompanyProfile(Base):
    """Company profile with branding settings."""
    
    __tablename__ = "company_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), unique=True, index=True)
    
    # Basic Info
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    about_us: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Branding - Logos
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_dark_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # For dark mode
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    og_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Open Graph
    
    # Branding - Colors
    primary_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="#1976D2")
    secondary_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="#FF9800")
    accent_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Contact Information
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    toll_free: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    whatsapp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Social Media
    website_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    facebook_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    instagram_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    youtube_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # SEO Settings
    meta_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_analytics_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    facebook_pixel_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Email Settings
    smtp_host: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smtp_username: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    smtp_password: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email_from_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email_from_address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Timezone & Currency
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    default_currency: Mapped[str] = mapped_column(String(10), default="INR")
    date_format: Mapped[str] = mapped_column(String(20), default="DD/MM/YYYY")
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<CompanyProfile {self.company_name}>"


# =============================================================================
# BANK ACCOUNTS
# =============================================================================

class BankAccountType(str, enum.Enum):
    """Bank account type."""
    SAVINGS = "savings"
    CURRENT = "current"
    OVERDRAFT = "overdraft"


class BankAccount(Base):
    """Bank accounts for agent wallet top-ups and payments."""
    
    __tablename__ = "bank_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Bank Details
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    branch_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_name: Mapped[str] = mapped_column(String(300), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    account_type: Mapped[BankAccountType] = mapped_column(
        SQLEnum(BankAccountType), default=BankAccountType.CURRENT
    )
    
    # IFSC/SWIFT
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # India
    swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # International
    iban: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    routing_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # UPI
    upi_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upi_qr_code_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Purpose
    purpose: Mapped[str] = mapped_column(String(100), default="wallet_topup")  # wallet_topup, refund, payout
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Display settings
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BankAccount {self.bank_name} - {self.account_number[-4:]}>"


# =============================================================================
# BUSINESS REGISTRATION
# =============================================================================

class BusinessRegistration(Base):
    """Business registration and legal documents."""
    
    __tablename__ = "business_registrations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), unique=True, index=True)
    
    # GST Details (India)
    gst_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gst_state_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    gst_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # regular, composition
    gst_certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # PAN (India)
    pan_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pan_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    pan_card_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Company Registration
    cin_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Corporate Identity Number
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    incorporation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    incorporation_certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # IATA/Travel License
    iata_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    iata_certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    travel_license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    travel_license_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    travel_license_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # TAN (Tax Deduction Account Number - India)
    tan_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Additional registrations
    msme_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    msme_certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Insurance
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    insurance_certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Custom fields for other registrations
    custom_registrations: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<BusinessRegistration tenant={self.tenant_id}>"


# =============================================================================
# ACCESS CONTROL LIST (ACL) - ENHANCED
# =============================================================================

class ACLModule(Base):
    """System modules for granular ACL."""
    
    __tablename__ = "acl_modules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Module identification
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hierarchy
    parent_module_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("acl_modules.id"), nullable=True
    )
    
    # Icon and ordering
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    permissions: Mapped[List["ACLPermission"]] = relationship(
        "ACLPermission", back_populates="module"
    )
    children: Mapped[List["ACLModule"]] = relationship("ACLModule")
    
    def __repr__(self):
        return f"<ACLModule {self.name}>"


class ACLPermission(Base):
    """Permissions for each module."""
    
    __tablename__ = "acl_permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Module reference
    module_id: Mapped[int] = mapped_column(Integer, ForeignKey("acl_modules.id"), index=True)
    
    # Permission identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., view, create, edit, delete
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Permission code (module.action format)
    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)  # e.g., bookings.create
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    module: Mapped["ACLModule"] = relationship("ACLModule", back_populates="permissions")
    
    __table_args__ = (
        UniqueConstraint('module_id', 'name', name='uq_acl_permission_module_name'),
    )
    
    def __repr__(self):
        return f"<ACLPermission {self.code}>"


class ACLRole(Base):
    """Custom roles with granular permissions."""
    
    __tablename__ = "acl_roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Role identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Role type
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)  # Cannot delete
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # Assigned by default
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    role_permissions: Mapped[List["ACLRolePermission"]] = relationship(
        "ACLRolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["ACLUserRole"]] = relationship(
        "ACLUserRole", back_populates="role", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_acl_role_tenant_name'),
    )
    
    def __repr__(self):
        return f"<ACLRole {self.name}>"


class ACLRolePermission(Base):
    """Many-to-many: Role to Permission mapping."""
    
    __tablename__ = "acl_role_permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("acl_roles.id"), index=True)
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("acl_permissions.id"), index=True)
    
    # Grant type
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True)  # True = grant, False = deny
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    role: Mapped["ACLRole"] = relationship("ACLRole", back_populates="role_permissions")
    permission: Mapped["ACLPermission"] = relationship("ACLPermission")
    
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    
    def __repr__(self):
        return f"<ACLRolePermission role={self.role_id} perm={self.permission_id}>"


class ACLUserRole(Base):
    """Many-to-many: User to Role mapping."""
    
    __tablename__ = "acl_user_roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("acl_roles.id"), index=True)
    
    # Assignment metadata
    assigned_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    role: Mapped["ACLRole"] = relationship("ACLRole", back_populates="user_roles")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )
    
    def __repr__(self):
        return f"<ACLUserRole user={self.user_id} role={self.role_id}>"
