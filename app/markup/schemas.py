"""
Markup Pydantic Schemas

Request/Response schemas for markup management endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.markup.models import ServiceType, MarkupType, RouteType


class MarkupRuleBase(BaseModel):
    """Base markup rule schema."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    service_type: ServiceType
    markup_type: MarkupType
    value: float = Field(..., gt=0, description="Markup value (INR or %)")
    priority: int = Field(default=0, description="Higher priority rules apply first")
    agent_commission_percentage: float = Field(default=0.0, ge=0, le=100)


class MarkupRuleCreate(MarkupRuleBase):
    """Schema for creating markup rule."""
    tenant_id: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class MarkupRuleUpdate(BaseModel):
    """Schema for updating markup rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    markup_type: Optional[MarkupType] = None
    value: Optional[float] = Field(None, gt=0)
    priority: Optional[int] = None
    agent_commission_percentage: Optional[float] = Field(None, ge=0, le=100)
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class MarkupRuleResponse(BaseModel):
    """Markup rule response."""
    id: int
    name: str
    description: Optional[str]
    tenant_id: Optional[int]
    service_type: ServiceType
    markup_type: MarkupType
    value: float
    priority: int
    conditions: Dict[str, Any]
    agent_commission_percentage: float
    is_active: bool
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MarkupRuleListResponse(BaseModel):
    """Paginated list of markup rules."""
    rules: list[MarkupRuleResponse]
    total: int
    page: int
    size: int


class PriceBreakdown(BaseModel):
    """Price breakdown with markup calculation."""
    base_price: float = Field(..., description="Original supplier price")
    markup_amount: float = Field(..., description="Total markup added")
    admin_margin: float = Field(..., description="Admin's profit margin")
    agent_commission: float = Field(..., description="Agent's commission")
    taxes: float = Field(..., description="Taxes (GST, etc.)")
    total_price: float = Field(..., description="Final price to customer")
    applied_rules: list[str] = Field(default_factory=list, description="List of applied rule names")


class MarkupCalculationRequest(BaseModel):
    """Request to calculate markup for given parameters."""
    service_type: ServiceType
    base_price: float = Field(..., gt=0)
    search_params: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[int] = None
