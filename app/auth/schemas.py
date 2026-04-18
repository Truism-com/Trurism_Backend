"""
Authentication Pydantic Schemas

This module defines Pydantic schemas for request/response validation:
- User registration and login schemas
- User profile schemas
- Token response schemas
- Password reset schemas
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

from app.auth.models import UserRole, AgentApprovalStatus


class UserRegisterRequest(BaseModel):
    """
    Schema for user registration request.
    
    Validates user registration data including email, password,
    and role-specific information like company details for agents.
    """
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    company_name: Optional[str] = None  # Required for agents
    pan_number: Optional[str] = None    # Required for agents
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: Optional[str], info) -> Optional[str]:
        """Validate company name is provided for agents."""
        role = info.data.get('role')
        if role == UserRole.AGENT and not v:
            raise ValueError('Company name is required for agents')
        return v
    
    @field_validator('pan_number')
    @classmethod
    def validate_pan_number(cls, v: Optional[str], info) -> Optional[str]:
        """Validate PAN number is provided for agents."""
        role = info.data.get('role')
        if role == UserRole.AGENT and not v:
            raise ValueError('PAN number is required for agents')
        if v and len(v) != 10:
            raise ValueError('PAN number must be exactly 10 characters')
        return v


class UserLoginRequest(BaseModel):
    """
    Schema for user login request.
    
    Validates login credentials for user authentication.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Schema for authentication token response.
    
    Returns JWT access and refresh tokens after successful login.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request.
    
    Used to exchange a valid refresh token for a new access token.
    """
    refresh_token: str


class UserProfileResponse(BaseModel):
    """
    Schema for user profile response.
    
    Returns user profile information for authenticated users.
    """
    id: int
    email: str
    name: str
    phone: Optional[str]
    address: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    company_name: Optional[str]
    pan_number: Optional[str]
    approval_status: Optional[AgentApprovalStatus]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """
    Schema for user profile update request.
    
    Allows users to update their profile information.
    """
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v


class PasswordChangeRequest(BaseModel):
    """
    Schema for password change request.
    
    Validates current and new password for password changes.
    """
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class AgentApprovalRequest(BaseModel):
    """
    Schema for agent approval request.
    
    Used by admins to approve or reject agent applications.
    """
    approval_status: AgentApprovalStatus
    rejection_reason: Optional[str] = None


class UserListResponse(BaseModel):
    """
    Schema for user list response.
    
    Used in admin endpoints to list all users with pagination.
    """
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    approval_status: Optional[AgentApprovalStatus]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class GoogleLoginRequest(BaseModel):
    """Schema for Google OAuth login via ID token."""
    id_token: str
