"""
Pricing & Commercials Engine Schemas

Pydantic schemas for pricing validation and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.pricing.models import ServiceType, MarkupType, UserType, DiscountType


# =============================================================================
# MARKUP RULE SCHEMAS
# =============================================================================

class MarkupRuleBase(BaseModel):
    """Base markup rule schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    
    # Service targeting
    service_type: ServiceType = ServiceType.ALL
    
    # Supplier targeting
    supplier_code: Optional[str] = Field(None, max_length=50)
    supplier_name: Optional[str] = Field(None, max_length=200)
    
    # Flight-specific
    airline_code: Optional[str] = Field(None, max_length=10)
    origin_city: Optional[str] = Field(None, max_length=10)
    destination_city: Optional[str] = Field(None, max_length=10)
    origin_country: Optional[str] = Field(None, max_length=10)
    destination_country: Optional[str] = Field(None, max_length=10)
    cabin_class: Optional[str] = Field(None, max_length=20)
    fare_type: Optional[str] = Field(None, max_length=50)
    
    # Hotel-specific
    hotel_star_rating: Optional[int] = Field(None, ge=1, le=5)
    hotel_chain: Optional[str] = Field(None, max_length=100)
    
    # User type
    user_type: UserType = UserType.ALL
    agent_id: Optional[int] = None
    
    # Markup configuration
    markup_type: MarkupType = MarkupType.PERCENTAGE
    markup_value: Decimal = Field(..., ge=0)
    
    # Constraints
    min_markup: Optional[Decimal] = Field(None, ge=0)
    max_markup: Optional[Decimal] = Field(None, ge=0)
    min_fare: Optional[Decimal] = Field(None, ge=0)
    max_fare: Optional[Decimal] = Field(None, ge=0)
    
    # Applicability
    apply_on_net_fare: bool = True
    apply_on_taxes: bool = False
    
    # Priority
    priority: int = Field(0, ge=0)
    is_stackable: bool = False
    
    # Validity
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    
    is_active: bool = True


class MarkupRuleCreate(MarkupRuleBase):
    """Schema for creating markup rule."""
    pass


class MarkupRuleUpdate(BaseModel):
    """Schema for updating markup rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    service_type: Optional[ServiceType] = None
    supplier_code: Optional[str] = None
    airline_code: Optional[str] = None
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    cabin_class: Optional[str] = None
    user_type: Optional[UserType] = None
    markup_type: Optional[MarkupType] = None
    markup_value: Optional[Decimal] = Field(None, ge=0)
    min_markup: Optional[Decimal] = Field(None, ge=0)
    max_markup: Optional[Decimal] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=0)
    is_stackable: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None


class MarkupRuleResponse(MarkupRuleBase):
    """Markup rule response."""
    id: int
    tenant_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MarkupRuleListResponse(BaseModel):
    """List of markup rules."""
    items: List[MarkupRuleResponse]
    total: int


# =============================================================================
# DISCOUNT RULE SCHEMAS
# =============================================================================

class DiscountRuleBase(BaseModel):
    """Base discount rule schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    
    # Service targeting
    service_type: ServiceType = ServiceType.ALL
    
    # Supplier targeting
    supplier_code: Optional[str] = Field(None, max_length=50)
    airline_code: Optional[str] = Field(None, max_length=10)
    
    # User type
    user_type: UserType = UserType.ALL
    agent_ids: Optional[List[int]] = None
    
    # Discount configuration
    discount_type: DiscountType = DiscountType.PERCENTAGE
    discount_value: Decimal = Field(..., ge=0)
    
    # Caps
    max_discount: Optional[Decimal] = Field(None, ge=0)
    min_booking_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Usage limits
    usage_limit_total: Optional[int] = Field(None, ge=0)
    usage_limit_per_user: Optional[int] = Field(None, ge=0)
    
    # Applicability
    apply_on_markup: bool = False
    
    # Priority
    priority: int = Field(0, ge=0)
    
    # Validity
    valid_from: date
    valid_to: date
    travel_from: Optional[date] = None
    travel_to: Optional[date] = None
    
    is_active: bool = True
    
    @field_validator('valid_to')
    @classmethod
    def validate_dates(cls, v, info):
        if info.data.get('valid_from') and v < info.data['valid_from']:
            raise ValueError('valid_to must be after valid_from')
        return v


class DiscountRuleCreate(DiscountRuleBase):
    """Schema for creating discount rule."""
    pass


class DiscountRuleUpdate(BaseModel):
    """Schema for updating discount rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    service_type: Optional[ServiceType] = None
    supplier_code: Optional[str] = None
    airline_code: Optional[str] = None
    user_type: Optional[UserType] = None
    agent_ids: Optional[List[int]] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(None, ge=0)
    max_discount: Optional[Decimal] = Field(None, ge=0)
    min_booking_amount: Optional[Decimal] = Field(None, ge=0)
    usage_limit_total: Optional[int] = Field(None, ge=0)
    usage_limit_per_user: Optional[int] = Field(None, ge=0)
    apply_on_markup: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    travel_from: Optional[date] = None
    travel_to: Optional[date] = None
    is_active: Optional[bool] = None


class DiscountRuleResponse(DiscountRuleBase):
    """Discount rule response."""
    id: int
    tenant_id: int
    usage_count: int = 0
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DiscountRuleListResponse(BaseModel):
    """List of discount rules."""
    items: List[DiscountRuleResponse]
    total: int


class DiscountValidationResult(BaseModel):
    """Result of discount validation."""
    is_valid: bool
    discount_amount: Decimal = Decimal(0)
    error_message: Optional[str] = None
    discount_rule: Optional[DiscountRuleResponse] = None


# =============================================================================
# CONVENIENCE FEE SLAB SCHEMAS
# =============================================================================

class ConvenienceFeeSlabBase(BaseModel):
    """Base convenience fee slab schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    
    # Service targeting
    service_type: ServiceType = ServiceType.ALL
    
    # Payment mode
    payment_mode: str = Field(..., max_length=50)
    card_type: Optional[str] = Field(None, max_length=50)
    
    # User type
    user_type: UserType = UserType.ALL
    
    # Amount range
    min_amount: Decimal = Field(Decimal(0), ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Fee configuration
    fee_type: str = Field("percentage", pattern="^(fixed|percentage)$")
    fee_value: Decimal = Field(..., ge=0)
    
    # Fee limits
    min_fee: Optional[Decimal] = Field(None, ge=0)
    max_fee: Optional[Decimal] = Field(None, ge=0)
    
    # Tax
    apply_gst: bool = True
    gst_rate: Decimal = Field(Decimal("18.00"), ge=0, le=100)
    
    # Priority
    priority: int = Field(0, ge=0)
    
    # Validity
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    
    is_active: bool = True


class ConvenienceFeeSlabCreate(ConvenienceFeeSlabBase):
    """Schema for creating fee slab."""
    pass


class ConvenienceFeeSlabUpdate(BaseModel):
    """Schema for updating fee slab."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    service_type: Optional[ServiceType] = None
    payment_mode: Optional[str] = Field(None, max_length=50)
    card_type: Optional[str] = None
    user_type: Optional[UserType] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    fee_type: Optional[str] = Field(None, pattern="^(fixed|percentage)$")
    fee_value: Optional[Decimal] = Field(None, ge=0)
    min_fee: Optional[Decimal] = Field(None, ge=0)
    max_fee: Optional[Decimal] = Field(None, ge=0)
    apply_gst: Optional[bool] = None
    gst_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    priority: Optional[int] = Field(None, ge=0)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None


class ConvenienceFeeSlabResponse(ConvenienceFeeSlabBase):
    """Fee slab response."""
    id: int
    tenant_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConvenienceFeeSlabListResponse(BaseModel):
    """List of fee slabs."""
    items: List[ConvenienceFeeSlabResponse]
    total: int


# =============================================================================
# PRICE CALCULATION SCHEMAS
# =============================================================================

class PriceCalculationRequest(BaseModel):
    """Request for price calculation."""
    service_type: ServiceType
    supplier_code: Optional[str] = None
    
    # Base pricing
    base_fare: Decimal = Field(..., ge=0)
    taxes: Decimal = Field(Decimal(0), ge=0)
    
    # Flight-specific
    airline_code: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    cabin_class: Optional[str] = None
    
    # Hotel-specific
    hotel_star_rating: Optional[int] = None
    hotel_chain: Optional[str] = None
    
    # User context
    user_type: UserType = UserType.B2C
    agent_id: Optional[int] = None
    
    # Discount code
    discount_code: Optional[str] = None
    
    # Payment info (for convenience fee)
    payment_mode: Optional[str] = None
    card_type: Optional[str] = None
    
    # Travel date (for discount validation)
    travel_date: Optional[date] = None
    
    # Session tracking
    session_id: Optional[str] = None


class MarkupBreakdown(BaseModel):
    """Markup breakdown details."""
    rule_id: int
    rule_name: str
    markup_type: str
    markup_value: Decimal
    calculated_markup: Decimal


class DiscountBreakdown(BaseModel):
    """Discount breakdown details."""
    rule_id: int
    rule_name: str
    code: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    calculated_discount: Decimal


class FeeBreakdown(BaseModel):
    """Convenience fee breakdown."""
    slab_id: int
    slab_name: str
    fee_type: str
    fee_value: Decimal
    calculated_fee: Decimal
    gst_amount: Decimal
    total_fee: Decimal


class PriceCalculationResponse(BaseModel):
    """Response for price calculation."""
    # Input
    base_fare: Decimal
    taxes: Decimal
    
    # Markup
    total_markup: Decimal
    fare_after_markup: Decimal
    markup_breakdown: List[MarkupBreakdown] = []
    
    # Discount
    total_discount: Decimal
    fare_after_discount: Decimal
    discount_breakdown: List[DiscountBreakdown] = []
    
    # Convenience fee
    convenience_fee: Decimal
    convenience_fee_gst: Decimal
    total_convenience_fee: Decimal
    fee_breakdown: Optional[FeeBreakdown] = None
    
    # Final
    subtotal: Decimal  # base + taxes + markup - discount
    grand_total: Decimal  # subtotal + convenience fee
    
    # Summary
    you_save: Decimal
    effective_margin: Decimal
    
    # Metadata
    calculated_at: datetime


# =============================================================================
# BULK OPERATIONS
# =============================================================================

class BulkMarkupUpdate(BaseModel):
    """Bulk update markup rules."""
    rule_ids: List[int]
    updates: MarkupRuleUpdate


class BulkDiscountUpdate(BaseModel):
    """Bulk update discount rules."""
    rule_ids: List[int]
    updates: DiscountRuleUpdate
