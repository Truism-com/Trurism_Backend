"""
API Key Database Models

This module defines database models for API key management:
- APIKey model for partner authentication
- Scope-based permissions
- Usage tracking and rate limiting
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base


class APIKeyScope(str, enum.Enum):
    """
    API key scopes for granular access control.
    
    - ALL: Access to all services
    - FLIGHT: Flight search and booking only
    - HOTEL: Hotel search and booking only
    - BUS: Bus search and booking only
    - PACKAGE: Holiday packages only
    - VISA: Visa services only
    - ACTIVITY: Activity bookings only
    """
    ALL = "all"
    FLIGHT = "flight"
    HOTEL = "hotel"
    BUS = "bus"
    PACKAGE = "package"
    VISA = "visa"
    ACTIVITY = "activity"


class APIKey(Base):
    """
    API Key model for partner integrations.
    
    This model stores API keys for partners/agents with scope-based
    permissions and usage tracking for the travel booking platform.
    """
    __tablename__ = "api_keys"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)  # SHA256 hash
    key_prefix = Column(String(16), nullable=False)  # For identification (e.g., "tk_live_")
    name = Column(String(255), nullable=False)  # Descriptive name
    
    # Partner/User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    
    # Permissions and scopes
    scopes = Column(JSON, nullable=False, default=list)  # List of APIKeyScope values
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Rate limiting (requests per minute)
    rate_limit = Column(Integer, default=60, nullable=False)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    environment = Column(String(20), default="production")  # production, staging, development
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired/revoked)."""
        if not self.is_active or self.revoked_at:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def has_scope(self, scope: str) -> bool:
        """Check if API key has a specific scope."""
        if not self.scopes:
            return False
        
        # ALL scope grants access to everything
        if APIKeyScope.ALL.value in self.scopes:
            return True
        
        return scope in self.scopes
