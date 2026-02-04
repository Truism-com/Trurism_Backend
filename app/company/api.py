"""
Company Settings API Endpoints

Admin endpoints for company profile, branding, bank accounts, registration, and ACL.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.company.services import CompanyService
from app.company.schemas import (
    CompanyProfileUpdate, CompanyProfileResponse,
    CompanyBrandingUpdate, CompanyContactUpdate, CompanySocialUpdate,
    CompanySEOUpdate, CompanyEmailSettingsUpdate,
    BankAccountCreate, BankAccountUpdate, BankAccountResponse, BankAccountListResponse,
    BusinessRegistrationUpdate, BusinessRegistrationResponse,
    ACLModuleResponse, ACLModuleWithPermissions, ACLPermissionResponse,
    ACLRoleCreate, ACLRoleUpdate, ACLRoleResponse, ACLRoleDetailResponse, ACLRoleListResponse,
    ACLUserRoleAssign, ACLUserRoleResponse, UserPermissionsResponse
)

router = APIRouter(prefix="/admin/company", tags=["Admin - Company Settings"])


# =============================================================================
# COMPANY PROFILE
# =============================================================================

@router.get("/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get company profile and branding settings."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.get_company_profile()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not configured")
    
    return profile


@router.put("/profile", response_model=CompanyProfileResponse)
async def update_company_profile(
    data: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update company profile."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.update_company_profile(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return profile


@router.put("/profile/branding", response_model=CompanyProfileResponse)
async def update_branding(
    data: CompanyBrandingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update branding settings (logo, colors)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.update_branding(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return profile


@router.put("/profile/contact", response_model=CompanyProfileResponse)
async def update_contact_info(
    data: CompanyContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update contact information."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.update_contact(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return profile


@router.put("/profile/social", response_model=CompanyProfileResponse)
async def update_social_media(
    data: CompanySocialUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update social media links."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.update_social(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return profile


@router.put("/profile/seo", response_model=CompanyProfileResponse)
async def update_seo_settings(
    data: CompanySEOUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update SEO and analytics settings."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.update_seo(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return profile


@router.put("/profile/email-settings", response_model=CompanyProfileResponse)
async def update_email_settings(
    data: CompanyEmailSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update SMTP/email settings."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    profile = await service.update_email_settings(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return profile


# =============================================================================
# BANK ACCOUNTS
# =============================================================================

@router.get("/bank-accounts", response_model=BankAccountListResponse)
async def list_bank_accounts(
    purpose: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all bank accounts."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    accounts = await service.get_bank_accounts(
        purpose=purpose,
        is_active=is_active
    )
    
    return BankAccountListResponse(items=accounts, total=len(accounts))


@router.post("/bank-accounts", response_model=BankAccountResponse)
async def create_bank_account(
    data: BankAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new bank account."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    account = await service.create_bank_account(
        data=data.model_dump(),
        created_by=current_user.id
    )
    
    return account


@router.get("/bank-accounts/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get bank account by ID."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    account = await service.get_bank_account(account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    return account


@router.put("/bank-accounts/{account_id}", response_model=BankAccountResponse)
async def update_bank_account(
    account_id: int = Path(...),
    data: BankAccountUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update bank account."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    account = await service.update_bank_account(
        account_id=account_id,
        data=data.model_dump(exclude_unset=True, exclude_none=True)
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    return account


@router.delete("/bank-accounts/{account_id}")
async def delete_bank_account(
    account_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete bank account."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    success = await service.delete_bank_account(account_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    return {"message": "Bank account deleted"}


# =============================================================================
# BUSINESS REGISTRATION
# =============================================================================

@router.get("/registration", response_model=BusinessRegistrationResponse)
async def get_business_registration(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get business registration details."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    registration = await service.get_business_registration()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Business registration not configured")
    
    return registration


@router.put("/registration", response_model=BusinessRegistrationResponse)
async def update_business_registration(
    data: BusinessRegistrationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update business registration details."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    registration = await service.update_business_registration(
        data=data.model_dump(exclude_unset=True, exclude_none=True),
        updated_by=current_user.id
    )
    
    return registration


# =============================================================================
# ACL - MODULES & PERMISSIONS
# =============================================================================

@router.get("/acl/modules", response_model=List[ACLModuleWithPermissions])
async def list_acl_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all ACL modules with permissions."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    modules = await service.get_acl_modules()
    
    return modules


@router.get("/acl/permissions", response_model=List[ACLPermissionResponse])
async def list_all_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available permissions."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    permissions = await service.get_all_permissions()
    
    return permissions


# =============================================================================
# ACL - ROLES
# =============================================================================

@router.get("/acl/roles", response_model=ACLRoleListResponse)
async def list_acl_roles(
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all ACL roles."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    roles = await service.get_acl_roles(is_active=is_active)
    
    return ACLRoleListResponse(items=roles, total=len(roles))


@router.post("/acl/roles", response_model=ACLRoleResponse)
async def create_acl_role(
    data: ACLRoleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new ACL role."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    role = await service.create_acl_role(
        data=data.model_dump(exclude={'permissions'}),
        permissions=[p.model_dump() for p in data.permissions] if data.permissions else [],
        created_by=current_user.id
    )
    
    return role


@router.get("/acl/roles/{role_id}", response_model=ACLRoleDetailResponse)
async def get_acl_role(
    role_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get ACL role with permissions."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    role = await service.get_acl_role(role_id)
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permissions = await service.get_role_permissions(role_id)
    
    return ACLRoleDetailResponse(
        **role.__dict__,
        permissions=permissions
    )


@router.put("/acl/roles/{role_id}", response_model=ACLRoleResponse)
async def update_acl_role(
    role_id: int = Path(...),
    data: ACLRoleUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update ACL role."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    role = await service.update_acl_role(
        role_id=role_id,
        data=data.model_dump(exclude={'permissions'}, exclude_unset=True, exclude_none=True),
        permissions=[p.model_dump() for p in data.permissions] if data.permissions else None
    )
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.delete("/acl/roles/{role_id}")
async def delete_acl_role(
    role_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete ACL role."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    success = await service.delete_acl_role(role_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete system role or role not found")
    
    return {"message": "Role deleted"}


# =============================================================================
# ACL - USER ROLE ASSIGNMENTS
# =============================================================================

@router.post("/acl/user-roles", response_model=ACLUserRoleResponse)
async def assign_role_to_user(
    data: ACLUserRoleAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a user."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    user_role = await service.assign_role_to_user(
        user_id=data.user_id,
        role_id=data.role_id,
        assigned_by=current_user.id,
        expires_at=data.expires_at
    )
    
    role = await service.get_acl_role(data.role_id)
    
    return ACLUserRoleResponse(
        id=user_role.id,
        user_id=user_role.user_id,
        role_id=user_role.role_id,
        role_name=role.name if role else None,
        role_display_name=role.display_name if role else None,
        assigned_by=user_role.assigned_by,
        assigned_at=user_role.assigned_at,
        expires_at=user_role.expires_at,
        is_active=user_role.is_active
    )


@router.delete("/acl/user-roles/{user_id}/{role_id}")
async def remove_role_from_user(
    user_id: int = Path(...),
    role_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a role from a user."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    success = await service.remove_role_from_user(user_id, role_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User role assignment not found")
    
    return {"message": "Role removed from user"}


@router.get("/acl/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's effective permissions."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    roles = await service.get_user_roles(user_id)
    permissions = await service.get_user_permissions(user_id)
    
    return UserPermissionsResponse(
        user_id=user_id,
        roles=roles,
        permissions=list(permissions)
    )


# =============================================================================
# SEEDING
# =============================================================================

@router.post("/acl/seed")
async def seed_acl_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Seed default ACL modules, permissions, and roles."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = CompanyService(db)
    
    modules, permissions = await service.seed_acl_modules_and_permissions()
    roles = await service.seed_default_roles()
    
    return {
        "message": "ACL data seeded",
        "modules_created": modules,
        "permissions_created": permissions,
        "roles_created": len(roles)
    }


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

public_router = APIRouter(prefix="/company", tags=["Company (Public)"])


@public_router.get("/branding")
async def get_public_branding(
    db: AsyncSession = Depends(get_db)
):
    """Get public branding info (logo, colors, contact)."""
    service = CompanyService(db)
    profile = await service.get_company_profile()
    
    if not profile:
        return {}
    
    return {
        "company_name": profile.company_name,
        "tagline": profile.tagline,
        "logo_url": profile.logo_url,
        "logo_dark_url": profile.logo_dark_url,
        "favicon_url": profile.favicon_url,
        "primary_color": profile.primary_color,
        "secondary_color": profile.secondary_color,
        "accent_color": profile.accent_color,
        "email": profile.email,
        "support_email": profile.support_email,
        "phone": profile.phone,
        "toll_free": profile.toll_free,
        "whatsapp": profile.whatsapp,
        "website_url": profile.website_url,
        "facebook_url": profile.facebook_url,
        "instagram_url": profile.instagram_url,
        "twitter_url": profile.twitter_url,
        "linkedin_url": profile.linkedin_url,
        "youtube_url": profile.youtube_url
    }


@public_router.get("/bank-accounts")
async def get_public_bank_accounts(
    db: AsyncSession = Depends(get_db)
):
    """Get public bank accounts for wallet top-up."""
    service = CompanyService(db)
    accounts = await service.get_bank_accounts(
        purpose="wallet_topup",
        is_active=True
    )
    
    # Return limited info
    return [
        {
            "id": acc.id,
            "bank_name": acc.bank_name,
            "branch_name": acc.branch_name,
            "account_name": acc.account_name,
            "account_number": acc.account_number,
            "account_type": acc.account_type.value,
            "ifsc_code": acc.ifsc_code,
            "upi_id": acc.upi_id,
            "upi_qr_code_url": acc.upi_qr_code_url,
            "is_primary": acc.is_primary
        }
        for acc in accounts
    ]
