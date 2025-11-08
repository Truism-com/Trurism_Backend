"""
API Key Pydantic Schemas

This module defines request/response schemas for API key management:
- API key creation and validation
- Usage statistics
- Scope management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

from app.api_keys.models import APIKeyScope


class APIKeyCreate(BaseModel):
    """
    Schema for creating a new API key.
    
    Validates API key creation parameters including name,
    scopes, and expiration settings.
    """
    name: str = Field(..., min_length=3, max_length=255, description="API key name")
    scopes: List[APIKeyScope] = Field(..., min_items=1, description="List of access scopes")
    description: Optional[str] = Field(None, max_length=1000, description="API key description")
    rate_limit: Optional[int] = Field(60, ge=1, le=1000, description="Requests per minute limit")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="Expiration in days")
    environment: Optional[str] = Field("production", description="Environment (production, staging, development)")
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["production", "staging", "development"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v


class APIKeyResponse(BaseModel):
    """
    Schema for API key response.
    
    Returns API key information including the plain key
    (only shown once during creation).
    """
    id: int = Field(..., description="API key ID")
    key: Optional[str] = Field(None, description="Plain API key (only shown once)")
    key_prefix: str = Field(..., description="Key prefix for identification")
    name: str = Field(..., description="API key name")
    scopes: List[str] = Field(..., description="Access scopes")
    is_active: bool = Field(..., description="Whether key is active")
    rate_limit: int = Field(..., description="Rate limit (requests/minute)")
    environment: str = Field(..., description="Environment")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(..., description="Total usage count")
    
    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """
    Schema for listing API keys.
    
    Returns a list of API keys without the actual key values.
    """
    id: int
    key_prefix: str
    name: str
    scopes: List[str]
    is_active: bool
    rate_limit: int
    environment: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    """
    Schema for updating an API key.
    
    Allows updating name, scopes, rate limit, and active status.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    scopes: Optional[List[APIKeyScope]] = Field(None, min_items=1)
    description: Optional[str] = Field(None, max_length=1000)
    rate_limit: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class APIKeyValidationRequest(BaseModel):
    """
    Schema for API key validation request.
    
    Used internally to validate API keys and check scopes.
    """
    api_key: str = Field(..., description="API key to validate")
    required_scope: Optional[str] = Field(None, description="Required scope for the operation")


class APIKeyUsageStats(BaseModel):
    """
    Schema for API key usage statistics.
    
    Provides detailed usage analytics for an API key.
    """
    key_id: int
    key_name: str
    total_requests: int
    requests_today: int
    requests_this_month: int
    last_used_at: Optional[datetime]
    first_used_at: Optional[datetime]
    average_requests_per_day: float
