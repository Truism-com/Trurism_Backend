"""
Settings API Endpoints

REST API for admin settings and staff management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.settings.models import PaymentMode
from app.settings.services import SettingsService
from app.settings.schemas import (
    ConvenienceFeeCreate, ConvenienceFeeUpdate,
    ConvenienceFeeResponse, ConvenienceFeeListResponse,
    FeeCalculationRequest, FeeCalculationResponse,
    StaffPermissionCreate, StaffPermissionResponse, PermissionsByModule,
    StaffRoleCreate, StaffRoleUpdate, StaffRoleResponse, StaffRoleListResponse,
    StaffMemberCreate, StaffMemberUpdate, StaffMemberResponse, StaffMemberListResponse,
    StaffPermissionCheck,
    SystemSettingCreate, SystemSettingUpdate,
    SystemSettingResponse, SystemSettingListResponse,
    SettingsByCategory, PublicSettingsResponse
)

router = APIRouter(prefix="/settings", tags=["Settings"])


# =============================================================================
# CONVENIENCE FEE ENDPOINTS
# =============================================================================

@router.get("/fees", response_model=ConvenienceFeeListResponse)
async def get_convenience_fees(
    service_type: Optional[str] = None,
    payment_mode: Optional[PaymentMode] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all convenience fee configurations (admin)."""
    service = SettingsService(db)
    fees = await service.get_convenience_fees(
        service_type=service_type,
        payment_mode=payment_mode,
        is_active=is_active
    )
    return ConvenienceFeeListResponse(
        items=[ConvenienceFeeResponse.model_validate(f) for f in fees],
        total=len(fees)
    )


@router.post("/fees", response_model=ConvenienceFeeResponse)
async def create_convenience_fee(
    data: ConvenienceFeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a convenience fee configuration (admin)."""
    service = SettingsService(db)
    fee = await service.create_convenience_fee(
        data=data,
        created_by_id=current_user.id
    )
    return ConvenienceFeeResponse.model_validate(fee)


@router.get("/fees/{fee_id}", response_model=ConvenienceFeeResponse)
async def get_convenience_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get convenience fee by ID (admin)."""
    service = SettingsService(db)
    fee = await service.get_convenience_fee(fee_id)
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
    return ConvenienceFeeResponse.model_validate(fee)


@router.put("/fees/{fee_id}", response_model=ConvenienceFeeResponse)
async def update_convenience_fee(
    fee_id: int,
    data: ConvenienceFeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a convenience fee (admin)."""
    service = SettingsService(db)
    fee = await service.update_convenience_fee(fee_id, data)
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
    return ConvenienceFeeResponse.model_validate(fee)


@router.delete("/fees/{fee_id}")
async def delete_convenience_fee(
    fee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a convenience fee (admin)."""
    service = SettingsService(db)
    deleted = await service.delete_convenience_fee(fee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fee not found")
    return {"message": "Fee deleted successfully"}


@router.post("/fees/calculate", response_model=FeeCalculationResponse)
async def calculate_convenience_fee(
    data: FeeCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calculate convenience fee for a transaction (public)."""
    service = SettingsService(db)
    return await service.calculate_convenience_fee(data)


# =============================================================================
# PERMISSION ENDPOINTS
# =============================================================================

@router.get("/permissions", response_model=list[StaffPermissionResponse])
async def get_all_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all available permissions (admin)."""
    service = SettingsService(db)
    permissions = await service.get_all_permissions()
    return [StaffPermissionResponse.model_validate(p) for p in permissions]


@router.get("/permissions/by-module", response_model=list[PermissionsByModule])
async def get_permissions_by_module(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get permissions grouped by module (admin)."""
    service = SettingsService(db)
    return await service.get_permissions_by_module()


@router.post("/permissions", response_model=StaffPermissionResponse)
async def create_permission(
    data: StaffPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new permission (admin)."""
    service = SettingsService(db)
    permission = await service.create_permission(data)
    return StaffPermissionResponse.model_validate(permission)


@router.post("/permissions/seed")
async def seed_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Seed default permissions (admin)."""
    service = SettingsService(db)
    await service.seed_default_permissions()
    return {"message": "Default permissions seeded"}


# =============================================================================
# ROLE ENDPOINTS
# =============================================================================

@router.get("/roles", response_model=StaffRoleListResponse)
async def get_roles(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all staff roles (admin)."""
    service = SettingsService(db)
    roles = await service.get_roles(is_active=is_active)
    return StaffRoleListResponse(
        items=[StaffRoleResponse.model_validate(r) for r in roles],
        total=len(roles)
    )


@router.post("/roles", response_model=StaffRoleResponse)
async def create_role(
    data: StaffRoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a staff role (admin)."""
    service = SettingsService(db)
    role = await service.create_role(data)
    return StaffRoleResponse.model_validate(role)


@router.get("/roles/{role_id}", response_model=StaffRoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get role by ID (admin)."""
    service = SettingsService(db)
    role = await service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return StaffRoleResponse.model_validate(role)


@router.put("/roles/{role_id}", response_model=StaffRoleResponse)
async def update_role(
    role_id: int,
    data: StaffRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a role (admin)."""
    service = SettingsService(db)
    try:
        role = await service.update_role(role_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return StaffRoleResponse.model_validate(role)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a role (admin)."""
    service = SettingsService(db)
    try:
        deleted = await service.delete_role(role_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}


@router.post("/roles/seed")
async def seed_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Seed default roles (admin)."""
    service = SettingsService(db)
    await service.seed_default_roles()
    return {"message": "Default roles seeded"}


# =============================================================================
# STAFF MEMBER ENDPOINTS
# =============================================================================

@router.get("/staff", response_model=StaffMemberListResponse)
async def get_staff_members(
    role_id: Optional[int] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all staff members (admin)."""
    service = SettingsService(db)
    staff = await service.get_staff_members(
        role_id=role_id,
        department=department,
        is_active=is_active
    )
    return StaffMemberListResponse(
        items=[StaffMemberResponse.model_validate(s) for s in staff],
        total=len(staff)
    )


@router.post("/staff", response_model=StaffMemberResponse)
async def create_staff_member(
    data: StaffMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a staff member (admin)."""
    service = SettingsService(db)
    staff = await service.create_staff_member(
        data=data,
        created_by_id=current_user.id
    )
    return StaffMemberResponse.model_validate(staff)


@router.get("/staff/me", response_model=StaffMemberResponse)
async def get_my_staff_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's staff profile."""
    service = SettingsService(db)
    staff = await service.get_staff_member_by_user(current_user.id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff profile not found")
    return StaffMemberResponse.model_validate(staff)


@router.get("/staff/me/permissions", response_model=list[str])
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's effective permissions."""
    service = SettingsService(db)
    staff = await service.get_staff_member_by_user(current_user.id)
    
    if not staff or not staff.is_active:
        return []
    
    # Combine role permissions and additional permissions
    permissions = set()
    
    if staff.role and staff.role.permissions:
        permissions.update(staff.role.permissions)
    
    if staff.additional_permissions:
        permissions.update(staff.additional_permissions)
    
    # Remove restricted permissions
    if staff.restricted_permissions:
        permissions -= set(staff.restricted_permissions)
    
    return list(permissions)


@router.get("/staff/{staff_id}", response_model=StaffMemberResponse)
async def get_staff_member(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get staff member by ID (admin)."""
    service = SettingsService(db)
    staff = await service.get_staff_member(staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return StaffMemberResponse.model_validate(staff)


@router.put("/staff/{staff_id}", response_model=StaffMemberResponse)
async def update_staff_member(
    staff_id: int,
    data: StaffMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a staff member (admin)."""
    service = SettingsService(db)
    staff = await service.update_staff_member(staff_id, data)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return StaffMemberResponse.model_validate(staff)


@router.delete("/staff/{staff_id}")
async def delete_staff_member(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a staff member (admin)."""
    service = SettingsService(db)
    deleted = await service.delete_staff_member(staff_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return {"message": "Staff member deleted successfully"}


@router.get("/staff/{staff_id}/check-permission", response_model=StaffPermissionCheck)
async def check_staff_permission(
    staff_id: int,
    permission_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Check if staff member has a specific permission (admin)."""
    service = SettingsService(db)
    staff = await service.get_staff_member(staff_id)
    
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    has_perm, granted_by = await service.check_staff_permission(
        staff.user_id,
        permission_code
    )
    
    return StaffPermissionCheck(
        has_permission=has_perm,
        permission_code=permission_code,
        granted_by=granted_by
    )


# =============================================================================
# SYSTEM SETTING ENDPOINTS
# =============================================================================

@router.get("/system", response_model=SystemSettingListResponse)
async def get_system_settings(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all system settings (admin)."""
    service = SettingsService(db)
    settings = await service.get_settings(category=category)
    return SystemSettingListResponse(
        items=[SystemSettingResponse.model_validate(s) for s in settings],
        total=len(settings)
    )


@router.get("/system/by-category", response_model=list[SettingsByCategory])
async def get_settings_by_category(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get settings grouped by category (admin)."""
    service = SettingsService(db)
    return await service.get_settings_by_category()


@router.get("/system/public", response_model=PublicSettingsResponse)
async def get_public_settings(
    db: AsyncSession = Depends(get_db)
):
    """Get public settings for frontend."""
    service = SettingsService(db)
    settings = await service.get_public_settings()
    return PublicSettingsResponse(settings=settings)


@router.post("/system", response_model=SystemSettingResponse)
async def create_system_setting(
    data: SystemSettingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a system setting (admin)."""
    service = SettingsService(db)
    setting = await service.create_setting(data)
    return SystemSettingResponse.model_validate(setting)


@router.get("/system/{key}", response_model=SystemSettingResponse)
async def get_system_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get system setting by key (admin)."""
    service = SettingsService(db)
    setting = await service.get_setting(key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SystemSettingResponse.model_validate(setting)


@router.put("/system/{key}", response_model=SystemSettingResponse)
async def update_system_setting(
    key: str,
    data: SystemSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a system setting (admin)."""
    service = SettingsService(db)
    try:
        setting = await service.update_setting(
            key,
            data,
            updated_by_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SystemSettingResponse.model_validate(setting)


@router.delete("/system/{key}")
async def delete_system_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a system setting (admin)."""
    service = SettingsService(db)
    try:
        deleted = await service.delete_setting(key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"message": "Setting deleted successfully"}


@router.post("/system/seed")
async def seed_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Seed default settings (admin)."""
    service = SettingsService(db)
    await service.seed_default_settings()
    return {"message": "Default settings seeded"}
