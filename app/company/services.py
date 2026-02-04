"""
Company Settings Service Layer

Business logic for company profile, bank accounts, registration, and ACL.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.company.models import (
    CompanyProfile, BankAccount, BusinessRegistration,
    ACLModule, ACLPermission, ACLRole, ACLRolePermission, ACLUserRole
)

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for company settings and ACL."""
    
    def __init__(self, db: AsyncSession, tenant_id: int = 1):
        self.db = db
        self.tenant_id = tenant_id
    
    # =========================================================================
    # COMPANY PROFILE
    # =========================================================================
    
    async def get_company_profile(self) -> Optional[CompanyProfile]:
        """Get company profile for tenant."""
        stmt = select(CompanyProfile).where(
            CompanyProfile.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_company_profile(
        self,
        data: Dict[str, Any]
    ) -> CompanyProfile:
        """Create company profile."""
        profile = CompanyProfile(
            tenant_id=self.tenant_id,
            **data
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
    
    async def update_company_profile(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[CompanyProfile]:
        """Update company profile."""
        profile = await self.get_company_profile()
        
        if not profile:
            # Create if doesn't exist
            data['updated_by'] = updated_by
            return await self.create_company_profile(data)
        
        for key, value in data.items():
            if value is not None:
                setattr(profile, key, value)
        
        profile.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
    
    async def update_branding(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[CompanyProfile]:
        """Update only branding settings."""
        return await self.update_company_profile(data, updated_by)
    
    async def update_contact(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[CompanyProfile]:
        """Update only contact settings."""
        return await self.update_company_profile(data, updated_by)
    
    async def update_social(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[CompanyProfile]:
        """Update only social media settings."""
        return await self.update_company_profile(data, updated_by)
    
    async def update_seo(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[CompanyProfile]:
        """Update only SEO settings."""
        return await self.update_company_profile(data, updated_by)
    
    async def update_email_settings(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> Optional[CompanyProfile]:
        """Update only email/SMTP settings."""
        return await self.update_company_profile(data, updated_by)
    
    # =========================================================================
    # BANK ACCOUNTS
    # =========================================================================
    
    async def create_bank_account(
        self,
        data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> BankAccount:
        """Create bank account."""
        # If marking as primary, unset other primaries
        if data.get('is_primary'):
            await self._unset_primary_bank_accounts()
        
        account = BankAccount(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account
    
    async def get_bank_account(self, account_id: int) -> Optional[BankAccount]:
        """Get bank account by ID."""
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_bank_accounts(
        self,
        purpose: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[BankAccount]:
        """Get all bank accounts."""
        stmt = select(BankAccount).where(
            BankAccount.tenant_id == self.tenant_id
        )
        
        if purpose:
            stmt = stmt.where(BankAccount.purpose == purpose)
        if is_active is not None:
            stmt = stmt.where(BankAccount.is_active == is_active)
        
        stmt = stmt.order_by(BankAccount.display_order, BankAccount.id)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_bank_account(
        self,
        account_id: int,
        data: Dict[str, Any]
    ) -> Optional[BankAccount]:
        """Update bank account."""
        account = await self.get_bank_account(account_id)
        if not account:
            return None
        
        # If marking as primary, unset other primaries
        if data.get('is_primary'):
            await self._unset_primary_bank_accounts(exclude_id=account_id)
        
        for key, value in data.items():
            if value is not None:
                setattr(account, key, value)
        
        await self.db.commit()
        await self.db.refresh(account)
        return account
    
    async def delete_bank_account(self, account_id: int) -> bool:
        """Delete bank account."""
        account = await self.get_bank_account(account_id)
        if not account:
            return False
        
        await self.db.delete(account)
        await self.db.commit()
        return True
    
    async def _unset_primary_bank_accounts(
        self,
        exclude_id: Optional[int] = None
    ) -> None:
        """Unset primary flag on all bank accounts."""
        stmt = select(BankAccount).where(
            BankAccount.tenant_id == self.tenant_id,
            BankAccount.is_primary == True
        )
        if exclude_id:
            stmt = stmt.where(BankAccount.id != exclude_id)
        
        result = await self.db.execute(stmt)
        for account in result.scalars().all():
            account.is_primary = False
        
        await self.db.commit()
    
    # =========================================================================
    # BUSINESS REGISTRATION
    # =========================================================================
    
    async def get_business_registration(self) -> Optional[BusinessRegistration]:
        """Get business registration for tenant."""
        stmt = select(BusinessRegistration).where(
            BusinessRegistration.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_business_registration(
        self,
        data: Dict[str, Any],
        updated_by: Optional[int] = None
    ) -> BusinessRegistration:
        """Update or create business registration."""
        registration = await self.get_business_registration()
        
        if not registration:
            registration = BusinessRegistration(
                tenant_id=self.tenant_id,
                **data
            )
            self.db.add(registration)
        else:
            for key, value in data.items():
                if value is not None:
                    setattr(registration, key, value)
            registration.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(registration)
        return registration
    
    # =========================================================================
    # ACL MODULES
    # =========================================================================
    
    async def get_acl_modules(
        self,
        include_inactive: bool = False
    ) -> List[ACLModule]:
        """Get all ACL modules."""
        stmt = select(ACLModule)
        if not include_inactive:
            stmt = stmt.where(ACLModule.is_active == True)
        
        stmt = stmt.options(selectinload(ACLModule.permissions))
        stmt = stmt.order_by(ACLModule.display_order, ACLModule.id)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())
    
    async def get_acl_module(self, module_id: int) -> Optional[ACLModule]:
        """Get ACL module by ID."""
        stmt = select(ACLModule).where(ACLModule.id == module_id)
        stmt = stmt.options(selectinload(ACLModule.permissions))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_permissions(self) -> List[ACLPermission]:
        """Get all ACL permissions."""
        stmt = select(ACLPermission).where(ACLPermission.is_active == True)
        stmt = stmt.order_by(ACLPermission.module_id, ACLPermission.id)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # =========================================================================
    # ACL ROLES
    # =========================================================================
    
    async def create_acl_role(
        self,
        data: Dict[str, Any],
        permissions: List[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> ACLRole:
        """Create ACL role with permissions."""
        role = ACLRole(
            tenant_id=self.tenant_id,
            created_by=created_by,
            name=data.get('name'),
            display_name=data.get('display_name'),
            description=data.get('description'),
            is_default=data.get('is_default', False)
        )
        self.db.add(role)
        await self.db.flush()
        
        # Add permissions
        if permissions:
            for perm in permissions:
                role_perm = ACLRolePermission(
                    role_id=role.id,
                    permission_id=perm['permission_id'],
                    is_granted=perm.get('is_granted', True)
                )
                self.db.add(role_perm)
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_acl_role(self, role_id: int) -> Optional[ACLRole]:
        """Get ACL role by ID."""
        stmt = select(ACLRole).where(
            ACLRole.id == role_id,
            ACLRole.tenant_id == self.tenant_id
        )
        stmt = stmt.options(selectinload(ACLRole.role_permissions))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_acl_roles(
        self,
        is_active: Optional[bool] = True
    ) -> List[ACLRole]:
        """Get all ACL roles for tenant."""
        stmt = select(ACLRole).where(ACLRole.tenant_id == self.tenant_id)
        if is_active is not None:
            stmt = stmt.where(ACLRole.is_active == is_active)
        
        stmt = stmt.order_by(ACLRole.name)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_acl_role(
        self,
        role_id: int,
        data: Dict[str, Any],
        permissions: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[ACLRole]:
        """Update ACL role."""
        role = await self.get_acl_role(role_id)
        if not role:
            return None
        
        if role.is_system_role:
            # Can only update permissions for system roles
            pass
        else:
            for key in ['name', 'display_name', 'description', 'is_default', 'is_active']:
                if key in data and data[key] is not None:
                    setattr(role, key, data[key])
        
        # Update permissions if provided
        if permissions is not None:
            # Delete existing permissions
            for rp in role.role_permissions:
                await self.db.delete(rp)
            
            # Add new permissions
            for perm in permissions:
                role_perm = ACLRolePermission(
                    role_id=role.id,
                    permission_id=perm['permission_id'],
                    is_granted=perm.get('is_granted', True)
                )
                self.db.add(role_perm)
        
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def delete_acl_role(self, role_id: int) -> bool:
        """Delete ACL role."""
        role = await self.get_acl_role(role_id)
        if not role or role.is_system_role:
            return False
        
        await self.db.delete(role)
        await self.db.commit()
        return True
    
    async def get_role_permissions(self, role_id: int) -> List[ACLPermission]:
        """Get permissions for a role."""
        stmt = select(ACLPermission).join(
            ACLRolePermission,
            ACLRolePermission.permission_id == ACLPermission.id
        ).where(
            ACLRolePermission.role_id == role_id,
            ACLRolePermission.is_granted == True
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # =========================================================================
    # ACL USER ROLES
    # =========================================================================
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role_id: int,
        assigned_by: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> ACLUserRole:
        """Assign a role to a user."""
        # Check if already assigned
        stmt = select(ACLUserRole).where(
            ACLUserRole.user_id == user_id,
            ACLUserRole.role_id == role_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.is_active = True
            existing.assigned_by = assigned_by
            existing.assigned_at = datetime.utcnow()
            existing.expires_at = expires_at
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        user_role = ACLUserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )
        self.db.add(user_role)
        await self.db.commit()
        await self.db.refresh(user_role)
        return user_role
    
    async def remove_role_from_user(
        self,
        user_id: int,
        role_id: int
    ) -> bool:
        """Remove a role from a user."""
        stmt = select(ACLUserRole).where(
            ACLUserRole.user_id == user_id,
            ACLUserRole.role_id == role_id
        )
        result = await self.db.execute(stmt)
        user_role = result.scalar_one_or_none()
        
        if not user_role:
            return False
        
        user_role.is_active = False
        await self.db.commit()
        return True
    
    async def get_user_roles(self, user_id: int) -> List[ACLRole]:
        """Get all active roles for a user."""
        stmt = select(ACLRole).join(
            ACLUserRole,
            ACLUserRole.role_id == ACLRole.id
        ).where(
            ACLUserRole.user_id == user_id,
            ACLUserRole.is_active == True,
            or_(
                ACLUserRole.expires_at == None,
                ACLUserRole.expires_at > datetime.utcnow()
            )
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_permissions(self, user_id: int) -> Set[str]:
        """Get all effective permission codes for a user."""
        roles = await self.get_user_roles(user_id)
        permissions = set()
        
        for role in roles:
            role_perms = await self.get_role_permissions(role.id)
            for perm in role_perms:
                permissions.add(perm.code)
        
        return permissions
    
    async def user_has_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> bool:
        """Check if user has a specific permission."""
        permissions = await self.get_user_permissions(user_id)
        return permission_code in permissions
    
    # =========================================================================
    # SEEDING
    # =========================================================================
    
    async def seed_acl_modules_and_permissions(self) -> Tuple[int, int]:
        """Seed default ACL modules and permissions."""
        modules_data = [
            {
                'name': 'dashboard',
                'display_name': 'Dashboard',
                'icon': 'dashboard',
                'order': 0,
                'permissions': ['view']
            },
            {
                'name': 'bookings',
                'display_name': 'Bookings',
                'icon': 'book',
                'order': 1,
                'permissions': ['view', 'create', 'edit', 'delete', 'cancel', 'refund', 'export']
            },
            {
                'name': 'flights',
                'display_name': 'Flights',
                'icon': 'flight',
                'order': 2,
                'permissions': ['view', 'search', 'book', 'manage_markup']
            },
            {
                'name': 'hotels',
                'display_name': 'Hotels',
                'icon': 'hotel',
                'order': 3,
                'permissions': ['view', 'search', 'book', 'manage_markup']
            },
            {
                'name': 'packages',
                'display_name': 'Holiday Packages',
                'icon': 'beach_access',
                'order': 4,
                'permissions': ['view', 'create', 'edit', 'delete', 'publish']
            },
            {
                'name': 'visa',
                'display_name': 'Visa Services',
                'icon': 'card_travel',
                'order': 5,
                'permissions': ['view', 'create', 'edit', 'delete', 'process']
            },
            {
                'name': 'activities',
                'display_name': 'Activities',
                'icon': 'local_activity',
                'order': 6,
                'permissions': ['view', 'create', 'edit', 'delete']
            },
            {
                'name': 'transfers',
                'display_name': 'Transfers',
                'icon': 'directions_car',
                'order': 7,
                'permissions': ['view', 'create', 'edit', 'delete']
            },
            {
                'name': 'customers',
                'display_name': 'Customers',
                'icon': 'people',
                'order': 8,
                'permissions': ['view', 'create', 'edit', 'delete', 'export']
            },
            {
                'name': 'agents',
                'display_name': 'Agents',
                'icon': 'support_agent',
                'order': 9,
                'permissions': ['view', 'create', 'edit', 'delete', 'approve', 'manage_credit']
            },
            {
                'name': 'pricing',
                'display_name': 'Pricing & Markup',
                'icon': 'attach_money',
                'order': 10,
                'permissions': ['view', 'create', 'edit', 'delete']
            },
            {
                'name': 'reports',
                'display_name': 'Reports',
                'icon': 'assessment',
                'order': 11,
                'permissions': ['view', 'export', 'schedule']
            },
            {
                'name': 'cms',
                'display_name': 'Content Management',
                'icon': 'article',
                'order': 12,
                'permissions': ['view', 'create', 'edit', 'delete', 'publish']
            },
            {
                'name': 'settings',
                'display_name': 'Settings',
                'icon': 'settings',
                'order': 13,
                'permissions': ['view', 'edit']
            },
            {
                'name': 'users',
                'display_name': 'User Management',
                'icon': 'manage_accounts',
                'order': 14,
                'permissions': ['view', 'create', 'edit', 'delete', 'manage_roles']
            },
        ]
        
        modules_created = 0
        permissions_created = 0
        
        for module_data in modules_data:
            # Check if module exists
            stmt = select(ACLModule).where(ACLModule.name == module_data['name'])
            result = await self.db.execute(stmt)
            module = result.scalar_one_or_none()
            
            if not module:
                module = ACLModule(
                    name=module_data['name'],
                    display_name=module_data['display_name'],
                    icon=module_data.get('icon'),
                    display_order=module_data.get('order', 0)
                )
                self.db.add(module)
                await self.db.flush()
                modules_created += 1
            
            # Create permissions
            for perm_name in module_data.get('permissions', []):
                code = f"{module_data['name']}.{perm_name}"
                
                stmt = select(ACLPermission).where(ACLPermission.code == code)
                result = await self.db.execute(stmt)
                if not result.scalar_one_or_none():
                    permission = ACLPermission(
                        module_id=module.id,
                        name=perm_name,
                        display_name=perm_name.replace('_', ' ').title(),
                        code=code
                    )
                    self.db.add(permission)
                    permissions_created += 1
        
        await self.db.commit()
        return modules_created, permissions_created
    
    async def seed_default_roles(self) -> List[ACLRole]:
        """Seed default ACL roles."""
        roles_data = [
            {
                'name': 'super_admin',
                'display_name': 'Super Administrator',
                'description': 'Full access to all features',
                'is_system_role': True,
                'permissions': '*'  # All permissions
            },
            {
                'name': 'admin',
                'display_name': 'Administrator',
                'description': 'Administrative access excluding system settings',
                'is_system_role': True,
                'permissions': [
                    'dashboard.view', 'bookings.*', 'flights.*', 'hotels.*',
                    'packages.*', 'visa.*', 'activities.*', 'transfers.*',
                    'customers.*', 'agents.*', 'pricing.*', 'reports.*', 'cms.*'
                ]
            },
            {
                'name': 'manager',
                'display_name': 'Manager',
                'description': 'Can manage bookings and agents',
                'is_system_role': True,
                'permissions': [
                    'dashboard.view', 'bookings.view', 'bookings.edit',
                    'flights.view', 'flights.search', 'hotels.view', 'hotels.search',
                    'customers.view', 'agents.view', 'reports.view'
                ]
            },
            {
                'name': 'staff',
                'display_name': 'Staff',
                'description': 'Basic staff access',
                'is_system_role': True,
                'permissions': [
                    'dashboard.view', 'bookings.view', 'bookings.create',
                    'flights.view', 'flights.search', 'flights.book',
                    'hotels.view', 'hotels.search', 'hotels.book',
                    'customers.view'
                ]
            },
            {
                'name': 'agent',
                'display_name': 'Agent',
                'description': 'B2B Agent access',
                'is_system_role': True,
                'is_default': True,
                'permissions': [
                    'dashboard.view', 'bookings.view', 'bookings.create',
                    'flights.view', 'flights.search', 'flights.book',
                    'hotels.view', 'hotels.search', 'hotels.book'
                ]
            },
        ]
        
        # Get all permissions
        all_perms = await self.get_all_permissions()
        perm_map = {p.code: p.id for p in all_perms}
        
        created_roles = []
        
        for role_data in roles_data:
            # Check if role exists
            stmt = select(ACLRole).where(
                ACLRole.tenant_id == self.tenant_id,
                ACLRole.name == role_data['name']
            )
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                continue
            
            role = ACLRole(
                tenant_id=self.tenant_id,
                name=role_data['name'],
                display_name=role_data['display_name'],
                description=role_data.get('description'),
                is_system_role=role_data.get('is_system_role', False),
                is_default=role_data.get('is_default', False)
            )
            self.db.add(role)
            await self.db.flush()
            
            # Add permissions
            if role_data.get('permissions') == '*':
                # All permissions
                for perm_id in perm_map.values():
                    role_perm = ACLRolePermission(
                        role_id=role.id,
                        permission_id=perm_id
                    )
                    self.db.add(role_perm)
            else:
                for perm_code in role_data.get('permissions', []):
                    if perm_code.endswith('.*'):
                        # Wildcard - add all permissions for module
                        module_name = perm_code[:-2]
                        for code, perm_id in perm_map.items():
                            if code.startswith(f"{module_name}."):
                                role_perm = ACLRolePermission(
                                    role_id=role.id,
                                    permission_id=perm_id
                                )
                                self.db.add(role_perm)
                    elif perm_code in perm_map:
                        role_perm = ACLRolePermission(
                            role_id=role.id,
                            permission_id=perm_map[perm_code]
                        )
                        self.db.add(role_perm)
            
            created_roles.append(role)
        
        await self.db.commit()
        return created_roles
