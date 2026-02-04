"""
Settings Pydantic Schemas

Schemas for settings and staff management validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime

from app.settings.models import PaymentMode


# =============================================================================
# CONVENIENCE FEE SCHEMAS
# =============================================================================

class ConvenienceFeeBase(BaseModel):
    """Base convenience fee schema."""
    service_type: str = Field(..., max_length=50)
    payment_mode: PaymentMode
    fee_type: str = Field("percentage", pattern="^(percentage|fixed|both)$")
    percentage: float = Field(0, ge=0, le=100)
    fixed_amount: float = Field(0, ge=0)
    min_fee: float = Field(0, ge=0)
    max_fee: Optional[float] = Field(None, ge=0)
    gst_percentage: float = Field(18.0, ge=0, le=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class ConvenienceFeeCreate(ConvenienceFeeBase):
    """Schema for creating a convenience fee."""
    pass


class ConvenienceFeeUpdate(BaseModel):
    """Schema for updating a convenience fee."""
    fee_type: Optional[str] = Field(None, pattern="^(percentage|fixed|both)$")
    percentage: Optional[float] = Field(None, ge=0, le=100)
    fixed_amount: Optional[float] = Field(None, ge=0)
    min_fee: Optional[float] = Field(None, ge=0)
    max_fee: Optional[float] = Field(None, ge=0)
    gst_percentage: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ConvenienceFeeResponse(ConvenienceFeeBase):
    """Convenience fee response schema."""
    id: int
    tenant_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConvenienceFeeListResponse(BaseModel):
    """List of convenience fees."""
    items: List[ConvenienceFeeResponse]
    total: int


class FeeCalculationRequest(BaseModel):
    """Request to calculate convenience fee."""
    service_type: str
    payment_mode: PaymentMode
    amount: float = Field(..., ge=0)


class FeeCalculationResponse(BaseModel):
    """Calculated convenience fee."""
    base_amount: float
    fee_amount: float
    gst_on_fee: float
    total_fee: float
    total_amount: float
    fee_breakdown: Dict[str, Any]


# =============================================================================
# STAFF PERMISSION SCHEMAS
# =============================================================================

class StaffPermissionBase(BaseModel):
    """Base permission schema."""
    code: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    module: str = Field(..., max_length=50)
    display_order: int = Field(0, ge=0)


class StaffPermissionCreate(StaffPermissionBase):
    """Schema for creating a permission."""
    pass


class StaffPermissionResponse(StaffPermissionBase):
    """Permission response schema."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PermissionsByModule(BaseModel):
    """Permissions grouped by module."""
    module: str
    permissions: List[StaffPermissionResponse]


# =============================================================================
# STAFF ROLE SCHEMAS
# =============================================================================

class StaffRoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None  # List of permission codes


class StaffRoleCreate(StaffRoleBase):
    """Schema for creating a role."""
    pass


class StaffRoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StaffRoleResponse(BaseModel):
    """Role response schema."""
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_system: bool
    is_active: bool
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StaffRoleListResponse(BaseModel):
    """List of roles."""
    items: List[StaffRoleResponse]
    total: int


# =============================================================================
# STAFF MEMBER SCHEMAS
# =============================================================================

class StaffMemberBase(BaseModel):
    """Base staff member schema."""
    employee_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)
    role_id: int
    additional_permissions: Optional[List[str]] = None
    restricted_permissions: Optional[List[str]] = None
    can_access_admin: bool = True
    ip_whitelist: Optional[List[str]] = None


class StaffMemberCreate(StaffMemberBase):
    """Schema for creating a staff member."""
    user_id: int


class StaffMemberUpdate(BaseModel):
    """Schema for updating a staff member."""
    employee_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=100)
    role_id: Optional[int] = None
    additional_permissions: Optional[List[str]] = None
    restricted_permissions: Optional[List[str]] = None
    can_access_admin: Optional[bool] = None
    ip_whitelist: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StaffMemberUserInfo(BaseModel):
    """Basic user info for staff member."""
    id: int
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        from_attributes = True


class StaffMemberResponse(BaseModel):
    """Staff member response schema."""
    id: int
    user_id: int
    user: Optional[StaffMemberUserInfo] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    role_id: int
    role: Optional[StaffRoleResponse] = None
    additional_permissions: Optional[List[str]] = None
    restricted_permissions: Optional[List[str]] = None
    can_access_admin: bool
    ip_whitelist: Optional[List[str]] = None
    is_active: bool
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StaffMemberListResponse(BaseModel):
    """List of staff members."""
    items: List[StaffMemberResponse]
    total: int


class StaffPermissionCheck(BaseModel):
    """Check if staff has permission."""
    has_permission: bool
    permission_code: str
    granted_by: Optional[str] = None  # role, additional, or denied


# =============================================================================
# SYSTEM SETTING SCHEMAS
# =============================================================================

class SystemSettingBase(BaseModel):
    """Base system setting schema."""
    key: str = Field(..., max_length=100)
    value: Any
    value_type: str = Field("string", pattern="^(string|number|boolean|json)$")
    category: str = Field("general", max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False
    is_editable: bool = True


class SystemSettingCreate(SystemSettingBase):
    """Schema for creating a system setting."""
    pass


class SystemSettingUpdate(BaseModel):
    """Schema for updating a system setting."""
    value: Optional[Any] = None
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class SystemSettingResponse(BaseModel):
    """System setting response schema."""
    id: int
    key: str
    value: Any
    value_type: str
    category: str
    description: Optional[str] = None
    is_public: bool
    is_editable: bool
    tenant_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SystemSettingListResponse(BaseModel):
    """List of system settings."""
    items: List[SystemSettingResponse]
    total: int


class SettingsByCategory(BaseModel):
    """Settings grouped by category."""
    category: str
    settings: List[SystemSettingResponse]


class PublicSettingsResponse(BaseModel):
    """Public settings for frontend."""
    settings: Dict[str, Any]
