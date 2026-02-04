"""
Company Settings Schemas

Pydantic schemas for company branding, bank accounts, registration, and ACL.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from app.company.models import BankAccountType


# =============================================================================
# COMPANY PROFILE SCHEMAS
# =============================================================================

class CompanyProfileBase(BaseModel):
    """Base company profile schema."""
    company_name: str = Field(..., min_length=1, max_length=300)
    legal_name: Optional[str] = Field(None, max_length=300)
    tagline: Optional[str] = Field(None, max_length=500)
    about_us: Optional[str] = None


class CompanyBrandingUpdate(BaseModel):
    """Branding update schema."""
    logo_url: Optional[str] = Field(None, max_length=500)
    logo_dark_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    og_image_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=20, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, max_length=20, pattern="^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, max_length=20, pattern="^#[0-9A-Fa-f]{6}$")


class CompanyContactUpdate(BaseModel):
    """Contact information update schema."""
    email: Optional[EmailStr] = None
    support_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    toll_free: Optional[str] = Field(None, max_length=50)
    whatsapp: Optional[str] = Field(None, max_length=50)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=300)
    address_line2: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)


class CompanySocialUpdate(BaseModel):
    """Social media update schema."""
    website_url: Optional[str] = Field(None, max_length=300)
    facebook_url: Optional[str] = Field(None, max_length=300)
    instagram_url: Optional[str] = Field(None, max_length=300)
    twitter_url: Optional[str] = Field(None, max_length=300)
    linkedin_url: Optional[str] = Field(None, max_length=300)
    youtube_url: Optional[str] = Field(None, max_length=300)


class CompanySEOUpdate(BaseModel):
    """SEO settings update schema."""
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    google_analytics_id: Optional[str] = Field(None, max_length=50)
    facebook_pixel_id: Optional[str] = Field(None, max_length=50)


class CompanyEmailSettingsUpdate(BaseModel):
    """Email settings update schema."""
    smtp_host: Optional[str] = Field(None, max_length=200)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_username: Optional[str] = Field(None, max_length=200)
    smtp_password: Optional[str] = Field(None, max_length=200)
    email_from_name: Optional[str] = Field(None, max_length=200)
    email_from_address: Optional[EmailStr] = None


class CompanyProfileCreate(CompanyProfileBase):
    """Create company profile."""
    pass


class CompanyProfileUpdate(BaseModel):
    """Update company profile."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=300)
    legal_name: Optional[str] = Field(None, max_length=300)
    tagline: Optional[str] = Field(None, max_length=500)
    about_us: Optional[str] = None
    
    # Branding
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    favicon_url: Optional[str] = None
    og_image_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    
    # Contact
    email: Optional[str] = None
    support_email: Optional[str] = None
    phone: Optional[str] = None
    toll_free: Optional[str] = None
    whatsapp: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    
    # Social
    website_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    youtube_url: Optional[str] = None
    
    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    google_analytics_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None
    
    # Localization
    timezone: Optional[str] = None
    default_currency: Optional[str] = None
    date_format: Optional[str] = None


class CompanyProfileResponse(BaseModel):
    """Company profile response."""
    id: int
    tenant_id: int
    
    # Basic
    company_name: str
    legal_name: Optional[str] = None
    tagline: Optional[str] = None
    about_us: Optional[str] = None
    
    # Branding
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    favicon_url: Optional[str] = None
    og_image_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    
    # Contact
    email: Optional[str] = None
    support_email: Optional[str] = None
    phone: Optional[str] = None
    toll_free: Optional[str] = None
    whatsapp: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    
    # Social
    website_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    youtube_url: Optional[str] = None
    
    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    google_analytics_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None
    
    # Localization
    timezone: str
    default_currency: str
    date_format: str
    
    # Audit
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# BANK ACCOUNT SCHEMAS
# =============================================================================

class BankAccountBase(BaseModel):
    """Base bank account schema."""
    bank_name: str = Field(..., min_length=1, max_length=200)
    branch_name: Optional[str] = Field(None, max_length=200)
    account_name: str = Field(..., min_length=1, max_length=300)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_type: BankAccountType = BankAccountType.CURRENT
    
    ifsc_code: Optional[str] = Field(None, max_length=20)
    swift_code: Optional[str] = Field(None, max_length=20)
    iban: Optional[str] = Field(None, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=20)
    
    upi_id: Optional[str] = Field(None, max_length=100)
    upi_qr_code_url: Optional[str] = Field(None, max_length=500)
    
    purpose: str = Field("wallet_topup", max_length=100)
    description: Optional[str] = None
    
    display_order: int = Field(0, ge=0)
    is_primary: bool = False
    is_active: bool = True


class BankAccountCreate(BankAccountBase):
    """Create bank account."""
    pass


class BankAccountUpdate(BaseModel):
    """Update bank account."""
    bank_name: Optional[str] = Field(None, min_length=1, max_length=200)
    branch_name: Optional[str] = None
    account_name: Optional[str] = Field(None, min_length=1, max_length=300)
    account_number: Optional[str] = None
    account_type: Optional[BankAccountType] = None
    ifsc_code: Optional[str] = None
    swift_code: Optional[str] = None
    iban: Optional[str] = None
    routing_number: Optional[str] = None
    upi_id: Optional[str] = None
    upi_qr_code_url: Optional[str] = None
    purpose: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None


class BankAccountResponse(BankAccountBase):
    """Bank account response."""
    id: int
    tenant_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BankAccountListResponse(BaseModel):
    """List of bank accounts."""
    items: List[BankAccountResponse]
    total: int


# =============================================================================
# BUSINESS REGISTRATION SCHEMAS
# =============================================================================

class BusinessRegistrationCreate(BaseModel):
    """Create business registration."""
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None


class BusinessRegistrationUpdate(BaseModel):
    """Update business registration."""
    # GST
    gst_number: Optional[str] = Field(None, max_length=50)
    gst_state_code: Optional[str] = Field(None, max_length=10)
    gst_type: Optional[str] = Field(None, max_length=20)
    gst_certificate_url: Optional[str] = None
    
    # PAN
    pan_number: Optional[str] = Field(None, max_length=20)
    pan_name: Optional[str] = Field(None, max_length=300)
    pan_card_url: Optional[str] = None
    
    # Company Registration
    cin_number: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=100)
    incorporation_date: Optional[date] = None
    incorporation_certificate_url: Optional[str] = None
    
    # IATA/Travel License
    iata_code: Optional[str] = Field(None, max_length=20)
    iata_certificate_url: Optional[str] = None
    travel_license_number: Optional[str] = Field(None, max_length=100)
    travel_license_expiry: Optional[date] = None
    travel_license_url: Optional[str] = None
    
    # TAN
    tan_number: Optional[str] = Field(None, max_length=20)
    
    # MSME
    msme_number: Optional[str] = Field(None, max_length=50)
    msme_certificate_url: Optional[str] = None
    
    # Insurance
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_expiry: Optional[date] = None
    insurance_certificate_url: Optional[str] = None
    
    # Custom
    custom_registrations: Optional[Dict[str, Any]] = None


class BusinessRegistrationResponse(BaseModel):
    """Business registration response."""
    id: int
    tenant_id: int
    
    # GST
    gst_number: Optional[str] = None
    gst_state_code: Optional[str] = None
    gst_type: Optional[str] = None
    gst_certificate_url: Optional[str] = None
    
    # PAN
    pan_number: Optional[str] = None
    pan_name: Optional[str] = None
    pan_card_url: Optional[str] = None
    
    # Company Registration
    cin_number: Optional[str] = None
    registration_number: Optional[str] = None
    incorporation_date: Optional[date] = None
    incorporation_certificate_url: Optional[str] = None
    
    # IATA/Travel License
    iata_code: Optional[str] = None
    iata_certificate_url: Optional[str] = None
    travel_license_number: Optional[str] = None
    travel_license_expiry: Optional[date] = None
    travel_license_url: Optional[str] = None
    
    # TAN
    tan_number: Optional[str] = None
    
    # MSME
    msme_number: Optional[str] = None
    msme_certificate_url: Optional[str] = None
    
    # Insurance
    insurance_policy_number: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_expiry: Optional[date] = None
    insurance_certificate_url: Optional[str] = None
    
    # Custom
    custom_registrations: Optional[Dict[str, Any]] = None
    
    # Audit
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# ACL SCHEMAS
# =============================================================================

class ACLModuleResponse(BaseModel):
    """ACL module response."""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    parent_module_id: Optional[int] = None
    icon: Optional[str] = None
    display_order: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ACLPermissionResponse(BaseModel):
    """ACL permission response."""
    id: int
    module_id: int
    name: str
    display_name: str
    description: Optional[str] = None
    code: str
    is_active: bool
    
    class Config:
        from_attributes = True


class ACLModuleWithPermissions(ACLModuleResponse):
    """Module with its permissions."""
    permissions: List[ACLPermissionResponse] = []
    children: List["ACLModuleWithPermissions"] = []


class ACLRolePermissionAssign(BaseModel):
    """Assign permission to role."""
    permission_id: int
    is_granted: bool = True


class ACLRoleCreate(BaseModel):
    """Create ACL role."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: bool = False
    permissions: List[ACLRolePermissionAssign] = []


class ACLRoleUpdate(BaseModel):
    """Update ACL role."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[ACLRolePermissionAssign]] = None


class ACLRoleResponse(BaseModel):
    """ACL role response."""
    id: int
    tenant_id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_system_role: bool
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ACLRoleDetailResponse(ACLRoleResponse):
    """ACL role with permissions."""
    permissions: List[ACLPermissionResponse] = []


class ACLRoleListResponse(BaseModel):
    """List of roles."""
    items: List[ACLRoleResponse]
    total: int


class ACLUserRoleAssign(BaseModel):
    """Assign role to user."""
    user_id: int
    role_id: int
    expires_at: Optional[datetime] = None


class ACLUserRoleResponse(BaseModel):
    """User role assignment response."""
    id: int
    user_id: int
    role_id: int
    role_name: Optional[str] = None
    role_display_name: Optional[str] = None
    assigned_by: Optional[int] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class UserPermissionsResponse(BaseModel):
    """User's effective permissions."""
    user_id: int
    roles: List[ACLRoleResponse]
    permissions: List[str]  # List of permission codes


# Update forward ref
ACLModuleWithPermissions.model_rebuild()
