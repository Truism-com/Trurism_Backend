"""
Tenant Database Models

This module defines database models for multi-tenant white-label support:
- Tenant configuration
- Branding settings
- Module enablement flags
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


class Tenant(Base):
    """
    Tenant model for white-label configuration.
    
    Each tenant represents a separate travel brand/website that uses
    the same backend infrastructure with different branding and settings.
    """
    __tablename__ = "tenants"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "agency1"
    name = Column(String(255), nullable=False)  # e.g., "Travel Agency 1"
    
    # Domain configuration
    domain = Column(String(255), unique=True, index=True, nullable=False)  # e.g., "agency1.com"
    subdomain = Column(String(100), nullable=True)  # e.g., "agency1" for agency1.trurism.com
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    brand_name = Column(String(255), nullable=True)
    
    # Theme colors (JSON)
    theme_colors = Column(JSON, nullable=True, default=dict)
    # Example: {"primary": "#1E40AF", "secondary": "#F59E0B", "accent": "#10B981"}
    
    # Contact information
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    support_whatsapp = Column(String(50), nullable=True)
    
    # Social media links (JSON)
    social_links = Column(JSON, nullable=True, default=dict)
    # Example: {"facebook": "https://facebook.com/...", "twitter": "...", "instagram": "..."}
    
    # Module configuration (JSON) - Which modules are enabled
    enabled_modules = Column(JSON, nullable=True, default=dict)
    # Example: {"flights": true, "hotels": true, "buses": true, "holidays": true, "visas": false}
    
    # Currency and localization
    default_currency = Column(String(3), default="INR", nullable=False)
    default_language = Column(String(5), default="en", nullable=False)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    
    # Business information
    company_name = Column(String(255), nullable=True)
    gst_number = Column(String(20), nullable=True)
    pan_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Custom settings (JSON) - For any additional configuration
    custom_settings = Column(JSON, nullable=True, default=dict)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, code={self.code}, domain={self.domain})>"
    
    def get_public_config(self) -> dict:
        """
        Get public configuration for frontend.
        
        This returns only the configuration that should be exposed
        to the frontend application.
        """
        return {
            "tenant_id": self.id,
            "code": self.code,
            "brand_name": self.brand_name or self.name,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "theme_colors": self.theme_colors or {},
            "support": {
                "email": self.support_email,
                "phone": self.support_phone,
                "whatsapp": self.support_whatsapp
            },
            "social_links": self.social_links or {},
            "enabled_modules": self.enabled_modules or {},
            "currency": self.default_currency,
            "language": self.default_language
        }
