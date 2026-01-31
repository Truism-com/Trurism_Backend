"""
Markup Database Models

This module defines database models for markup and commission management:
- Markup rules for services
- Commission calculation
- Rule priority and conditions
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base


class ServiceType(str, enum.Enum):
    """Service types for markup rules."""
    FLIGHT = "flight"
    HOTEL = "hotel"
    BUS = "bus"
    HOLIDAY = "holiday"
    VISA = "visa"
    ACTIVITY = "activity"
    TRANSFER = "transfer"
    ALL = "all"  # Apply to all services


class MarkupType(str, enum.Enum):
    """Markup calculation types."""
    FIXED = "fixed"  # Fixed amount (e.g., 500 INR)
    PERCENTAGE = "percentage"  # Percentage of base price (e.g., 5%)


class RouteType(str, enum.Enum):
    """Route types for flight/bus markups."""
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"
    ALL = "all"


class MarkupRule(Base):
    """
    Markup rule model for pricing calculations.
    
    This model defines rules for adding markup to supplier prices.
    Rules can be service-specific with various conditions.
    """
    __tablename__ = "markup_rules"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Tenant association (for multi-tenant)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # Rule configuration
    service_type = Column(Enum(ServiceType), nullable=False, index=True)
    markup_type = Column(Enum(MarkupType), nullable=False)
    value = Column(Float, nullable=False)  # Amount in INR or percentage
    
    # Priority (higher priority rules are applied first)
    priority = Column(Integer, default=0, nullable=False)
    
    # Conditions (JSON) - Rules are applied only if conditions match
    conditions = Column(JSON, nullable=True, default=dict)
    # Example flight conditions:
    # {
    #   "route_type": "international",
    #   "airline": "6E",
    #   "origin": "DEL",
    #   "destination": "DXB",
    #   "travel_class": "economy",
    #   "min_price": 5000,
    #   "max_price": 50000
    # }
    
    # Agent commission (percentage of markup)
    agent_commission_percentage = Column(Float, default=0.0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Validity period
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<MarkupRule(id={self.id}, service={self.service_type}, type={self.markup_type}, value={self.value})>"
    
    def is_valid(self) -> bool:
        """Check if rule is currently valid."""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    def calculate_markup(self, base_price: float) -> float:
        """
        Calculate markup amount based on rule.
        
        Args:
            base_price: Original supplier price
            
        Returns:
            float: Markup amount
        """
        if self.markup_type == MarkupType.FIXED:
            return self.value
        elif self.markup_type == MarkupType.PERCENTAGE:
            return (base_price * self.value) / 100
        return 0.0
    
    def calculate_agent_commission(self, markup_amount: float) -> float:
        """
        Calculate agent commission from markup.
        
        Args:
            markup_amount: Total markup amount
            
        Returns:
            float: Agent commission amount
        """
        return (markup_amount * self.agent_commission_percentage) / 100
    
    def matches_conditions(self, search_params: dict) -> bool:
        """
        Check if search parameters match rule conditions.
        
        Args:
            search_params: Search/booking parameters to match
            
        Returns:
            bool: True if all conditions match
        """
        if not self.conditions:
            return True
        
        for key, value in self.conditions.items():
            param_value = search_params.get(key)
            
            # Handle special conditions
            if key == "min_price":
                if param_value is None or param_value < value:
                    return False
            elif key == "max_price":
                if param_value is None or param_value > value:
                    return False
            elif key == "route_type":
                if param_value != value and value != "all":
                    return False
            else:
                # Exact match for other conditions
                if param_value != value:
                    return False
        
        return True
