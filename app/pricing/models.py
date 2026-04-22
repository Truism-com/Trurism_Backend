"""
Pricing & Commercials Engine Models

Database models for markup rules, discounts, and convenience fee slabs.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Numeric, Enum as SQLEnum, JSON, Date
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import enum

from app.core.database import Base


class ServiceType(str, enum.Enum):
    """Service/product types for pricing."""
    FLIGHT = "flight"
    HOTEL = "hotel"
    PACKAGE = "package"
    ACTIVITY = "activity"
    TRANSFER = "transfer"
    VISA = "visa"
    INSURANCE = "insurance"
    ALL = "all"


class MarkupType(str, enum.Enum):
    """Type of markup."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class UserType(str, enum.Enum):
    """User type for differentiated pricing."""
    B2B = "b2b"  # Agents
    B2C = "b2c"  # Direct customers
    CORPORATE = "corporate"
    ALL = "all"


class DiscountType(str, enum.Enum):
    """Type of discount."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class PricingMarkupRule(Base):
    """Advanced markup rule for pricing engine calculations."""
    
    __tablename__ = "pricing_markup_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Rule identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Service targeting
    service_type: Mapped[ServiceType] = mapped_column(
        SQLEnum(ServiceType), nullable=False, default=ServiceType.ALL
    )
    
    # Supplier targeting
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Flight-specific targeting
    airline_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    origin_city: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    destination_city: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    origin_country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    destination_country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    cabin_class: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fare_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Hotel-specific targeting
    hotel_star_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hotel_chain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # User type targeting
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType), nullable=False, default=UserType.ALL
    )
    agent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Markup configuration
    markup_type: Mapped[MarkupType] = mapped_column(
        SQLEnum(MarkupType), nullable=False, default=MarkupType.PERCENTAGE
    )
    markup_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    
    # Min/Max constraints
    min_markup: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    max_markup: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Fare range targeting
    min_fare: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    max_fare: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    
    # Applicability
    apply_on_net_fare: Mapped[bool] = mapped_column(Boolean, default=True)
    apply_on_taxes: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Priority and stacking
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_stackable: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Validity
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<PricingMarkupRule {self.name}: {self.markup_type.value}={self.markup_value}>"


class DiscountRule(Base):
    """Discount rule for promotions and agent discounts."""
    
    __tablename__ = "discount_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Rule identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    
    # Service targeting
    service_type: Mapped[ServiceType] = mapped_column(
        SQLEnum(ServiceType), nullable=False, default=ServiceType.ALL
    )
    
    # Supplier targeting
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    airline_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # User type targeting
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType), nullable=False, default=UserType.ALL
    )
    agent_ids: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)  # List of agent IDs
    
    # Discount configuration
    discount_type: Mapped[DiscountType] = mapped_column(
        SQLEnum(DiscountType), nullable=False, default=DiscountType.PERCENTAGE
    )
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    
    # Caps
    max_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    min_booking_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    
    # Usage limits
    usage_limit_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_limit_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Applicability
    apply_on_markup: Mapped[bool] = mapped_column(Boolean, default=False)  # After markup calculation
    
    # Priority
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Validity
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Travel date restrictions
    travel_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    travel_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DiscountRule {self.name}: {self.discount_type.value}={self.discount_value}>"


class ConvenienceFeeSlab(Base):
    """Convenience fee slabs by amount range and payment mode."""
    
    __tablename__ = "convenience_fee_slabs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Service targeting
    service_type: Mapped[ServiceType] = mapped_column(
        SQLEnum(ServiceType), nullable=False, default=ServiceType.ALL
    )
    
    # Payment mode targeting
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=False)  # credit_card, debit_card, netbanking, upi, wallet
    card_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # visa, mastercard, amex
    
    # User type targeting
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType), nullable=False, default=UserType.ALL
    )
    
    # Amount range (slab)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    max_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)  # null for unlimited
    
    # Fee configuration
    fee_type: Mapped[str] = mapped_column(String(20), default="percentage")  # fixed, percentage
    fee_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    
    # Min/Max fee
    min_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    max_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Tax configuration
    apply_gst: Mapped[bool] = mapped_column(Boolean, default=True)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=18.00)
    
    # Priority for overlapping slabs
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Validity
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ConvenienceFeeSlab {self.name}: {self.min_amount}-{self.max_amount}>"


class PriceAuditLog(Base):
    """Audit log for price calculations."""
    
    __tablename__ = "price_audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    # Reference
    booking_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    booking_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # User
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    user_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Input
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    base_fare: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    taxes: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    
    # Applied rules
    markup_rules_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    discount_rules_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    fee_slabs_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Output
    total_markup: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    convenience_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    final_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    
    # Metadata
    calculation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PriceAuditLog {self.id}: {self.base_fare} -> {self.final_amount}>"

class CouponServiceType(str, enum.Enum):
    """Service type supported by coupons."""
    FLIGHT = "flight"
    HOTEL = "hotel"
    BUS = "bus"
    ALL = "all"
    
class Coupon(Base):
    """Customer-facting promo/coupon codes."""
    
    __tablename__ = "coupons"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), index=True)
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType), nullable=False, default=DiscountType.PERCENTAGE)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    
    min_order_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    max_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12,2), nullable=True)
    
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False)
    valid_untill: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    service_type: Mapped[CouponServiceType] = mapped_column(SQLEnum(CouponServiceType), nullable=False, default=CouponServiceType.ALL    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Coupon {self.code}: {self.discount_type.value} = {self.discount_value}>"