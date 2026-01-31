"""
Visa Services

Business logic for visa operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any, List
from datetime import datetime
import secrets
import re
import logging

from app.visa.models import (
    VisaCountry, VisaType, VisaRequirement,
    VisaApplication, ApplicationStatus
)

logger = logging.getLogger(__name__)


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:200]


def generate_ref(prefix: str = "VSA") -> str:
    """Generate unique reference number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()
    return f"{prefix}{timestamp}{random_part}"


class VisaService:
    """
    Service for visa management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # Country Management
    # =========================================================================
    
    async def create_country(
        self,
        name: str,
        slug: Optional[str] = None,
        **kwargs
    ) -> VisaCountry:
        """Create a new visa country."""
        country = VisaCountry(
            name=name,
            slug=slug or generate_slug(name),
            **kwargs
        )
        self.db.add(country)
        await self.db.commit()
        await self.db.refresh(country)
        return country
    
    async def get_countries(
        self,
        active_only: bool = True,
        popular_only: bool = False
    ) -> List[VisaCountry]:
        """Get all visa countries."""
        query = select(VisaCountry)
        
        if active_only:
            query = query.where(VisaCountry.is_active == True)
        
        if popular_only:
            query = query.where(VisaCountry.is_popular == True)
        
        query = query.order_by(VisaCountry.display_order, VisaCountry.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_country(
        self,
        country_id: Optional[int] = None,
        slug: Optional[str] = None,
        include_types: bool = False
    ) -> Optional[VisaCountry]:
        """Get country by ID or slug."""
        query = select(VisaCountry)
        
        if country_id:
            query = query.where(VisaCountry.id == country_id)
        elif slug:
            query = query.where(VisaCountry.slug == slug)
        else:
            return None
        
        if include_types:
            query = query.options(
                selectinload(VisaCountry.visa_types).selectinload(VisaType.requirements)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_country(
        self,
        country_id: int,
        **updates
    ) -> Optional[VisaCountry]:
        """Update a country."""
        country = await self.get_country(country_id)
        if not country:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(country, key):
                setattr(country, key, value)
        
        await self.db.commit()
        await self.db.refresh(country)
        return country
    
    async def search_countries(
        self,
        query: Optional[str] = None,
        is_popular: Optional[bool] = None,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search countries with filters."""
        stmt = select(VisaCountry)
        conditions = []
        
        if active_only:
            conditions.append(VisaCountry.is_active == True)
        
        if query:
            search_term = f"%{query}%"
            conditions.append(
                or_(
                    VisaCountry.name.ilike(search_term),
                    VisaCountry.code.ilike(search_term)
                )
            )
        
        if is_popular is not None:
            conditions.append(VisaCountry.is_popular == is_popular)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(VisaCountry.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Order and paginate
        stmt = stmt.order_by(VisaCountry.display_order, VisaCountry.name)
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        countries = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "countries": countries,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    # =========================================================================
    # Visa Type Management
    # =========================================================================
    
    async def create_visa_type(
        self,
        country_id: int,
        name: str,
        slug: Optional[str] = None,
        **kwargs
    ) -> VisaType:
        """Create a new visa type."""
        visa_type = VisaType(
            country_id=country_id,
            name=name,
            slug=slug or generate_slug(name),
            **kwargs
        )
        self.db.add(visa_type)
        await self.db.commit()
        await self.db.refresh(visa_type)
        return visa_type
    
    async def get_visa_types(
        self,
        country_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[VisaType]:
        """Get visa types, optionally filtered by country."""
        query = select(VisaType).options(selectinload(VisaType.country))
        
        if country_id:
            query = query.where(VisaType.country_id == country_id)
        
        if active_only:
            query = query.where(VisaType.is_active == True)
        
        query = query.order_by(VisaType.display_order, VisaType.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_visa_type(
        self,
        visa_type_id: Optional[int] = None,
        slug: Optional[str] = None,
        include_requirements: bool = True
    ) -> Optional[VisaType]:
        """Get visa type by ID or slug."""
        query = select(VisaType).options(selectinload(VisaType.country))
        
        if visa_type_id:
            query = query.where(VisaType.id == visa_type_id)
        elif slug:
            query = query.where(VisaType.slug == slug)
        else:
            return None
        
        if include_requirements:
            query = query.options(selectinload(VisaType.requirements))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_visa_type(
        self,
        visa_type_id: int,
        **updates
    ) -> Optional[VisaType]:
        """Update a visa type."""
        visa_type = await self.get_visa_type(visa_type_id, include_requirements=False)
        if not visa_type:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(visa_type, key):
                setattr(visa_type, key, value)
        
        await self.db.commit()
        await self.db.refresh(visa_type)
        return visa_type
    
    # =========================================================================
    # Requirement Management
    # =========================================================================
    
    async def add_requirement(
        self,
        visa_type_id: int,
        category: str,
        title: str,
        **kwargs
    ) -> VisaRequirement:
        """Add requirement to a visa type."""
        requirement = VisaRequirement(
            visa_type_id=visa_type_id,
            category=category,
            title=title,
            **kwargs
        )
        self.db.add(requirement)
        await self.db.commit()
        await self.db.refresh(requirement)
        return requirement
    
    async def update_requirement(
        self,
        requirement_id: int,
        **updates
    ) -> Optional[VisaRequirement]:
        """Update a requirement."""
        result = await self.db.execute(
            select(VisaRequirement).where(VisaRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(requirement, key):
                setattr(requirement, key, value)
        
        await self.db.commit()
        await self.db.refresh(requirement)
        return requirement
    
    async def delete_requirement(self, requirement_id: int) -> bool:
        """Delete a requirement."""
        result = await self.db.execute(
            select(VisaRequirement).where(VisaRequirement.id == requirement_id)
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            return False
        await self.db.delete(requirement)
        await self.db.commit()
        return True
    
    # =========================================================================
    # Application Management
    # =========================================================================
    
    async def create_application(
        self,
        visa_type_id: int,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        user_id: Optional[int] = None,
        is_express: bool = False,
        **kwargs
    ) -> VisaApplication:
        """Create a new visa application."""
        # Get visa type for pricing
        visa_type = await self.get_visa_type(visa_type_id, include_requirements=False)
        if not visa_type:
            raise ValueError(f"Visa type {visa_type_id} not found")
        
        # Calculate pricing
        base_amount = visa_type.total_price
        express_fee = visa_type.express_price if is_express and visa_type.is_express_available else 0
        taxes = (base_amount + express_fee) * 0.18  # GST
        total_amount = base_amount + express_fee + taxes
        
        application = VisaApplication(
            application_ref=generate_ref("VSA"),
            visa_type_id=visa_type_id,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            is_express=is_express,
            base_amount=base_amount,
            express_fee=express_fee or 0,
            taxes=taxes,
            total_amount=total_amount,
            status=ApplicationStatus.DRAFT,
            **kwargs
        )
        
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        
        logger.info(f"Created visa application {application.application_ref}")
        return application
    
    async def get_application(
        self,
        application_id: Optional[int] = None,
        application_ref: Optional[str] = None
    ) -> Optional[VisaApplication]:
        """Get application by ID or reference."""
        query = select(VisaApplication).options(
            selectinload(VisaApplication.visa_type).selectinload(VisaType.country)
        )
        
        if application_id:
            query = query.where(VisaApplication.id == application_id)
        elif application_ref:
            query = query.where(VisaApplication.application_ref == application_ref)
        else:
            return None
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        visa_type_id: Optional[int] = None,
        country_id: Optional[int] = None,
        user_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """List applications with filters."""
        stmt = select(VisaApplication).options(
            selectinload(VisaApplication.visa_type).selectinload(VisaType.country)
        )
        
        conditions = []
        
        if status:
            conditions.append(VisaApplication.status == status)
        
        if visa_type_id:
            conditions.append(VisaApplication.visa_type_id == visa_type_id)
        
        if country_id:
            stmt = stmt.join(VisaType)
            conditions.append(VisaType.country_id == country_id)
        
        if user_id:
            conditions.append(VisaApplication.user_id == user_id)
        
        if assigned_to_id:
            conditions.append(VisaApplication.assigned_to_id == assigned_to_id)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count
        count_stmt = select(func.count(VisaApplication.id))
        if visa_type_id:
            count_stmt = count_stmt.where(VisaApplication.visa_type_id == visa_type_id)
        if status:
            count_stmt = count_stmt.where(VisaApplication.status == status)
        if user_id:
            count_stmt = count_stmt.where(VisaApplication.user_id == user_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Order and paginate
        stmt = stmt.order_by(VisaApplication.created_at.desc())
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        applications = list(result.scalars().all())
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "applications": applications,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def update_application(
        self,
        application_id: int,
        **updates
    ) -> Optional[VisaApplication]:
        """Update application."""
        application = await self.get_application(application_id)
        if not application:
            return None
        
        for key, value in updates.items():
            if value is not None and hasattr(application, key):
                setattr(application, key, value)
        
        # Auto-update processed_at when status changes to approved/rejected
        if updates.get('status') in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]:
            application.processed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(application)
        return application
    
    async def submit_application(
        self,
        application_id: int
    ) -> Optional[VisaApplication]:
        """Submit a draft application."""
        application = await self.get_application(application_id)
        if not application:
            return None
        
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError("Only draft applications can be submitted")
        
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(application)
        
        logger.info(f"Submitted application {application.application_ref}")
        return application
    
    async def get_application_stats(self) -> Dict[str, int]:
        """Get application statistics by status."""
        stats = {}
        
        for status in ApplicationStatus:
            result = await self.db.execute(
                select(func.count(VisaApplication.id)).where(
                    VisaApplication.status == status
                )
            )
            stats[status.value] = result.scalar() or 0
        
        # Total
        total_result = await self.db.execute(
            select(func.count(VisaApplication.id))
        )
        stats['total'] = total_result.scalar() or 0
        
        return stats
