"""
Pricing & Commercials Engine API Endpoints

Admin and public endpoints for pricing management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from decimal import Decimal

from app.core.database import get_db
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.pricing.services import PricingService
from app.pricing.models import ServiceType, MarkupType, UserType, DiscountType,CouponServiceType
from app.pricing.schemas import (
    MarkupRuleCreate, MarkupRuleUpdate, MarkupRuleResponse, MarkupRuleListResponse,
    DiscountRuleCreate, DiscountRuleUpdate, DiscountRuleResponse, DiscountRuleListResponse,
    DiscountValidationResult,
    ConvenienceFeeSlabCreate, ConvenienceFeeSlabUpdate, ConvenienceFeeSlabResponse,
    ConvenienceFeeSlabListResponse,
    PriceCalculationRequest, PriceCalculationResponse,
    MarkupBreakdown, DiscountBreakdown, FeeBreakdown,
    BulkMarkupUpdate, BulkDiscountUpdate, CouponCreate, CouponUpdate, CouponResponse, CouponValidateRequest, CouponValidateResponse,
)

router = APIRouter(prefix="/pricing", tags=["Pricing Engine"])
admin_router = APIRouter(prefix="/admin/pricing", tags=["Admin - Pricing"])


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@router.post("/calculate", response_model=PriceCalculationResponse)
async def calculate_price(
    data: PriceCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Calculate final price with markup, discount, and convenience fee.
    
    This endpoint applies:
    1. Matching markup rules based on service, supplier, route, user type
    2. Discount code if provided
    3. Convenience fee based on payment mode and amount slab
    """
    service = PricingService(db)
    
    user_id = current_user.id if current_user else None
    
    result = await service.calculate_price(
        service_type=data.service_type,
        base_fare=data.base_fare,
        taxes=data.taxes,
        user_type=data.user_type,
        supplier_code=data.supplier_code,
        airline_code=data.airline_code,
        origin=data.origin,
        destination=data.destination,
        cabin_class=data.cabin_class,
        agent_id=data.agent_id,
        hotel_star_rating=data.hotel_star_rating,
        hotel_chain=data.hotel_chain,
        discount_code=data.discount_code,
        payment_mode=data.payment_mode,
        card_type=data.card_type,
        travel_date=data.travel_date,
        user_id=user_id,
        session_id=data.session_id,
        log_calculation=True
    )
    
    return PriceCalculationResponse(
        base_fare=Decimal(str(result['base_fare'])),
        taxes=Decimal(str(result['taxes'])),
        total_markup=Decimal(str(result['total_markup'])),
        fare_after_markup=Decimal(str(result['fare_after_markup'])),
        markup_breakdown=[MarkupBreakdown(**m) for m in result['markup_breakdown']],
        total_discount=Decimal(str(result['total_discount'])),
        fare_after_discount=Decimal(str(result['fare_after_discount'])),
        discount_breakdown=[DiscountBreakdown(**d) for d in result['discount_breakdown']],
        convenience_fee=Decimal(str(result['convenience_fee'])),
        convenience_fee_gst=Decimal(str(result['convenience_fee_gst'])),
        total_convenience_fee=Decimal(str(result['total_convenience_fee'])),
        fee_breakdown=FeeBreakdown(**result['fee_breakdown']) if result['fee_breakdown'] else None,
        subtotal=Decimal(str(result['subtotal'])),
        grand_total=Decimal(str(result['grand_total'])),
        you_save=Decimal(str(result['you_save'])),
        effective_margin=Decimal(str(result['effective_margin'])),
        calculated_at=result['calculated_at']
    )


@router.post("/validate-discount", response_model=DiscountValidationResult)
async def validate_discount_code(
    code: str = Query(..., description="Discount code to validate"),
    service_type: ServiceType = Query(...),
    amount: Decimal = Query(..., ge=0),
    user_type: UserType = Query(UserType.B2C),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Validate a discount code and get discount amount."""
    service = PricingService(db)
    
    is_valid, discount_amount, error, rule = await service.validate_discount_code(
        code=code,
        service_type=service_type,
        amount=amount,
        user_type=user_type,
        user_id=current_user.id if current_user else None
    )
    
    return DiscountValidationResult(
        is_valid=is_valid,
        discount_amount=discount_amount or Decimal(0),
        error_message=error,
        discount_rule=rule
    )


@router.get("/convenience-fees", response_model=ConvenienceFeeSlabListResponse)
async def get_convenience_fees(
    service_type: Optional[ServiceType] = Query(None),
    payment_mode: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get applicable convenience fee slabs."""
    service = PricingService(db)
    slabs, total = await service.get_fee_slabs(
        service_type=service_type,
        payment_mode=payment_mode,
        is_active=True
    )
    
    return ConvenienceFeeSlabListResponse(items=slabs, total=total)


# =============================================================================
# ADMIN - MARKUP RULES
# =============================================================================

@admin_router.get("/markup-rules", response_model=MarkupRuleListResponse)
async def list_markup_rules(
    service_type: Optional[ServiceType] = Query(None),
    user_type: Optional[UserType] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all markup rules with filters."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rules, total = await service.get_markup_rules(
        service_type=service_type,
        user_type=user_type,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    
    return MarkupRuleListResponse(items=rules, total=total)


@admin_router.post("/markup-rules", response_model=MarkupRuleResponse)
async def create_markup_rule(
    data: MarkupRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new markup rule."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rule = await service.create_markup_rule(
        data=data.model_dump(exclude_unset=True),
        created_by=current_user.id
    )
    
    return rule


@admin_router.get("/markup-rules/{rule_id}", response_model=MarkupRuleResponse)
async def get_markup_rule(
    rule_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get markup rule by ID."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rule = await service.get_markup_rule(rule_id)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Markup rule not found")
    
    return rule


@admin_router.put("/markup-rules/{rule_id}", response_model=MarkupRuleResponse)
async def update_markup_rule(
    rule_id: int = Path(...),
    data: MarkupRuleUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update markup rule."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rule = await service.update_markup_rule(
        rule_id=rule_id,
        data=data.model_dump(exclude_unset=True, exclude_none=True)
    )
    
    if not rule:
        raise HTTPException(status_code=404, detail="Markup rule not found")
    
    return rule


@admin_router.delete("/markup-rules/{rule_id}")
async def delete_markup_rule(
    rule_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete markup rule."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    success = await service.delete_markup_rule(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Markup rule not found")
    
    return {"message": "Markup rule deleted"}


@admin_router.post("/markup-rules/bulk-update")
async def bulk_update_markup_rules(
    data: BulkMarkupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update multiple markup rules."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    updated = 0
    
    for rule_id in data.rule_ids:
        result = await service.update_markup_rule(
            rule_id=rule_id,
            data=data.updates.model_dump(exclude_unset=True, exclude_none=True)
        )
        if result:
            updated += 1
    
    return {"message": f"Updated {updated} markup rules"}


# =============================================================================
# ADMIN - DISCOUNT RULES
# =============================================================================

@admin_router.get("/discount-rules", response_model=DiscountRuleListResponse)
async def list_discount_rules(
    service_type: Optional[ServiceType] = Query(None),
    user_type: Optional[UserType] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all discount rules with filters."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rules, total = await service.get_discount_rules(
        service_type=service_type,
        user_type=user_type,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    
    return DiscountRuleListResponse(items=rules, total=total)


@admin_router.post("/discount-rules", response_model=DiscountRuleResponse)
async def create_discount_rule(
    data: DiscountRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new discount rule."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rule = await service.create_discount_rule(
        data=data.model_dump(exclude_unset=True),
        created_by=current_user.id
    )
    
    return rule


@admin_router.get("/discount-rules/{rule_id}", response_model=DiscountRuleResponse)
async def get_discount_rule(
    rule_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get discount rule by ID."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rule = await service.get_discount_rule(rule_id)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Discount rule not found")
    
    return rule


@admin_router.put("/discount-rules/{rule_id}", response_model=DiscountRuleResponse)
async def update_discount_rule(
    rule_id: int = Path(...),
    data: DiscountRuleUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update discount rule."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    rule = await service.update_discount_rule(
        rule_id=rule_id,
        data=data.model_dump(exclude_unset=True, exclude_none=True)
    )
    
    if not rule:
        raise HTTPException(status_code=404, detail="Discount rule not found")
    
    return rule


@admin_router.delete("/discount-rules/{rule_id}")
async def delete_discount_rule(
    rule_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete discount rule."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    success = await service.delete_discount_rule(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Discount rule not found")
    
    return {"message": "Discount rule deleted"}


# =============================================================================
# ADMIN - CONVENIENCE FEE SLABS
# =============================================================================

@admin_router.get("/fee-slabs", response_model=ConvenienceFeeSlabListResponse)
async def list_fee_slabs(
    service_type: Optional[ServiceType] = Query(None),
    payment_mode: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all convenience fee slabs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    slabs, total = await service.get_fee_slabs(
        service_type=service_type,
        payment_mode=payment_mode,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    
    return ConvenienceFeeSlabListResponse(items=slabs, total=total)


@admin_router.post("/fee-slabs", response_model=ConvenienceFeeSlabResponse)
async def create_fee_slab(
    data: ConvenienceFeeSlabCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new convenience fee slab."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    slab = await service.create_fee_slab(
        data=data.model_dump(exclude_unset=True),
        created_by=current_user.id
    )
    
    return slab


@admin_router.get("/fee-slabs/{slab_id}", response_model=ConvenienceFeeSlabResponse)
async def get_fee_slab(
    slab_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get fee slab by ID."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    slab = await service.get_fee_slab(slab_id)
    
    if not slab:
        raise HTTPException(status_code=404, detail="Fee slab not found")
    
    return slab


@admin_router.put("/fee-slabs/{slab_id}", response_model=ConvenienceFeeSlabResponse)
async def update_fee_slab(
    slab_id: int = Path(...),
    data: ConvenienceFeeSlabUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update fee slab."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    slab = await service.update_fee_slab(
        slab_id=slab_id,
        data=data.model_dump(exclude_unset=True, exclude_none=True)
    )
    
    if not slab:
        raise HTTPException(status_code=404, detail="Fee slab not found")
    
    return slab


@admin_router.delete("/fee-slabs/{slab_id}")
async def delete_fee_slab(
    slab_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete fee slab."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    success = await service.delete_fee_slab(slab_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Fee slab not found")
    
    return {"message": "Fee slab deleted"}


# =============================================================================
# ADMIN - SEEDING
# =============================================================================

@admin_router.post("/seed-defaults")
async def seed_default_pricing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Seed default markup rules and fee slabs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = PricingService(db)
    
    markup_rules = await service.seed_default_markup_rules()
    fee_slabs = await service.seed_default_fee_slabs()
    
    return {
        "message": "Default pricing seeded",
        "markup_rules_created": len(markup_rules),
        "fee_slabs_created": len(fee_slabs)
    }

# =============================================================================
# COUPON ENDPOINTS
# =============================================================================

@router.post("/coupon/validate",response_description=CouponValidateResponse)
async def validate_coupon(
    data: CouponValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """validate a coupon code and return the discoun amount"""
    service = PricingService (db)
    is_valid, discount_amount, error, coupon = await service.validate_coupon(
        code=data.code,
        order_amount=data.order_amount,
        service_type=data.service_type,
    )
    if not is_valid:
        return CouponValidateResponse(is_valid=False,error=error)
    return CouponValidateResponse(
        is_valid=True,
        discount_amount=discount_amount,
        final_amount=data.order_amount - discount_amount,
        coupon=CouponResponse.model_validate(coupon),
    )
    
@admin_router.post("/coupons", response_model=CouponValidateResponse)
async def create_coupon(
    data: CouponCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Create a new coupon."""
    service = PricingService(db)
    coupon = await service.create_coupon(
        data=data.model_dump(),
        created_by=current_user.id,
    )
    return CouponResponse.model_validate(coupon)

@admin_router.get("/coupons", response_model=List[CouponResponse])
async def list_coupons(
    skip: int =  Query (0, ge=0),
    limit: int = Query (50 , ge=1, le =200),
    current_user: User= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin: list all coupons"""
    service = PricingService(db)
    coupons = await service.get_coupons(skip=skip,limit=limit)
    return [CouponResponse.model_validate(c) for c in coupons]

@admin_router.put("/coupons/{coupon_id}",response_model=CouponValidateResponse)
async def update_coupon(
    data: CouponUpdate,  
    coupon_id: int = Path(...,ge=1),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin: Update an existing coupon"""
    service = PricingService(db)
    coupon =await service.update_coupon(
        coupon_id=coupon_id,
        data=data.model_dump(exclude_none=True)
    )
    if not coupon:
        raise HTTPException(status_code=404, detail="coupon not found")
    return CouponResponse.model_validate(coupon)

@admin_router.delete("/coupons/{coupon_id}",status_code=204)
async def delete_coupon(
    coupon_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin: delete a coupon"""
    service = PricingService(db)
    deleted = await service.delete_coupon(coupon_id)
    if not deleted:
        raise HTTPException(status_code=404 , detail="Coupon not found")
