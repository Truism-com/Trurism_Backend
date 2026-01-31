"""
Markup API Endpoints

REST API endpoints for markup and commission management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_database_session
from app.auth.api import get_current_admin_user, get_current_user
from app.auth.models import User
from app.markup.models import ServiceType
from app.markup.schemas import (
    MarkupRuleCreate, MarkupRuleUpdate, MarkupRuleResponse,
    MarkupRuleListResponse, PriceBreakdown, MarkupCalculationRequest
)
from app.markup.services import MarkupService
from app.tenant.middleware import get_optional_tenant

# Router for markup endpoints
router = APIRouter(prefix="/v1", tags=["Markup & Commission"])


@router.post("/admin/markups", response_model=MarkupRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_markup_rule(
    rule_data: MarkupRuleCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new markup rule.
    
    **Admin Only**: Define markup rules with conditions.
    
    **Example Payloads:**
    
    Fixed markup for international flights:
    ```json
    {
      "name": "International Flight Markup",
      "service_type": "flight",
      "markup_type": "fixed",
      "value": 500,
      "priority": 10,
      "agent_commission_percentage": 20,
      "conditions": {
        "route_type": "international"
      }
    }
    ```
    
    Percentage markup for premium airlines:
    ```json
    {
      "name": "Premium Airline Markup",
      "service_type": "flight",
      "markup_type": "percentage",
      "value": 5,
      "priority": 20,
      "agent_commission_percentage": 30,
      "conditions": {
        "airline": "6E"
      }
    }
    ```
    
    Args:
        rule_data: Markup rule creation data
        current_admin: Current admin user
        db: Database session
        
    Returns:
        MarkupRuleResponse: Created markup rule
    """
    markup_service = MarkupService(db)
    rule = await markup_service.create_markup_rule(rule_data, current_admin.id)
    return MarkupRuleResponse.from_orm(rule)


@router.get("/admin/markups", response_model=MarkupRuleListResponse)
async def list_markup_rules(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    service_type: Optional[ServiceType] = Query(None),
    active_only: bool = Query(True),
    current_admin: User = Depends(get_current_admin_user),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    List all markup rules with pagination.
    
    **Admin Only**: Returns paginated list of markup rules.
    
    Args:
        page: Page number
        size: Items per page
        service_type: Filter by service type
        active_only: Filter only active rules
        current_admin: Current admin user
        request: Request object (for tenant context)
        db: Database session
        
    Returns:
        MarkupRuleListResponse: Paginated list of markup rules
    """
    tenant = get_optional_tenant(request) if request else None
    tenant_id = tenant.id if tenant else None
    
    skip = (page - 1) * size
    
    markup_service = MarkupService(db)
    rules, total = await markup_service.get_all_markup_rules(
        skip=skip,
        limit=size,
        service_type=service_type,
        active_only=active_only,
        tenant_id=tenant_id
    )
    
    return MarkupRuleListResponse(
        rules=[MarkupRuleResponse.from_orm(r) for r in rules],
        total=total,
        page=page,
        size=size
    )


@router.get("/admin/markups/{rule_id}", response_model=MarkupRuleResponse)
async def get_markup_rule(
    rule_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get markup rule by ID.
    
    **Admin Only**: Returns detailed markup rule information.
    
    Args:
        rule_id: Markup rule ID
        current_admin: Current admin user
        db: Database session
        
    Returns:
        MarkupRuleResponse: Markup rule information
    """
    markup_service = MarkupService(db)
    rule = await markup_service.get_markup_rule(rule_id)
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Markup rule not found"
        )
    
    return MarkupRuleResponse.from_orm(rule)


@router.put("/admin/markups/{rule_id}", response_model=MarkupRuleResponse)
async def update_markup_rule(
    rule_id: int,
    update_data: MarkupRuleUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update markup rule.
    
    **Admin Only**: Update existing markup rule.
    
    Args:
        rule_id: Markup rule ID
        update_data: Update data
        current_admin: Current admin user
        db: Database session
        
    Returns:
        MarkupRuleResponse: Updated markup rule
    """
    markup_service = MarkupService(db)
    rule = await markup_service.update_markup_rule(rule_id, update_data)
    return MarkupRuleResponse.from_orm(rule)


@router.delete("/admin/markups/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_markup_rule(
    rule_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete (deactivate) markup rule.
    
    **Admin Only**: Soft delete markup rule.
    
    Args:
        rule_id: Markup rule ID
        current_admin: Current admin user
        db: Database session
    """
    markup_service = MarkupService(db)
    await markup_service.delete_markup_rule(rule_id)


@router.post("/markups/calculate", response_model=PriceBreakdown)
async def calculate_markup(
    calculation_request: MarkupCalculationRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Calculate price with markup for given parameters.
    
    **Use this endpoint** to get price breakdown before booking.
    
    **Example Request:**
    ```json
    {
      "service_type": "flight",
      "base_price": 5000,
      "search_params": {
        "route_type": "international",
        "airline": "6E",
        "travel_class": "economy"
      }
    }
    ```
    
    **Response includes:**
    - base_price: Original supplier price
    - markup_amount: Total markup added
    - admin_margin: Admin's profit
    - agent_commission: Agent's commission (if applicable)
    - taxes: GST/taxes
    - total_price: Final customer price
    - applied_rules: List of rules applied
    
    Args:
        calculation_request: Calculation request data
        current_user: Current authenticated user
        request: Request object (for tenant context)
        db: Database session
        
    Returns:
        PriceBreakdown: Detailed price breakdown
    """
    tenant = get_optional_tenant(request) if request else None
    tenant_id = calculation_request.tenant_id or (tenant.id if tenant else None)
    
    is_agent = current_user.is_agent
    
    markup_service = MarkupService(db)
    breakdown = await markup_service.calculate_price_with_markup(
        service_type=calculation_request.service_type,
        base_price=calculation_request.base_price,
        search_params=calculation_request.search_params,
        tenant_id=tenant_id,
        is_agent_booking=is_agent
    )
    
    return breakdown
