"""
Pricing & Commercials Engine Service Layer

Business logic for markup, discount, and fee calculations.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

from app.pricing.models import (
    PricingMarkupRule as MarkupRule, DiscountRule, ConvenienceFeeSlab, PriceAuditLog,
    ServiceType, MarkupType, UserType, DiscountType
)

logger = logging.getLogger(__name__)


class PricingService:
    """Service for pricing calculations."""
    
    def __init__(self, db: AsyncSession, tenant_id: int = 1):
        self.db = db
        self.tenant_id = tenant_id
    
    # =========================================================================
    # MARKUP RULES CRUD
    # =========================================================================
    
    async def create_markup_rule(
        self,
        data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> MarkupRule:
        """Create a new markup rule."""
        rule = MarkupRule(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
    
    async def get_markup_rule(self, rule_id: int) -> Optional[MarkupRule]:
        """Get markup rule by ID."""
        stmt = select(MarkupRule).where(
            MarkupRule.id == rule_id,
            MarkupRule.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_markup_rules(
        self,
        service_type: Optional[ServiceType] = None,
        user_type: Optional[UserType] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[MarkupRule], int]:
        """Get markup rules with filters."""
        stmt = select(MarkupRule).where(MarkupRule.tenant_id == self.tenant_id)
        
        if service_type:
            stmt = stmt.where(or_(
                MarkupRule.service_type == service_type,
                MarkupRule.service_type == ServiceType.ALL
            ))
        if user_type:
            stmt = stmt.where(or_(
                MarkupRule.user_type == user_type,
                MarkupRule.user_type == UserType.ALL
            ))
        if is_active is not None:
            stmt = stmt.where(MarkupRule.is_active == is_active)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(desc(MarkupRule.priority), MarkupRule.id)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        rules = list(result.scalars().all())
        
        return rules, total
    
    async def update_markup_rule(
        self,
        rule_id: int,
        data: Dict[str, Any]
    ) -> Optional[MarkupRule]:
        """Update markup rule."""
        rule = await self.get_markup_rule(rule_id)
        if not rule:
            return None
        
        for key, value in data.items():
            if value is not None:
                setattr(rule, key, value)
        
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
    
    async def delete_markup_rule(self, rule_id: int) -> bool:
        """Delete markup rule."""
        rule = await self.get_markup_rule(rule_id)
        if not rule:
            return False
        
        await self.db.delete(rule)
        await self.db.commit()
        return True
    
    # =========================================================================
    # DISCOUNT RULES CRUD
    # =========================================================================
    
    async def create_discount_rule(
        self,
        data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> DiscountRule:
        """Create a new discount rule."""
        rule = DiscountRule(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
    
    async def get_discount_rule(self, rule_id: int) -> Optional[DiscountRule]:
        """Get discount rule by ID."""
        stmt = select(DiscountRule).where(
            DiscountRule.id == rule_id,
            DiscountRule.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_discount_by_code(self, code: str) -> Optional[DiscountRule]:
        """Get discount rule by code."""
        stmt = select(DiscountRule).where(
            DiscountRule.code == code,
            DiscountRule.tenant_id == self.tenant_id,
            DiscountRule.is_active == True
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_discount_rules(
        self,
        service_type: Optional[ServiceType] = None,
        user_type: Optional[UserType] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DiscountRule], int]:
        """Get discount rules with filters."""
        stmt = select(DiscountRule).where(DiscountRule.tenant_id == self.tenant_id)
        
        if service_type:
            stmt = stmt.where(or_(
                DiscountRule.service_type == service_type,
                DiscountRule.service_type == ServiceType.ALL
            ))
        if user_type:
            stmt = stmt.where(or_(
                DiscountRule.user_type == user_type,
                DiscountRule.user_type == UserType.ALL
            ))
        if is_active is not None:
            stmt = stmt.where(DiscountRule.is_active == is_active)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(desc(DiscountRule.priority), DiscountRule.id)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        rules = list(result.scalars().all())
        
        return rules, total
    
    async def update_discount_rule(
        self,
        rule_id: int,
        data: Dict[str, Any]
    ) -> Optional[DiscountRule]:
        """Update discount rule."""
        rule = await self.get_discount_rule(rule_id)
        if not rule:
            return None
        
        for key, value in data.items():
            if value is not None:
                setattr(rule, key, value)
        
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
    
    async def delete_discount_rule(self, rule_id: int) -> bool:
        """Delete discount rule."""
        rule = await self.get_discount_rule(rule_id)
        if not rule:
            return False
        
        await self.db.delete(rule)
        await self.db.commit()
        return True
    
    async def validate_discount_code(
        self,
        code: str,
        service_type: ServiceType,
        amount: Decimal,
        user_type: UserType,
        user_id: Optional[int] = None,
        travel_date: Optional[date] = None
    ) -> Tuple[bool, Optional[Decimal], Optional[str], Optional[DiscountRule]]:
        """
        Validate discount code and return discount amount.
        
        Returns: (is_valid, discount_amount, error_message, rule)
        """
        rule = await self.get_discount_by_code(code)
        if not rule:
            return False, None, "Invalid discount code", None
        
        today = date.today()
        
        # Check validity dates
        if rule.valid_from > today or rule.valid_to < today:
            return False, None, "Discount code has expired", None
        
        # Check service type
        if rule.service_type != ServiceType.ALL and rule.service_type != service_type:
            return False, None, "Discount not applicable for this service", None
        
        # Check user type
        if rule.user_type != UserType.ALL and rule.user_type != user_type:
            return False, None, "Discount not applicable for your account type", None
        
        # Check minimum booking amount
        if rule.min_booking_amount and amount < rule.min_booking_amount:
            return False, None, f"Minimum booking amount is {rule.min_booking_amount}", None
        
        # Check usage limits
        if rule.usage_limit_total and rule.usage_count >= rule.usage_limit_total:
            return False, None, "Discount usage limit reached", None
        
        # Check travel date restrictions
        if travel_date:
            if rule.travel_from and travel_date < rule.travel_from:
                return False, None, "Discount not valid for selected travel date", None
            if rule.travel_to and travel_date > rule.travel_to:
                return False, None, "Discount not valid for selected travel date", None
        
        # Calculate discount
        if rule.discount_type == DiscountType.FIXED:
            discount_amount = rule.discount_value
        else:
            discount_amount = (amount * rule.discount_value / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        
        # Apply cap
        if rule.max_discount and discount_amount > rule.max_discount:
            discount_amount = rule.max_discount
        
        return True, discount_amount, None, rule
    
    async def increment_discount_usage(self, rule_id: int) -> None:
        """Increment discount usage count."""
        rule = await self.get_discount_rule(rule_id)
        if rule:
            rule.usage_count += 1
            await self.db.commit()
    
    # =========================================================================
    # CONVENIENCE FEE SLABS CRUD
    # =========================================================================
    
    async def create_fee_slab(
        self,
        data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> ConvenienceFeeSlab:
        """Create a new fee slab."""
        slab = ConvenienceFeeSlab(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(slab)
        await self.db.commit()
        await self.db.refresh(slab)
        return slab
    
    async def get_fee_slab(self, slab_id: int) -> Optional[ConvenienceFeeSlab]:
        """Get fee slab by ID."""
        stmt = select(ConvenienceFeeSlab).where(
            ConvenienceFeeSlab.id == slab_id,
            ConvenienceFeeSlab.tenant_id == self.tenant_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_fee_slabs(
        self,
        service_type: Optional[ServiceType] = None,
        payment_mode: Optional[str] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ConvenienceFeeSlab], int]:
        """Get fee slabs with filters."""
        stmt = select(ConvenienceFeeSlab).where(
            ConvenienceFeeSlab.tenant_id == self.tenant_id
        )
        
        if service_type:
            stmt = stmt.where(or_(
                ConvenienceFeeSlab.service_type == service_type,
                ConvenienceFeeSlab.service_type == ServiceType.ALL
            ))
        if payment_mode:
            stmt = stmt.where(ConvenienceFeeSlab.payment_mode == payment_mode)
        if is_active is not None:
            stmt = stmt.where(ConvenienceFeeSlab.is_active == is_active)
        
        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0
        
        # Paginate
        stmt = stmt.order_by(desc(ConvenienceFeeSlab.priority), ConvenienceFeeSlab.min_amount)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(stmt)
        slabs = list(result.scalars().all())
        
        return slabs, total
    
    async def update_fee_slab(
        self,
        slab_id: int,
        data: Dict[str, Any]
    ) -> Optional[ConvenienceFeeSlab]:
        """Update fee slab."""
        slab = await self.get_fee_slab(slab_id)
        if not slab:
            return None
        
        for key, value in data.items():
            if value is not None:
                setattr(slab, key, value)
        
        await self.db.commit()
        await self.db.refresh(slab)
        return slab
    
    async def delete_fee_slab(self, slab_id: int) -> bool:
        """Delete fee slab."""
        slab = await self.get_fee_slab(slab_id)
        if not slab:
            return False
        
        await self.db.delete(slab)
        await self.db.commit()
        return True
    
    # =========================================================================
    # PRICE CALCULATION ENGINE
    # =========================================================================
    
    async def find_matching_markup_rules(
        self,
        service_type: ServiceType,
        user_type: UserType,
        base_fare: Decimal,
        supplier_code: Optional[str] = None,
        airline_code: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        cabin_class: Optional[str] = None,
        agent_id: Optional[int] = None,
        hotel_star_rating: Optional[int] = None,
        hotel_chain: Optional[str] = None
    ) -> List[MarkupRule]:
        """Find all matching markup rules ordered by priority."""
        today = date.today()
        
        stmt = select(MarkupRule).where(
            MarkupRule.tenant_id == self.tenant_id,
            MarkupRule.is_active == True,
            or_(
                MarkupRule.service_type == service_type,
                MarkupRule.service_type == ServiceType.ALL
            ),
            or_(
                MarkupRule.user_type == user_type,
                MarkupRule.user_type == UserType.ALL
            ),
            or_(MarkupRule.valid_from == None, MarkupRule.valid_from <= today),
            or_(MarkupRule.valid_to == None, MarkupRule.valid_to >= today)
        )
        
        # Fare range check
        stmt = stmt.where(
            or_(MarkupRule.min_fare == None, MarkupRule.min_fare <= base_fare),
            or_(MarkupRule.max_fare == None, MarkupRule.max_fare >= base_fare)
        )
        
        # Optional filters - only apply if rule has value
        if supplier_code:
            stmt = stmt.where(or_(
                MarkupRule.supplier_code == None,
                MarkupRule.supplier_code == supplier_code
            ))
        if airline_code:
            stmt = stmt.where(or_(
                MarkupRule.airline_code == None,
                MarkupRule.airline_code == airline_code
            ))
        if origin:
            stmt = stmt.where(or_(
                MarkupRule.origin_city == None,
                MarkupRule.origin_city == origin
            ))
        if destination:
            stmt = stmt.where(or_(
                MarkupRule.destination_city == None,
                MarkupRule.destination_city == destination
            ))
        if cabin_class:
            stmt = stmt.where(or_(
                MarkupRule.cabin_class == None,
                MarkupRule.cabin_class == cabin_class
            ))
        if agent_id:
            stmt = stmt.where(or_(
                MarkupRule.agent_id == None,
                MarkupRule.agent_id == agent_id
            ))
        if hotel_star_rating:
            stmt = stmt.where(or_(
                MarkupRule.hotel_star_rating == None,
                MarkupRule.hotel_star_rating == hotel_star_rating
            ))
        if hotel_chain:
            stmt = stmt.where(or_(
                MarkupRule.hotel_chain == None,
                MarkupRule.hotel_chain == hotel_chain
            ))
        
        stmt = stmt.order_by(desc(MarkupRule.priority))
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def find_matching_fee_slab(
        self,
        service_type: ServiceType,
        amount: Decimal,
        payment_mode: str,
        user_type: UserType,
        card_type: Optional[str] = None
    ) -> Optional[ConvenienceFeeSlab]:
        """Find matching convenience fee slab."""
        today = date.today()
        
        stmt = select(ConvenienceFeeSlab).where(
            ConvenienceFeeSlab.tenant_id == self.tenant_id,
            ConvenienceFeeSlab.is_active == True,
            or_(
                ConvenienceFeeSlab.service_type == service_type,
                ConvenienceFeeSlab.service_type == ServiceType.ALL
            ),
            or_(
                ConvenienceFeeSlab.user_type == user_type,
                ConvenienceFeeSlab.user_type == UserType.ALL
            ),
            ConvenienceFeeSlab.payment_mode == payment_mode,
            ConvenienceFeeSlab.min_amount <= amount,
            or_(
                ConvenienceFeeSlab.max_amount == None,
                ConvenienceFeeSlab.max_amount >= amount
            ),
            or_(ConvenienceFeeSlab.valid_from == None, ConvenienceFeeSlab.valid_from <= today),
            or_(ConvenienceFeeSlab.valid_to == None, ConvenienceFeeSlab.valid_to >= today)
        )
        
        if card_type:
            stmt = stmt.where(or_(
                ConvenienceFeeSlab.card_type == None,
                ConvenienceFeeSlab.card_type == card_type
            ))
        
        stmt = stmt.order_by(desc(ConvenienceFeeSlab.priority)).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def calculate_price(
        self,
        service_type: ServiceType,
        base_fare: Decimal,
        taxes: Decimal = Decimal(0),
        user_type: UserType = UserType.B2C,
        supplier_code: Optional[str] = None,
        airline_code: Optional[str] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        cabin_class: Optional[str] = None,
        agent_id: Optional[int] = None,
        hotel_star_rating: Optional[int] = None,
        hotel_chain: Optional[str] = None,
        discount_code: Optional[str] = None,
        payment_mode: Optional[str] = None,
        card_type: Optional[str] = None,
        travel_date: Optional[date] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        log_calculation: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate final price with markup, discount, and convenience fee.
        
        Returns complete price breakdown.
        """
        result = {
            'base_fare': base_fare,
            'taxes': taxes,
            'total_markup': Decimal(0),
            'fare_after_markup': base_fare + taxes,
            'markup_breakdown': [],
            'total_discount': Decimal(0),
            'fare_after_discount': base_fare + taxes,
            'discount_breakdown': [],
            'convenience_fee': Decimal(0),
            'convenience_fee_gst': Decimal(0),
            'total_convenience_fee': Decimal(0),
            'fee_breakdown': None,
            'subtotal': base_fare + taxes,
            'grand_total': base_fare + taxes,
            'you_save': Decimal(0),
            'effective_margin': Decimal(0),
            'calculated_at': datetime.utcnow()
        }
        
        # =====================================================================
        # STEP 1: CALCULATE MARKUP
        # =====================================================================
        
        markup_rules = await self.find_matching_markup_rules(
            service_type=service_type,
            user_type=user_type,
            base_fare=base_fare,
            supplier_code=supplier_code,
            airline_code=airline_code,
            origin=origin,
            destination=destination,
            cabin_class=cabin_class,
            agent_id=agent_id,
            hotel_star_rating=hotel_star_rating,
            hotel_chain=hotel_chain
        )
        
        applied_non_stackable = False
        total_markup = Decimal(0)
        
        for rule in markup_rules:
            # Skip stackable rules if non-stackable already applied
            if applied_non_stackable and not rule.is_stackable:
                continue
            
            # Calculate markup base
            markup_base = Decimal(0)
            if rule.apply_on_net_fare:
                markup_base += base_fare
            if rule.apply_on_taxes:
                markup_base += taxes
            
            # Calculate markup amount
            if rule.markup_type == MarkupType.FIXED:
                markup_amount = rule.markup_value
            else:
                markup_amount = (markup_base * rule.markup_value / 100).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
            
            # Apply min/max constraints
            if rule.min_markup and markup_amount < rule.min_markup:
                markup_amount = rule.min_markup
            if rule.max_markup and markup_amount > rule.max_markup:
                markup_amount = rule.max_markup
            
            total_markup += markup_amount
            
            result['markup_breakdown'].append({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'markup_type': rule.markup_type.value,
                'markup_value': float(rule.markup_value),
                'calculated_markup': float(markup_amount)
            })
            
            if not rule.is_stackable:
                applied_non_stackable = True
                break  # Only one non-stackable rule
        
        result['total_markup'] = total_markup
        result['fare_after_markup'] = base_fare + taxes + total_markup
        
        # =====================================================================
        # STEP 2: APPLY DISCOUNT
        # =====================================================================
        
        if discount_code:
            is_valid, discount_amount, error, discount_rule = await self.validate_discount_code(
                code=discount_code,
                service_type=service_type,
                amount=result['fare_after_markup'],
                user_type=user_type,
                user_id=user_id,
                travel_date=travel_date
            )
            
            if is_valid and discount_amount:
                result['total_discount'] = discount_amount
                result['discount_breakdown'].append({
                    'rule_id': discount_rule.id,
                    'rule_name': discount_rule.name,
                    'code': discount_rule.code,
                    'discount_type': discount_rule.discount_type.value,
                    'discount_value': float(discount_rule.discount_value),
                    'calculated_discount': float(discount_amount)
                })
        
        result['fare_after_discount'] = result['fare_after_markup'] - result['total_discount']
        result['subtotal'] = result['fare_after_discount']
        
        # =====================================================================
        # STEP 3: CALCULATE CONVENIENCE FEE
        # =====================================================================
        
        if payment_mode:
            fee_slab = await self.find_matching_fee_slab(
                service_type=service_type,
                amount=result['subtotal'],
                payment_mode=payment_mode,
                user_type=user_type,
                card_type=card_type
            )
            
            if fee_slab:
                if fee_slab.fee_type == 'fixed':
                    fee_amount = fee_slab.fee_value
                else:
                    fee_amount = (result['subtotal'] * fee_slab.fee_value / 100).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                
                # Apply min/max
                if fee_slab.min_fee and fee_amount < fee_slab.min_fee:
                    fee_amount = fee_slab.min_fee
                if fee_slab.max_fee and fee_amount > fee_slab.max_fee:
                    fee_amount = fee_slab.max_fee
                
                # Calculate GST
                gst_amount = Decimal(0)
                if fee_slab.apply_gst:
                    gst_amount = (fee_amount * fee_slab.gst_rate / 100).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )
                
                total_fee = fee_amount + gst_amount
                
                result['convenience_fee'] = fee_amount
                result['convenience_fee_gst'] = gst_amount
                result['total_convenience_fee'] = total_fee
                result['fee_breakdown'] = {
                    'slab_id': fee_slab.id,
                    'slab_name': fee_slab.name,
                    'fee_type': fee_slab.fee_type,
                    'fee_value': float(fee_slab.fee_value),
                    'calculated_fee': float(fee_amount),
                    'gst_amount': float(gst_amount),
                    'total_fee': float(total_fee)
                }
        
        # =====================================================================
        # STEP 4: CALCULATE FINAL TOTALS
        # =====================================================================
        
        result['grand_total'] = result['subtotal'] + result['total_convenience_fee']
        result['you_save'] = result['total_discount']
        result['effective_margin'] = result['total_markup'] - result['total_discount']
        
        # =====================================================================
        # STEP 5: LOG CALCULATION (optional)
        # =====================================================================
        
        if log_calculation:
            audit_log = PriceAuditLog(
                tenant_id=self.tenant_id,
                session_id=session_id,
                user_id=user_id,
                user_type=user_type.value if user_type else None,
                service_type=service_type.value,
                supplier_code=supplier_code,
                base_fare=base_fare,
                taxes=taxes,
                markup_rules_applied=result['markup_breakdown'],
                discount_rules_applied=result['discount_breakdown'],
                fee_slabs_applied=result['fee_breakdown'],
                total_markup=result['total_markup'],
                total_discount=result['total_discount'],
                convenience_fee=result['total_convenience_fee'],
                final_amount=result['grand_total'],
                calculation_metadata={
                    'airline_code': airline_code,
                    'origin': origin,
                    'destination': destination,
                    'cabin_class': cabin_class,
                    'payment_mode': payment_mode,
                    'card_type': card_type
                }
            )
            self.db.add(audit_log)
            await self.db.commit()
        
        # Convert decimals to float for JSON serialization
        for key in ['base_fare', 'taxes', 'total_markup', 'fare_after_markup',
                    'total_discount', 'fare_after_discount', 'convenience_fee',
                    'convenience_fee_gst', 'total_convenience_fee', 'subtotal',
                    'grand_total', 'you_save', 'effective_margin']:
            result[key] = float(result[key])
        
        return result
    
    # =========================================================================
    # SEEDING DEFAULT RULES
    # =========================================================================
    
    async def seed_default_markup_rules(self) -> List[MarkupRule]:
        """Seed default markup rules."""
        defaults = [
            {
                'name': 'Default Flight Markup - B2C',
                'service_type': ServiceType.FLIGHT,
                'user_type': UserType.B2C,
                'markup_type': MarkupType.PERCENTAGE,
                'markup_value': Decimal('5.00'),
                'priority': 0
            },
            {
                'name': 'Default Flight Markup - B2B',
                'service_type': ServiceType.FLIGHT,
                'user_type': UserType.B2B,
                'markup_type': MarkupType.PERCENTAGE,
                'markup_value': Decimal('2.00'),
                'priority': 0
            },
            {
                'name': 'Default Hotel Markup - B2C',
                'service_type': ServiceType.HOTEL,
                'user_type': UserType.B2C,
                'markup_type': MarkupType.PERCENTAGE,
                'markup_value': Decimal('10.00'),
                'priority': 0
            },
            {
                'name': 'Default Hotel Markup - B2B',
                'service_type': ServiceType.HOTEL,
                'user_type': UserType.B2B,
                'markup_type': MarkupType.PERCENTAGE,
                'markup_value': Decimal('5.00'),
                'priority': 0
            },
        ]
        
        rules = []
        for data in defaults:
            # Check if exists
            stmt = select(MarkupRule).where(
                MarkupRule.tenant_id == self.tenant_id,
                MarkupRule.name == data['name']
            )
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                rule = await self.create_markup_rule(data)
                rules.append(rule)
        
        return rules
    
    async def seed_default_fee_slabs(self) -> List[ConvenienceFeeSlab]:
        """Seed default convenience fee slabs."""
        defaults = [
            # Credit Card slabs
            {
                'name': 'Credit Card - Up to 10K',
                'payment_mode': 'credit_card',
                'min_amount': Decimal(0),
                'max_amount': Decimal(10000),
                'fee_type': 'percentage',
                'fee_value': Decimal('1.50'),
                'priority': 10
            },
            {
                'name': 'Credit Card - 10K to 50K',
                'payment_mode': 'credit_card',
                'min_amount': Decimal(10001),
                'max_amount': Decimal(50000),
                'fee_type': 'percentage',
                'fee_value': Decimal('1.25'),
                'priority': 10
            },
            {
                'name': 'Credit Card - Above 50K',
                'payment_mode': 'credit_card',
                'min_amount': Decimal(50001),
                'max_amount': None,
                'fee_type': 'percentage',
                'fee_value': Decimal('1.00'),
                'priority': 10
            },
            # Debit Card slabs
            {
                'name': 'Debit Card - All Amounts',
                'payment_mode': 'debit_card',
                'min_amount': Decimal(0),
                'max_amount': None,
                'fee_type': 'percentage',
                'fee_value': Decimal('0.75'),
                'priority': 5
            },
            # UPI - Zero fee
            {
                'name': 'UPI - No Fee',
                'payment_mode': 'upi',
                'min_amount': Decimal(0),
                'max_amount': None,
                'fee_type': 'fixed',
                'fee_value': Decimal(0),
                'priority': 5
            },
            # Net Banking
            {
                'name': 'Net Banking',
                'payment_mode': 'netbanking',
                'min_amount': Decimal(0),
                'max_amount': None,
                'fee_type': 'fixed',
                'fee_value': Decimal(10),
                'priority': 5
            },
        ]
        
        slabs = []
        for data in defaults:
            # Check if exists
            stmt = select(ConvenienceFeeSlab).where(
                ConvenienceFeeSlab.tenant_id == self.tenant_id,
                ConvenienceFeeSlab.name == data['name']
            )
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                slab = await self.create_fee_slab(data)
                slabs.append(slab)
        
        return slabs
