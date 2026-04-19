"""
Settings Service Layer

Business logic for settings and staff management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple, Any, Dict
from datetime import datetime

from app.settings.models import (
    ConvenienceFee, StaffRole, StaffPermission, StaffMember,
    SystemSetting, PaymentMode, AirportCode, AirlineCode
)
from app.settings.schemas import (
    ConvenienceFeeCreate, ConvenienceFeeUpdate,
    FeeCalculationRequest, FeeCalculationResponse,
    StaffPermissionCreate,
    StaffRoleCreate, StaffRoleUpdate,
    StaffMemberCreate, StaffMemberUpdate,
    SystemSettingCreate, SystemSettingUpdate,
    PermissionsByModule, SettingsByCategory,
    StaffPermissionResponse, SystemSettingResponse
)


class SettingsService:
    """Service for settings and staff management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # CONVENIENCE FEE OPERATIONS
    # =========================================================================
    
    async def create_convenience_fee(
        self,
        data: ConvenienceFeeCreate,
        created_by_id: int,
        tenant_id: Optional[int] = None
    ) -> ConvenienceFee:
        """Create a convenience fee configuration."""
        fee = ConvenienceFee(
            **data.model_dump(),
            created_by_id=created_by_id,
            tenant_id=tenant_id
        )
        self.db.add(fee)
        await self.db.commit()
        await self.db.refresh(fee)
        return fee
    
    async def update_convenience_fee(
        self,
        fee_id: int,
        data: ConvenienceFeeUpdate
    ) -> Optional[ConvenienceFee]:
        """Update a convenience fee."""
        result = await self.db.execute(
            select(ConvenienceFee).where(ConvenienceFee.id == fee_id)
        )
        fee = result.scalar_one_or_none()
        
        if not fee:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(fee, key, value)
        
        await self.db.commit()
        await self.db.refresh(fee)
        return fee
    
    async def get_convenience_fee(self, fee_id: int) -> Optional[ConvenienceFee]:
        """Get convenience fee by ID."""
        result = await self.db.execute(
            select(ConvenienceFee).where(ConvenienceFee.id == fee_id)
        )
        return result.scalar_one_or_none()
    
    async def get_convenience_fees(
        self,
        service_type: Optional[str] = None,
        payment_mode: Optional[PaymentMode] = None,
        is_active: Optional[bool] = None,
        tenant_id: Optional[int] = None
    ) -> List[ConvenienceFee]:
        """Get convenience fees with filters."""
        query = select(ConvenienceFee)
        
        conditions = []
        if service_type:
            conditions.append(
                or_(
                    ConvenienceFee.service_type == service_type,
                    ConvenienceFee.service_type == "all"
                )
            )
        if payment_mode:
            conditions.append(ConvenienceFee.payment_mode == payment_mode)
        if is_active is not None:
            conditions.append(ConvenienceFee.is_active == is_active)
        if tenant_id:
            conditions.append(
                or_(
                    ConvenienceFee.tenant_id == tenant_id,
                    ConvenienceFee.tenant_id.is_(None)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(ConvenienceFee.service_type, ConvenienceFee.payment_mode)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def calculate_convenience_fee(
        self,
        data: FeeCalculationRequest,
        tenant_id: Optional[int] = None
    ) -> FeeCalculationResponse:
        """Calculate convenience fee for a transaction."""
        # Find matching fee configuration
        fees = await self.get_convenience_fees(
            service_type=data.service_type,
            payment_mode=data.payment_mode,
            is_active=True,
            tenant_id=tenant_id
        )
        
        # Prefer specific service type over 'all'
        fee_config = None
        for fee in fees:
            if fee.service_type == data.service_type:
                fee_config = fee
                break
            if fee.service_type == "all":
                fee_config = fee
        
        if not fee_config:
            # No fee configured
            return FeeCalculationResponse(
                base_amount=data.amount,
                fee_amount=0,
                gst_on_fee=0,
                total_fee=0,
                total_amount=data.amount,
                fee_breakdown={"message": "No convenience fee configured"}
            )
        
        # Calculate fee
        fee_amount = 0
        
        if fee_config.fee_type == "percentage":
            fee_amount = (data.amount * fee_config.percentage) / 100
        elif fee_config.fee_type == "fixed":
            fee_amount = fee_config.fixed_amount
        elif fee_config.fee_type == "both":
            percentage_fee = (data.amount * fee_config.percentage) / 100
            fee_amount = percentage_fee + fee_config.fixed_amount
        
        # Apply min/max
        if fee_amount < fee_config.min_fee:
            fee_amount = fee_config.min_fee
        if fee_config.max_fee and fee_amount > fee_config.max_fee:
            fee_amount = fee_config.max_fee
        
        # Calculate GST on fee
        gst_on_fee = (fee_amount * fee_config.gst_percentage) / 100
        total_fee = fee_amount + gst_on_fee
        
        return FeeCalculationResponse(
            base_amount=data.amount,
            fee_amount=round(fee_amount, 2),
            gst_on_fee=round(gst_on_fee, 2),
            total_fee=round(total_fee, 2),
            total_amount=round(data.amount + total_fee, 2),
            fee_breakdown={
                "fee_type": fee_config.fee_type,
                "percentage": fee_config.percentage,
                "fixed_amount": fee_config.fixed_amount,
                "gst_percentage": fee_config.gst_percentage
            }
        )
    
    async def delete_convenience_fee(self, fee_id: int) -> bool:
        """Delete a convenience fee."""
        result = await self.db.execute(
            select(ConvenienceFee).where(ConvenienceFee.id == fee_id)
        )
        fee = result.scalar_one_or_none()
        
        if not fee:
            return False
        
        await self.db.delete(fee)
        await self.db.commit()
        return True
    
    # =========================================================================
    # PERMISSION OPERATIONS
    # =========================================================================
    
    async def create_permission(
        self,
        data: StaffPermissionCreate
    ) -> StaffPermission:
        """Create a permission."""
        permission = StaffPermission(**data.model_dump())
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def get_permission(self, code: str) -> Optional[StaffPermission]:
        """Get permission by code."""
        result = await self.db.execute(
            select(StaffPermission).where(StaffPermission.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_all_permissions(self) -> List[StaffPermission]:
        """Get all permissions."""
        result = await self.db.execute(
            select(StaffPermission).order_by(
                StaffPermission.module,
                StaffPermission.display_order
            )
        )
        return list(result.scalars().all())
    
    async def get_permissions_by_module(self) -> List[PermissionsByModule]:
        """Get permissions grouped by module."""
        permissions = await self.get_all_permissions()
        
        modules: Dict[str, List[StaffPermission]] = {}
        for perm in permissions:
            if perm.module not in modules:
                modules[perm.module] = []
            modules[perm.module].append(perm)
        
        return [
            PermissionsByModule(
                module=module,
                permissions=[
                    StaffPermissionResponse.model_validate(p) for p in perms
                ]
            )
            for module, perms in modules.items()
        ]
    
    async def seed_default_permissions(self) -> None:
        """Seed default permissions if not exist."""
        default_permissions = [
            # Bookings
            ("bookings.view", "View Bookings", "View all bookings", "bookings", 1),
            ("bookings.create", "Create Bookings", "Create new bookings", "bookings", 2),
            ("bookings.edit", "Edit Bookings", "Edit booking details", "bookings", 3),
            ("bookings.cancel", "Cancel Bookings", "Cancel bookings", "bookings", 4),
            ("bookings.refund", "Process Refunds", "Process booking refunds", "bookings", 5),
            
            # Users
            ("users.view", "View Users", "View user list and details", "users", 1),
            ("users.create", "Create Users", "Create new users", "users", 2),
            ("users.edit", "Edit Users", "Edit user details", "users", 3),
            ("users.delete", "Delete Users", "Delete users", "users", 4),
            
            # Agents
            ("agents.view", "View Agents", "View agent list and details", "agents", 1),
            ("agents.approve", "Approve Agents", "Approve agent registrations", "agents", 2),
            ("agents.edit", "Edit Agents", "Edit agent details", "agents", 3),
            ("agents.wallet", "Manage Agent Wallet", "Manage agent wallet balances", "agents", 4),
            
            # Content
            ("content.sliders", "Manage Sliders", "Create/edit homepage sliders", "content", 1),
            ("content.offers", "Manage Offers", "Create/edit offers and coupons", "content", 2),
            ("content.blog", "Manage Blog", "Create/edit blog posts", "content", 3),
            ("content.pages", "Manage Pages", "Create/edit static pages", "content", 4),
            
            # Products
            ("products.holidays", "Manage Holidays", "Manage holiday packages", "products", 1),
            ("products.visa", "Manage Visa", "Manage visa services", "products", 2),
            ("products.activities", "Manage Activities", "Manage activities", "products", 3),
            ("products.transfers", "Manage Transfers", "Manage transfer services", "products", 4),
            
            # Settings
            ("settings.fees", "Manage Fees", "Manage convenience fees", "settings", 1),
            ("settings.roles", "Manage Roles", "Manage staff roles", "settings", 2),
            ("settings.staff", "Manage Staff", "Manage staff members", "settings", 3),
            ("settings.system", "System Settings", "Manage system settings", "settings", 4),
            
            # Reports
            ("reports.view", "View Reports", "View business reports", "reports", 1),
            ("reports.export", "Export Reports", "Export reports to files", "reports", 2),
            ("reports.financial", "Financial Reports", "View financial reports", "reports", 3),
        ]
        
        for code, name, description, module, order in default_permissions:
            existing = await self.get_permission(code)
            if not existing:
                await self.create_permission(StaffPermissionCreate(
                    code=code,
                    name=name,
                    description=description,
                    module=module,
                    display_order=order
                ))
    
    # =========================================================================
    # ROLE OPERATIONS
    # =========================================================================
    
    async def create_role(
        self,
        data: StaffRoleCreate,
        tenant_id: Optional[int] = None
    ) -> StaffRole:
        """Create a staff role."""
        role = StaffRole(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def update_role(
        self,
        role_id: int,
        data: StaffRoleUpdate
    ) -> Optional[StaffRole]:
        """Update a staff role."""
        result = await self.db.execute(
            select(StaffRole).where(StaffRole.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            return None
        
        if role.is_system and 'name' in data.model_dump(exclude_unset=True):
            raise ValueError("Cannot rename system role")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(role, key, value)
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_role(self, role_id: int) -> Optional[StaffRole]:
        """Get role by ID."""
        result = await self.db.execute(
            select(StaffRole).where(StaffRole.id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_role_by_name(self, name: str) -> Optional[StaffRole]:
        """Get role by name."""
        result = await self.db.execute(
            select(StaffRole).where(StaffRole.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_roles(
        self,
        is_active: Optional[bool] = None,
        tenant_id: Optional[int] = None
    ) -> List[StaffRole]:
        """Get all roles."""
        query = select(StaffRole)
        
        conditions = []
        if is_active is not None:
            conditions.append(StaffRole.is_active == is_active)
        if tenant_id:
            conditions.append(
                or_(
                    StaffRole.tenant_id == tenant_id,
                    StaffRole.tenant_id.is_(None)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(StaffRole.is_system.desc(), StaffRole.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_role(self, role_id: int) -> bool:
        """Delete a role."""
        result = await self.db.execute(
            select(StaffRole).where(StaffRole.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            return False
        
        if role.is_system:
            raise ValueError("Cannot delete system role")
        
        await self.db.delete(role)
        await self.db.commit()
        return True
    
    async def seed_default_roles(self) -> None:
        """Seed default roles."""
        default_roles = [
            (
                "Super Admin",
                "Full access to all features",
                [
                    "bookings.view", "bookings.create", "bookings.edit", 
                    "bookings.cancel", "bookings.refund",
                    "users.view", "users.create", "users.edit", "users.delete",
                    "agents.view", "agents.approve", "agents.edit", "agents.wallet",
                    "content.sliders", "content.offers", "content.blog", "content.pages",
                    "products.holidays", "products.visa", "products.activities", "products.transfers",
                    "settings.fees", "settings.roles", "settings.staff", "settings.system",
                    "reports.view", "reports.export", "reports.financial"
                ],
                True
            ),
            (
                "Manager",
                "Manage day-to-day operations",
                [
                    "bookings.view", "bookings.create", "bookings.edit", "bookings.cancel",
                    "users.view", "users.edit",
                    "agents.view", "agents.edit",
                    "content.sliders", "content.offers", "content.blog",
                    "products.holidays", "products.visa", "products.activities", "products.transfers",
                    "reports.view", "reports.export"
                ],
                True
            ),
            (
                "Agent Support",
                "Handle agent queries and approvals",
                [
                    "bookings.view",
                    "agents.view", "agents.approve", "agents.edit",
                    "reports.view"
                ],
                True
            ),
            (
                "Content Manager",
                "Manage website content",
                [
                    "content.sliders", "content.offers", "content.blog", "content.pages"
                ],
                True
            ),
            (
                "Support Staff",
                "Basic support access",
                [
                    "bookings.view",
                    "users.view",
                    "agents.view"
                ],
                True
            ),
        ]
        
        for name, description, permissions, is_system in default_roles:
            existing = await self.get_role_by_name(name)
            if not existing:
                role = StaffRole(
                    name=name,
                    description=description,
                    permissions=permissions,
                    is_system=is_system
                )
                self.db.add(role)
        
        await self.db.commit()
    
    # =========================================================================
    # STAFF MEMBER OPERATIONS
    # =========================================================================
    
    async def create_staff_member(
        self,
        data: StaffMemberCreate,
        created_by_id: int,
        tenant_id: Optional[int] = None
    ) -> StaffMember:
        """Create a staff member."""
        staff = StaffMember(
            **data.model_dump(),
            created_by_id=created_by_id,
            tenant_id=tenant_id
        )
        self.db.add(staff)
        await self.db.commit()
        
        # Reload with relationships
        result = await self.db.execute(
            select(StaffMember)
            .options(
                selectinload(StaffMember.user),
                selectinload(StaffMember.role)
            )
            .where(StaffMember.id == staff.id)
        )
        return result.scalar_one()
    
    async def update_staff_member(
        self,
        staff_id: int,
        data: StaffMemberUpdate
    ) -> Optional[StaffMember]:
        """Update a staff member."""
        result = await self.db.execute(
            select(StaffMember).where(StaffMember.id == staff_id)
        )
        staff = result.scalar_one_or_none()
        
        if not staff:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(staff, key, value)
        
        await self.db.commit()
        
        # Reload with relationships
        result = await self.db.execute(
            select(StaffMember)
            .options(
                selectinload(StaffMember.user),
                selectinload(StaffMember.role)
            )
            .where(StaffMember.id == staff_id)
        )
        return result.scalar_one()
    
    async def get_staff_member(self, staff_id: int) -> Optional[StaffMember]:
        """Get staff member by ID."""
        result = await self.db.execute(
            select(StaffMember)
            .options(
                selectinload(StaffMember.user),
                selectinload(StaffMember.role)
            )
            .where(StaffMember.id == staff_id)
        )
        return result.scalar_one_or_none()
    
    async def get_staff_member_by_user(self, user_id: int) -> Optional[StaffMember]:
        """Get staff member by user ID."""
        result = await self.db.execute(
            select(StaffMember)
            .options(
                selectinload(StaffMember.user),
                selectinload(StaffMember.role)
            )
            .where(StaffMember.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_staff_members(
        self,
        role_id: Optional[int] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
        tenant_id: Optional[int] = None
    ) -> List[StaffMember]:
        """Get staff members with filters."""
        query = select(StaffMember).options(
            selectinload(StaffMember.user),
            selectinload(StaffMember.role)
        )
        
        conditions = []
        if role_id:
            conditions.append(StaffMember.role_id == role_id)
        if department:
            conditions.append(StaffMember.department == department)
        if is_active is not None:
            conditions.append(StaffMember.is_active == is_active)
        if tenant_id:
            conditions.append(StaffMember.tenant_id == tenant_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(StaffMember.id.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def check_staff_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if staff member has a permission."""
        staff = await self.get_staff_member_by_user(user_id)
        
        if not staff or not staff.is_active:
            return False, None
        
        # Check if explicitly restricted
        if staff.restricted_permissions:
            if permission_code in staff.restricted_permissions:
                return False, "denied"
        
        # Check additional permissions first
        if staff.additional_permissions:
            if permission_code in staff.additional_permissions:
                return True, "additional"
        
        # Check role permissions
        if staff.role and staff.role.permissions:
            if permission_code in staff.role.permissions:
                return True, "role"
        
        return False, None
    
    async def update_last_login(self, user_id: int) -> None:
        """Update staff last login time."""
        staff = await self.get_staff_member_by_user(user_id)
        if staff:
            staff.last_login_at = datetime.utcnow()
            await self.db.commit()
    
    async def delete_staff_member(self, staff_id: int) -> bool:
        """Delete a staff member."""
        result = await self.db.execute(
            select(StaffMember).where(StaffMember.id == staff_id)
        )
        staff = result.scalar_one_or_none()
        
        if not staff:
            return False
        
        await self.db.delete(staff)
        await self.db.commit()
        return True
    
    # =========================================================================
    # SYSTEM SETTING OPERATIONS
    # =========================================================================
    
    async def create_setting(
        self,
        data: SystemSettingCreate,
        tenant_id: Optional[int] = None
    ) -> SystemSetting:
        """Create a system setting."""
        setting = SystemSetting(
            **data.model_dump(),
            tenant_id=tenant_id
        )
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
    
    async def update_setting(
        self,
        key: str,
        data: SystemSettingUpdate,
        updated_by_id: int,
        tenant_id: Optional[int] = None
    ) -> Optional[SystemSetting]:
        """Update a system setting."""
        query = select(SystemSetting).where(SystemSetting.key == key)
        if tenant_id:
            query = query.where(SystemSetting.tenant_id == tenant_id)
        else:
            query = query.where(SystemSetting.tenant_id.is_(None))
        
        result = await self.db.execute(query)
        setting = result.scalar_one_or_none()
        
        if not setting:
            return None
        
        if not setting.is_editable:
            raise ValueError("This setting cannot be edited")
        
        update_data = data.model_dump(exclude_unset=True)
        update_data['updated_by_id'] = updated_by_id
        
        for key_name, value in update_data.items():
            setattr(setting, key_name, value)
        
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
    
    async def get_setting(
        self,
        key: str,
        tenant_id: Optional[int] = None
    ) -> Optional[SystemSetting]:
        """Get setting by key."""
        query = select(SystemSetting).where(SystemSetting.key == key)
        
        # Check tenant-specific first, then global
        if tenant_id:
            query = query.where(
                or_(
                    SystemSetting.tenant_id == tenant_id,
                    SystemSetting.tenant_id.is_(None)
                )
            ).order_by(SystemSetting.tenant_id.desc().nullslast())
        else:
            query = query.where(SystemSetting.tenant_id.is_(None))
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_setting_value(
        self,
        key: str,
        default: Any = None,
        tenant_id: Optional[int] = None
    ) -> Any:
        """Get setting value with type conversion."""
        setting = await self.get_setting(key, tenant_id)
        
        if not setting:
            return default
        
        return setting.value
    
    async def get_settings(
        self,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        tenant_id: Optional[int] = None
    ) -> List[SystemSetting]:
        """Get settings with filters."""
        query = select(SystemSetting)
        
        conditions = []
        if category:
            conditions.append(SystemSetting.category == category)
        if is_public is not None:
            conditions.append(SystemSetting.is_public == is_public)
        if tenant_id:
            conditions.append(
                or_(
                    SystemSetting.tenant_id == tenant_id,
                    SystemSetting.tenant_id.is_(None)
                )
            )
        else:
            conditions.append(SystemSetting.tenant_id.is_(None))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(SystemSetting.category, SystemSetting.key)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_settings_by_category(
        self,
        tenant_id: Optional[int] = None
    ) -> List[SettingsByCategory]:
        """Get settings grouped by category."""
        settings = await self.get_settings(tenant_id=tenant_id)
        
        categories: Dict[str, List[SystemSetting]] = {}
        for setting in settings:
            if setting.category not in categories:
                categories[setting.category] = []
            categories[setting.category].append(setting)
        
        return [
            SettingsByCategory(
                category=category,
                settings=[
                    SystemSettingResponse.model_validate(s) for s in setts
                ]
            )
            for category, setts in categories.items()
        ]
    
    async def get_public_settings(
        self,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get all public settings as key-value pairs."""
        settings = await self.get_settings(
            is_public=True,
            tenant_id=tenant_id
        )
        
        return {s.key: s.value for s in settings}
    
    async def delete_setting(
        self,
        key: str,
        tenant_id: Optional[int] = None
    ) -> bool:
        """Delete a system setting."""
        query = select(SystemSetting).where(SystemSetting.key == key)
        if tenant_id:
            query = query.where(SystemSetting.tenant_id == tenant_id)
        else:
            query = query.where(SystemSetting.tenant_id.is_(None))
        
        result = await self.db.execute(query)
        setting = result.scalar_one_or_none()
        
        if not setting:
            return False
        
        if not setting.is_editable:
            raise ValueError("This setting cannot be deleted")
        
        await self.db.delete(setting)
        await self.db.commit()
        return True
    
    async def seed_default_settings(self) -> None:
        """Seed default system settings."""
        default_settings = [
            ("site_name", "Trurism", "string", "general", "Website name", True),
            ("site_tagline", "Your Travel Partner", "string", "general", "Website tagline", True),
            ("support_email", "support@trurism.com", "string", "general", "Support email", True),
            ("support_phone", "+91-XXXXXXXXXX", "string", "general", "Support phone", True),
            ("gst_percentage", 18.0, "number", "tax", "Default GST percentage", False),
            ("tds_percentage", 1.0, "number", "tax", "TDS percentage for agents", False),
            ("min_wallet_balance", 0, "number", "wallet", "Minimum wallet balance", False),
            ("max_wallet_topup", 500000, "number", "wallet", "Maximum wallet top-up amount", False),
            ("booking_email_enabled", True, "boolean", "notifications", "Send booking emails", False),
            ("sms_enabled", True, "boolean", "notifications", "SMS notifications enabled", False),
        ]
        
        for key, value, value_type, category, description, is_public in default_settings:
            existing = await self.get_setting(key)
            if not existing:
                setting = SystemSetting(
                    key=key,
                    value=value,
                    value_type=value_type,
                    category=category,
                    description=description,
                    is_public=is_public
                )
                self.db.add(setting)
        
        await self.db.commit()

    # =========================
    # AIRPORT METHODS
    # =========================
    async def create_airport(self, data):
        obj = AirportCode(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_airports(self):
        result = await self.db.execute(
            select(AirportCode).where(AirportCode.is_active == True)
        )
        return result.scalars().all()

    async def update_airport(self, code, data):
        result = await self.db.execute(
            select(AirportCode).where(AirportCode.code == code)
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return None

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)

        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete_airport(self, code):
        result = await self.db.execute(
            select(AirportCode).where(AirportCode.code == code)
        )
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        
        await self.db.delete(obj)
        await self.db.commit()
        return True