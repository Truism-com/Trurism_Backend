"""
Markup Services

Business logic for markup and commission calculations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from app.markup.models import MarkupRule, ServiceType
from app.markup.schemas import MarkupRuleCreate, MarkupRuleUpdate, PriceBreakdown


class MarkupService:
    """Service for markup and commission management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_markup_rule(
        self,
        rule_data: MarkupRuleCreate,
        created_by_id: int
    ) -> MarkupRule:
        """
        Create a new markup rule.
        
        Args:
            rule_data: Markup rule creation data
            created_by_id: ID of admin creating the rule
            
        Returns:
            MarkupRule: Created markup rule
        """
        rule = MarkupRule(
            **rule_data.model_dump(),
            created_by_id=created_by_id
        )
        
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        
        return rule
    
    async def get_markup_rule(self, rule_id: int) -> Optional[MarkupRule]:
        """Get markup rule by ID."""
        result = await self.db.execute(
            select(MarkupRule).where(MarkupRule.id == rule_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_markup_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        service_type: Optional[ServiceType] = None,
        active_only: bool = True,
        tenant_id: Optional[int] = None
    ) -> Tuple[List[MarkupRule], int]:
        """
        Get all markup rules with filtering.
        
        Args:
            skip: Records to skip
            limit: Max records to return
            service_type: Filter by service type
            active_only: Only active rules
            tenant_id: Filter by tenant
            
        Returns:
            Tuple[List[MarkupRule], int]: Rules and total count
        """
        query = select(MarkupRule)
        conditions = []
        
        if service_type:
            conditions.append(MarkupRule.service_type == service_type)
        
        if active_only:
            conditions.append(MarkupRule.is_active == True)
        
        if tenant_id is not None:
            conditions.append(
                (MarkupRule.tenant_id == tenant_id) | (MarkupRule.tenant_id == None)
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        from sqlalchemy import func, select as select_func
        count_query = select_func(func.count(MarkupRule.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results - ordered by priority (descending) then created_at
        query = query.order_by(
            MarkupRule.priority.desc(),
            MarkupRule.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        rules = list(result.scalars().all())
        
        return rules, total
    
    async def update_markup_rule(
        self,
        rule_id: int,
        update_data: MarkupRuleUpdate
    ) -> MarkupRule:
        """
        Update markup rule.
        
        Args:
            rule_id: Rule ID
            update_data: Update data
            
        Returns:
            MarkupRule: Updated rule
            
        Raises:
            HTTPException: If rule not found
        """
        rule = await self.get_markup_rule(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Markup rule not found"
            )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(rule, field, value)
        
        await self.db.commit()
        await self.db.refresh(rule)
        
        return rule
    
    async def delete_markup_rule(self, rule_id: int) -> bool:
        """
        Delete (deactivate) markup rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            bool: Success status
            
        Raises:
            HTTPException: If rule not found
        """
        rule = await self.get_markup_rule(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Markup rule not found"
            )
        
        rule.is_active = False
        await self.db.commit()
        
        return True
    
    async def calculate_price_with_markup(
        self,
        service_type: ServiceType,
        base_price: float,
        search_params: Dict[str, Any],
        tenant_id: Optional[int] = None,
        is_agent_booking: bool = False
    ) -> PriceBreakdown:
        """
        Calculate final price with markup applied.
        
        This is the CORE pricing function. It:
        1. Fetches applicable markup rules
        2. Applies highest priority matching rule
        3. Calculates admin margin and agent commission
        4. Adds taxes
        5. Returns detailed breakdown
        
        Args:
            service_type: Type of service (flight, hotel, etc.)
            base_price: Original supplier price
            search_params: Search/booking parameters for rule matching
            tenant_id: Current tenant ID
            is_agent_booking: Whether this is an agent booking
            
        Returns:
            PriceBreakdown: Detailed price breakdown
        """
        # Add base price to search params for min/max price conditions
        search_params_with_price = {**search_params, "price": base_price}
        
        # Get applicable rules
        rules, _ = await self.get_all_markup_rules(
            service_type=service_type,
            active_only=True,
            tenant_id=tenant_id,
            limit=100
        )
        
        # Filter rules that match current conditions
        applicable_rules = []
        for rule in rules:
            # Check if rule is valid (time-based)
            if not rule.is_valid():
                continue
            
            # Check if service type matches (ALL matches everything)
            if rule.service_type != service_type and rule.service_type != ServiceType.ALL:
                continue
            
            # Check if conditions match
            if rule.matches_conditions(search_params_with_price):
                applicable_rules.append(rule)
        
        # Apply highest priority rule (rules are already sorted by priority)
        markup_amount = 0.0
        agent_commission = 0.0
        applied_rule_names = []
        
        if applicable_rules:
            # Take first rule (highest priority)
            selected_rule = applicable_rules[0]
            markup_amount = selected_rule.calculate_markup(base_price)
            
            # Calculate agent commission if this is an agent booking
            if is_agent_booking:
                agent_commission = selected_rule.calculate_agent_commission(markup_amount)
            
            applied_rule_names.append(selected_rule.name)
        
        # Calculate admin margin (markup - agent commission)
        admin_margin = markup_amount - agent_commission
        
        # Calculate taxes (18% GST on total)
        subtotal = base_price + markup_amount
        taxes = subtotal * 0.18
        
        # Calculate final price
        total_price = subtotal + taxes
        
        return PriceBreakdown(
            base_price=round(base_price, 2),
            markup_amount=round(markup_amount, 2),
            admin_margin=round(admin_margin, 2),
            agent_commission=round(agent_commission, 2),
            taxes=round(taxes, 2),
            total_price=round(total_price, 2),
            applied_rules=applied_rule_names
        )
