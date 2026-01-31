"""
Visa Pydantic Schemas

Request/Response schemas for visa operations.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date

from app.visa.models import ApplicationStatus


# =============================================================================
# Visa Country Schemas
# =============================================================================

class VisaCountryBase(BaseModel):
    """Base schema for visa country."""
    name: str
    slug: Optional[str] = None
    code: Optional[str] = None
    flag_url: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    embassy_details: Optional[str] = None
    general_requirements: Optional[str] = None
    is_popular: bool = False
    display_order: int = 0


class VisaCountryCreate(VisaCountryBase):
    """Schema for creating a visa country."""
    pass


class VisaCountryUpdate(BaseModel):
    """Schema for updating a visa country."""
    name: Optional[str] = None
    slug: Optional[str] = None
    code: Optional[str] = None
    flag_url: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    embassy_details: Optional[str] = None
    general_requirements: Optional[str] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class VisaCountryResponse(VisaCountryBase):
    """Response schema for visa country."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VisaCountryWithTypes(VisaCountryResponse):
    """Response schema with visa types included."""
    visa_types: List["VisaTypeResponse"] = []


# =============================================================================
# Visa Type Schemas
# =============================================================================

class VisaTypeBase(BaseModel):
    """Base schema for visa type."""
    name: str
    slug: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    validity: Optional[str] = None
    entry_type: Optional[str] = None
    processing_time: Optional[str] = None
    min_processing_days: Optional[int] = None
    max_processing_days: Optional[int] = None
    display_order: int = 0


class VisaTypeCreate(VisaTypeBase):
    """Schema for creating a visa type."""
    country_id: int
    base_price: float = 0
    government_fee: float = 0
    vfs_fee: float = 0
    total_price: float = 0
    is_express_available: bool = False
    express_price: Optional[float] = None
    express_processing_days: Optional[int] = None


class VisaTypeUpdate(BaseModel):
    """Schema for updating a visa type."""
    name: Optional[str] = None
    slug: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    validity: Optional[str] = None
    entry_type: Optional[str] = None
    processing_time: Optional[str] = None
    min_processing_days: Optional[int] = None
    max_processing_days: Optional[int] = None
    base_price: Optional[float] = None
    government_fee: Optional[float] = None
    vfs_fee: Optional[float] = None
    total_price: Optional[float] = None
    is_express_available: Optional[bool] = None
    express_price: Optional[float] = None
    express_processing_days: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class VisaTypeResponse(VisaTypeBase):
    """Response schema for visa type."""
    id: int
    country_id: int
    base_price: float
    government_fee: float
    vfs_fee: float
    total_price: float
    is_express_available: bool
    express_price: Optional[float] = None
    express_processing_days: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VisaTypeDetail(VisaTypeResponse):
    """Detailed visa type with requirements."""
    country: Optional[VisaCountryResponse] = None
    requirements: List["VisaRequirementResponse"] = []


# =============================================================================
# Visa Requirement Schemas
# =============================================================================

class VisaRequirementBase(BaseModel):
    """Base schema for visa requirement."""
    category: str  # documents, personal, financial
    title: str
    description: Optional[str] = None
    is_mandatory: bool = True
    applies_to: Optional[str] = None
    display_order: int = 0


class VisaRequirementCreate(VisaRequirementBase):
    """Schema for creating a requirement."""
    visa_type_id: int


class VisaRequirementUpdate(BaseModel):
    """Schema for updating a requirement."""
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_mandatory: Optional[bool] = None
    applies_to: Optional[str] = None
    display_order: Optional[int] = None


class VisaRequirementResponse(VisaRequirementBase):
    """Response schema for visa requirement."""
    id: int
    visa_type_id: int
    
    class Config:
        from_attributes = True


# =============================================================================
# Visa Application Schemas
# =============================================================================

class VisaApplicationBase(BaseModel):
    """Base schema for visa application."""
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    passport_number: Optional[str] = None
    passport_expiry: Optional[date] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None
    travel_date: Optional[date] = None
    return_date: Optional[date] = None
    purpose_of_visit: Optional[str] = None
    is_express: bool = False


class VisaApplicationCreate(VisaApplicationBase):
    """Schema for creating a visa application."""
    visa_type_id: int
    documents: Optional[List[dict]] = None  # List of document info


class VisaApplicationUpdate(BaseModel):
    """Schema for updating application (admin)."""
    status: Optional[ApplicationStatus] = None
    status_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None
    admin_notes: Optional[str] = None
    
    # Result fields
    visa_number: Optional[str] = None
    visa_issue_date: Optional[date] = None
    visa_expiry_date: Optional[date] = None
    rejection_reason: Optional[str] = None
    
    # Payment
    amount_paid: Optional[float] = None
    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None


class VisaApplicationResponse(VisaApplicationBase):
    """Response schema for visa application."""
    id: int
    application_ref: str
    visa_type_id: int
    user_id: Optional[int] = None
    
    status: ApplicationStatus
    status_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    base_amount: float
    express_fee: float
    taxes: float
    total_amount: float
    amount_paid: float
    payment_status: Optional[str] = None
    
    visa_number: Optional[str] = None
    visa_issue_date: Optional[date] = None
    visa_expiry_date: Optional[date] = None
    rejection_reason: Optional[str] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VisaApplicationDetail(VisaApplicationResponse):
    """Detailed application with visa type and country."""
    visa_type: Optional[VisaTypeResponse] = None
    documents: Optional[List[dict]] = None
    admin_notes: Optional[str] = None  # Only for admin view


class VisaApplicationListResponse(BaseModel):
    """Paginated list of applications."""
    applications: List[VisaApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Search Schemas
# =============================================================================

class VisaSearchParams(BaseModel):
    """Parameters for visa search."""
    country_id: Optional[int] = None
    query: Optional[str] = None
    is_popular: Optional[bool] = None
    page: int = 1
    page_size: int = 20


class VisaCountryListResponse(BaseModel):
    """Paginated list of countries."""
    countries: List[VisaCountryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Update forward references
VisaCountryWithTypes.model_rebuild()
VisaTypeDetail.model_rebuild()
