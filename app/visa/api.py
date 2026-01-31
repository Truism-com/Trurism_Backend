"""
Visa API

REST endpoints for visa operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.visa.models import ApplicationStatus
from app.visa.services import VisaService
from app.visa.schemas import (
    # Country schemas
    VisaCountryCreate, VisaCountryUpdate, VisaCountryResponse,
    VisaCountryWithTypes, VisaCountryListResponse,
    # Type schemas
    VisaTypeCreate, VisaTypeUpdate, VisaTypeResponse, VisaTypeDetail,
    # Requirement schemas
    VisaRequirementCreate, VisaRequirementUpdate, VisaRequirementResponse,
    # Application schemas
    VisaApplicationCreate, VisaApplicationUpdate,
    VisaApplicationResponse, VisaApplicationDetail, VisaApplicationListResponse
)

router = APIRouter(prefix="/visa", tags=["Visa"])


# =============================================================================
# Country Endpoints (Public + Admin)
# =============================================================================

@router.get("/countries", response_model=List[VisaCountryResponse])
async def list_countries(
    active_only: bool = True,
    popular_only: bool = False,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all visa countries.
    
    Public endpoint.
    """
    service = VisaService(db)
    countries = await service.get_countries(
        active_only=active_only,
        popular_only=popular_only
    )
    return countries


@router.get("/countries/search", response_model=VisaCountryListResponse)
async def search_countries(
    query: Optional[str] = None,
    is_popular: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search visa countries.
    
    Public endpoint.
    """
    service = VisaService(db)
    result = await service.search_countries(
        query=query,
        is_popular=is_popular,
        page=page,
        page_size=page_size
    )
    return result


@router.post("/countries", response_model=VisaCountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    data: VisaCountryCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new visa country.
    
    Requires admin authentication.
    """
    service = VisaService(db)
    country = await service.create_country(**data.model_dump())
    return country


@router.get("/countries/{country_id}", response_model=VisaCountryWithTypes)
async def get_country(
    country_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get country with visa types."""
    service = VisaService(db)
    country = await service.get_country(country_id, include_types=True)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.get("/countries/slug/{slug}", response_model=VisaCountryWithTypes)
async def get_country_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_database_session)
):
    """Get country by slug with visa types."""
    service = VisaService(db)
    country = await service.get_country(slug=slug, include_types=True)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.put("/countries/{country_id}", response_model=VisaCountryResponse)
async def update_country(
    country_id: int,
    data: VisaCountryUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a country."""
    service = VisaService(db)
    country = await service.update_country(country_id, **data.model_dump(exclude_unset=True))
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


# =============================================================================
# Visa Type Endpoints (Public + Admin)
# =============================================================================

@router.get("/types", response_model=List[VisaTypeResponse])
async def list_visa_types(
    country_id: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get all visa types, optionally filtered by country.
    
    Public endpoint.
    """
    service = VisaService(db)
    visa_types = await service.get_visa_types(
        country_id=country_id,
        active_only=active_only
    )
    return visa_types


@router.post("/types", response_model=VisaTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_visa_type(
    data: VisaTypeCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new visa type."""
    service = VisaService(db)
    
    # Verify country exists
    country = await service.get_country(data.country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    visa_type = await service.create_visa_type(**data.model_dump())
    return visa_type


@router.get("/types/{visa_type_id}", response_model=VisaTypeDetail)
async def get_visa_type(
    visa_type_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get visa type details with requirements."""
    service = VisaService(db)
    visa_type = await service.get_visa_type(visa_type_id, include_requirements=True)
    if not visa_type:
        raise HTTPException(status_code=404, detail="Visa type not found")
    return visa_type


@router.put("/types/{visa_type_id}", response_model=VisaTypeResponse)
async def update_visa_type(
    visa_type_id: int,
    data: VisaTypeUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a visa type."""
    service = VisaService(db)
    visa_type = await service.update_visa_type(visa_type_id, **data.model_dump(exclude_unset=True))
    if not visa_type:
        raise HTTPException(status_code=404, detail="Visa type not found")
    return visa_type


# =============================================================================
# Requirement Endpoints (Admin)
# =============================================================================

@router.post("/types/{visa_type_id}/requirements", response_model=VisaRequirementResponse, status_code=status.HTTP_201_CREATED)
async def add_requirement(
    visa_type_id: int,
    data: VisaRequirementCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Add requirement to a visa type."""
    service = VisaService(db)
    
    # Verify visa type exists
    visa_type = await service.get_visa_type(visa_type_id, include_requirements=False)
    if not visa_type:
        raise HTTPException(status_code=404, detail="Visa type not found")
    
    requirement = await service.add_requirement(
        visa_type_id=visa_type_id,
        category=data.category,
        title=data.title,
        description=data.description,
        is_mandatory=data.is_mandatory,
        applies_to=data.applies_to,
        display_order=data.display_order
    )
    return requirement


@router.put("/requirements/{requirement_id}", response_model=VisaRequirementResponse)
async def update_requirement(
    requirement_id: int,
    data: VisaRequirementUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a requirement."""
    service = VisaService(db)
    requirement = await service.update_requirement(requirement_id, **data.model_dump(exclude_unset=True))
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a requirement."""
    service = VisaService(db)
    deleted = await service.delete_requirement(requirement_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return None


# =============================================================================
# Application Endpoints (Public + Admin)
# =============================================================================

@router.post("/applications", response_model=VisaApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: VisaApplicationCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(lambda: None)  # Optional auth
):
    """
    Create a new visa application.
    
    Can be created without authentication (guest) or by authenticated user.
    """
    service = VisaService(db)
    
    user_id = int(current_user.id) if current_user else None
    
    try:
        application = await service.create_application(
            user_id=user_id,
            **data.model_dump()
        )
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/applications", response_model=VisaApplicationListResponse)
async def list_applications(
    status: Optional[ApplicationStatus] = None,
    visa_type_id: Optional[int] = None,
    country_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all applications.
    
    Requires admin authentication.
    """
    service = VisaService(db)
    result = await service.list_applications(
        status=status,
        visa_type_id=visa_type_id,
        country_id=country_id,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/applications/stats")
async def get_application_stats(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get application statistics by status.
    
    Requires admin authentication.
    """
    service = VisaService(db)
    stats = await service.get_application_stats()
    return stats


@router.get("/applications/{application_id}", response_model=VisaApplicationDetail)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Get application details."""
    service = VisaService(db)
    application = await service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("/applications/ref/{application_ref}", response_model=VisaApplicationResponse)
async def get_application_by_ref(
    application_ref: str,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get application by reference number.
    
    Public endpoint for applicant to check status.
    """
    service = VisaService(db)
    application = await service.get_application(application_ref=application_ref)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.put("/applications/{application_id}", response_model=VisaApplicationResponse)
async def update_application(
    application_id: int,
    data: VisaApplicationUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_admin_user)
):
    """Update application (admin)."""
    service = VisaService(db)
    application = await service.update_application(
        application_id,
        **data.model_dump(exclude_unset=True)
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("/applications/{application_id}/submit", response_model=VisaApplicationResponse)
async def submit_application(
    application_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """Submit a draft application."""
    service = VisaService(db)
    
    application = await service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check ownership
    if application.user_id and application.user_id != int(current_user.id):
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        application = await service.submit_application(application_id)
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# User Applications
# =============================================================================

@router.get("/my/applications", response_model=VisaApplicationListResponse)
async def get_my_applications(
    status: Optional[ApplicationStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's visa applications.
    """
    service = VisaService(db)
    result = await service.list_applications(
        user_id=int(current_user.id),
        status=status,
        page=page,
        page_size=page_size
    )
    return result
