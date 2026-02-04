"""
CMS Service Layer

Business logic for content management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime, date
import re

from app.cms.models import (
    Slider, Offer, BlogCategory, BlogPost, StaticPage,
    SliderStatus, OfferStatus, PostStatus
)
from app.cms.schemas import (
    SliderCreate, SliderUpdate,
    OfferCreate, OfferUpdate, CouponValidation, CouponValidationResponse,
    BlogCategoryCreate, BlogCategoryUpdate,
    BlogPostCreate, BlogPostUpdate,
    StaticPageCreate, StaticPageUpdate,
    NavigationItem, NavigationResponse
)


def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text."""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:300]


class CMSService:
    """Service for content management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # SLIDER OPERATIONS
    # =========================================================================
    
    async def create_slider(
        self,
        data: SliderCreate,
        created_by_id: int,
        tenant_id: Optional[int] = None
    ) -> Slider:
        """Create a new slider."""
        slider = Slider(
            **data.model_dump(),
            created_by_id=created_by_id,
            tenant_id=tenant_id
        )
        self.db.add(slider)
        await self.db.commit()
        await self.db.refresh(slider)
        return slider
    
    async def update_slider(
        self,
        slider_id: int,
        data: SliderUpdate
    ) -> Optional[Slider]:
        """Update a slider."""
        result = await self.db.execute(
            select(Slider).where(Slider.id == slider_id)
        )
        slider = result.scalar_one_or_none()
        
        if not slider:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(slider, key, value)
        
        await self.db.commit()
        await self.db.refresh(slider)
        return slider
    
    async def get_slider(self, slider_id: int) -> Optional[Slider]:
        """Get slider by ID."""
        result = await self.db.execute(
            select(Slider).where(Slider.id == slider_id)
        )
        return result.scalar_one_or_none()
    
    async def get_sliders(
        self,
        placement: Optional[str] = None,
        status: Optional[SliderStatus] = None,
        tenant_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[Slider]:
        """Get sliders with filters."""
        query = select(Slider)
        
        conditions = []
        if placement:
            conditions.append(Slider.placement == placement)
        if status:
            conditions.append(Slider.status == status)
        if tenant_id:
            conditions.append(Slider.tenant_id == tenant_id)
        if active_only:
            today = date.today()
            conditions.append(Slider.status == SliderStatus.ACTIVE)
            conditions.append(
                or_(
                    Slider.start_date.is_(None),
                    Slider.start_date <= today
                )
            )
            conditions.append(
                or_(
                    Slider.end_date.is_(None),
                    Slider.end_date >= today
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Slider.display_order, Slider.id.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_slider(self, slider_id: int) -> bool:
        """Delete a slider."""
        result = await self.db.execute(
            select(Slider).where(Slider.id == slider_id)
        )
        slider = result.scalar_one_or_none()
        
        if not slider:
            return False
        
        await self.db.delete(slider)
        await self.db.commit()
        return True
    
    # =========================================================================
    # OFFER OPERATIONS
    # =========================================================================
    
    async def create_offer(
        self,
        data: OfferCreate,
        created_by_id: int,
        tenant_id: Optional[int] = None
    ) -> Offer:
        """Create a new offer/coupon."""
        slug = generate_slug(data.title)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while True:
            result = await self.db.execute(
                select(Offer).where(Offer.slug == slug)
            )
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        offer = Offer(
            **data.model_dump(),
            slug=slug,
            created_by_id=created_by_id,
            tenant_id=tenant_id
        )
        self.db.add(offer)
        await self.db.commit()
        await self.db.refresh(offer)
        return offer
    
    async def update_offer(
        self,
        offer_id: int,
        data: OfferUpdate
    ) -> Optional[Offer]:
        """Update an offer."""
        result = await self.db.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        offer = result.scalar_one_or_none()
        
        if not offer:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(offer, key, value)
        
        await self.db.commit()
        await self.db.refresh(offer)
        return offer
    
    async def get_offer(self, offer_id: int) -> Optional[Offer]:
        """Get offer by ID."""
        result = await self.db.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        return result.scalar_one_or_none()
    
    async def get_offer_by_slug(self, slug: str) -> Optional[Offer]:
        """Get offer by slug."""
        result = await self.db.execute(
            select(Offer).where(Offer.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_offer_by_code(self, code: str) -> Optional[Offer]:
        """Get offer by coupon code."""
        result = await self.db.execute(
            select(Offer).where(func.upper(Offer.code) == code.upper())
        )
        return result.scalar_one_or_none()
    
    async def get_offers(
        self,
        status: Optional[OfferStatus] = None,
        applicable_to: Optional[str] = None,
        is_featured: Optional[bool] = None,
        active_only: bool = False,
        tenant_id: Optional[int] = None
    ) -> List[Offer]:
        """Get offers with filters."""
        query = select(Offer)
        
        conditions = []
        if status:
            conditions.append(Offer.status == status)
        if applicable_to:
            conditions.append(
                or_(
                    Offer.applicable_to.is_(None),
                    Offer.applicable_to == "all",
                    Offer.applicable_to.contains(applicable_to)
                )
            )
        if is_featured is not None:
            conditions.append(Offer.is_featured == is_featured)
        if tenant_id:
            conditions.append(Offer.tenant_id == tenant_id)
        if active_only:
            today = date.today()
            conditions.append(Offer.status == OfferStatus.ACTIVE)
            conditions.append(Offer.start_date <= today)
            conditions.append(Offer.end_date >= today)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Offer.display_order, Offer.id.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def validate_coupon(
        self,
        data: CouponValidation,
        user_id: Optional[int] = None
    ) -> CouponValidationResponse:
        """Validate and calculate discount for a coupon code."""
        offer = await self.get_offer_by_code(data.code)
        
        if not offer:
            return CouponValidationResponse(
                valid=False,
                message="Invalid coupon code"
            )
        
        today = date.today()
        
        # Check status
        if offer.status != OfferStatus.ACTIVE:
            return CouponValidationResponse(
                valid=False,
                message="This coupon is no longer active"
            )
        
        # Check dates
        if offer.start_date > today:
            return CouponValidationResponse(
                valid=False,
                message="This coupon is not yet valid"
            )
        
        if offer.end_date < today:
            return CouponValidationResponse(
                valid=False,
                message="This coupon has expired"
            )
        
        # Check usage limit
        if offer.usage_limit and offer.current_usage >= offer.usage_limit:
            return CouponValidationResponse(
                valid=False,
                message="This coupon has reached its usage limit"
            )
        
        # Check minimum order
        if data.order_value < offer.min_order_value:
            return CouponValidationResponse(
                valid=False,
                message=f"Minimum order value of ₹{offer.min_order_value:.2f} required"
            )
        
        # Check applicability
        if offer.applicable_to and offer.applicable_to != "all":
            if data.service_type and data.service_type not in offer.applicable_to:
                return CouponValidationResponse(
                    valid=False,
                    message=f"This coupon is not valid for {data.service_type}"
                )
        
        # Calculate discount
        if offer.discount_type == "percentage":
            discount = (data.order_value * offer.discount_value) / 100
            if offer.max_discount:
                discount = min(discount, offer.max_discount)
        else:
            discount = min(offer.discount_value, data.order_value)
        
        from app.cms.schemas import OfferResponse
        
        return CouponValidationResponse(
            valid=True,
            discount_amount=round(discount, 2),
            message=f"Coupon applied! You save ₹{discount:.2f}",
            offer=OfferResponse.model_validate(offer)
        )
    
    async def increment_coupon_usage(self, offer_id: int) -> None:
        """Increment coupon usage count."""
        result = await self.db.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        offer = result.scalar_one_or_none()
        
        if offer:
            offer.current_usage += 1
            await self.db.commit()
    
    async def delete_offer(self, offer_id: int) -> bool:
        """Delete an offer."""
        result = await self.db.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        offer = result.scalar_one_or_none()
        
        if not offer:
            return False
        
        await self.db.delete(offer)
        await self.db.commit()
        return True
    
    # =========================================================================
    # BLOG CATEGORY OPERATIONS
    # =========================================================================
    
    async def create_blog_category(
        self,
        data: BlogCategoryCreate
    ) -> BlogCategory:
        """Create a blog category."""
        slug = generate_slug(data.name)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while True:
            result = await self.db.execute(
                select(BlogCategory).where(BlogCategory.slug == slug)
            )
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        category = BlogCategory(
            **data.model_dump(),
            slug=slug
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def update_blog_category(
        self,
        category_id: int,
        data: BlogCategoryUpdate
    ) -> Optional[BlogCategory]:
        """Update a blog category."""
        result = await self.db.execute(
            select(BlogCategory).where(BlogCategory.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Regenerate slug if name changed
        if 'name' in update_data:
            update_data['slug'] = generate_slug(update_data['name'])
        
        for key, value in update_data.items():
            setattr(category, key, value)
        
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def get_blog_category(
        self,
        category_id: int
    ) -> Optional[BlogCategory]:
        """Get blog category by ID."""
        result = await self.db.execute(
            select(BlogCategory).where(BlogCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_blog_category_by_slug(
        self,
        slug: str
    ) -> Optional[BlogCategory]:
        """Get blog category by slug."""
        result = await self.db.execute(
            select(BlogCategory).where(BlogCategory.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_blog_categories(
        self,
        active_only: bool = False
    ) -> List[BlogCategory]:
        """Get all blog categories."""
        query = select(BlogCategory)
        
        if active_only:
            query = query.where(BlogCategory.is_active == True)
        
        query = query.order_by(BlogCategory.display_order, BlogCategory.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_blog_category(self, category_id: int) -> bool:
        """Delete a blog category."""
        result = await self.db.execute(
            select(BlogCategory).where(BlogCategory.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            return False
        
        await self.db.delete(category)
        await self.db.commit()
        return True
    
    # =========================================================================
    # BLOG POST OPERATIONS
    # =========================================================================
    
    async def create_blog_post(
        self,
        data: BlogPostCreate,
        author_id: int
    ) -> BlogPost:
        """Create a blog post."""
        slug = generate_slug(data.title)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while True:
            result = await self.db.execute(
                select(BlogPost).where(BlogPost.slug == slug)
            )
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        post_data = data.model_dump(exclude={'publish_now'})
        
        # Set published_at if publishing now
        published_at = None
        if data.publish_now or data.status == PostStatus.PUBLISHED:
            published_at = datetime.utcnow()
            post_data['status'] = PostStatus.PUBLISHED
        
        post = BlogPost(
            **post_data,
            slug=slug,
            author_id=author_id,
            published_at=published_at
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        
        # Load relationships
        result = await self.db.execute(
            select(BlogPost)
            .options(selectinload(BlogPost.category))
            .where(BlogPost.id == post.id)
        )
        return result.scalar_one()
    
    async def update_blog_post(
        self,
        post_id: int,
        data: BlogPostUpdate
    ) -> Optional[BlogPost]:
        """Update a blog post."""
        result = await self.db.execute(
            select(BlogPost).where(BlogPost.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        if not post:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Update published_at if status changed to published
        if update_data.get('status') == PostStatus.PUBLISHED and not post.published_at:
            update_data['published_at'] = datetime.utcnow()
        
        for key, value in update_data.items():
            setattr(post, key, value)
        
        await self.db.commit()
        
        # Reload with relationships
        result = await self.db.execute(
            select(BlogPost)
            .options(selectinload(BlogPost.category))
            .where(BlogPost.id == post.id)
        )
        return result.scalar_one()
    
    async def get_blog_post(self, post_id: int) -> Optional[BlogPost]:
        """Get blog post by ID."""
        result = await self.db.execute(
            select(BlogPost)
            .options(selectinload(BlogPost.category))
            .where(BlogPost.id == post_id)
        )
        return result.scalar_one_or_none()
    
    async def get_blog_post_by_slug(
        self,
        slug: str,
        increment_views: bool = False
    ) -> Optional[BlogPost]:
        """Get blog post by slug."""
        result = await self.db.execute(
            select(BlogPost)
            .options(selectinload(BlogPost.category))
            .where(BlogPost.slug == slug)
        )
        post = result.scalar_one_or_none()
        
        if post and increment_views:
            post.view_count += 1
            await self.db.commit()
        
        return post
    
    async def get_blog_posts(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        status: Optional[PostStatus] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[BlogPost], int]:
        """Get blog posts with filters."""
        query = select(BlogPost).options(selectinload(BlogPost.category))
        count_query = select(func.count(BlogPost.id))
        
        conditions = []
        
        if category_id:
            conditions.append(BlogPost.category_id == category_id)
        
        if category_slug:
            # Get category by slug first
            cat_result = await self.db.execute(
                select(BlogCategory).where(BlogCategory.slug == category_slug)
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                conditions.append(BlogPost.category_id == cat.id)
        
        if status:
            conditions.append(BlogPost.status == status)
        
        if is_featured is not None:
            conditions.append(BlogPost.is_featured == is_featured)
        
        if search:
            search_filter = or_(
                BlogPost.title.ilike(f"%{search}%"),
                BlogPost.excerpt.ilike(f"%{search}%"),
                BlogPost.content.ilike(f"%{search}%")
            )
            conditions.append(search_filter)
        
        if tag:
            # JSON contains check - syntax varies by database
            conditions.append(BlogPost.tags.contains([tag]))
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(BlogPost.published_at.desc().nullsfirst(), BlogPost.id.desc())
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        posts = list(result.scalars().all())
        
        return posts, total
    
    async def get_related_posts(
        self,
        post_id: int,
        limit: int = 4
    ) -> List[BlogPost]:
        """Get related posts based on category and tags."""
        # Get original post
        post = await self.get_blog_post(post_id)
        if not post:
            return []
        
        query = select(BlogPost).options(selectinload(BlogPost.category))
        
        conditions = [
            BlogPost.id != post_id,
            BlogPost.status == PostStatus.PUBLISHED
        ]
        
        # Same category
        if post.category_id:
            conditions.append(BlogPost.category_id == post.category_id)
        
        query = query.where(and_(*conditions))
        query = query.order_by(BlogPost.published_at.desc())
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_blog_post(self, post_id: int) -> bool:
        """Delete a blog post."""
        result = await self.db.execute(
            select(BlogPost).where(BlogPost.id == post_id)
        )
        post = result.scalar_one_or_none()
        
        if not post:
            return False
        
        await self.db.delete(post)
        await self.db.commit()
        return True
    
    # =========================================================================
    # STATIC PAGE OPERATIONS
    # =========================================================================
    
    async def create_static_page(
        self,
        data: StaticPageCreate,
        created_by_id: int,
        tenant_id: Optional[int] = None
    ) -> StaticPage:
        """Create a static page."""
        slug = data.slug or generate_slug(data.title)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while True:
            result = await self.db.execute(
                select(StaticPage).where(StaticPage.slug == slug)
            )
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        page_data = data.model_dump()
        page_data['slug'] = slug
        
        page = StaticPage(
            **page_data,
            created_by_id=created_by_id,
            tenant_id=tenant_id
        )
        self.db.add(page)
        await self.db.commit()
        await self.db.refresh(page)
        return page
    
    async def update_static_page(
        self,
        page_id: int,
        data: StaticPageUpdate
    ) -> Optional[StaticPage]:
        """Update a static page."""
        result = await self.db.execute(
            select(StaticPage).where(StaticPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(page, key, value)
        
        await self.db.commit()
        await self.db.refresh(page)
        return page
    
    async def get_static_page(self, page_id: int) -> Optional[StaticPage]:
        """Get static page by ID."""
        result = await self.db.execute(
            select(StaticPage).where(StaticPage.id == page_id)
        )
        return result.scalar_one_or_none()
    
    async def get_static_page_by_slug(
        self,
        slug: str,
        tenant_id: Optional[int] = None
    ) -> Optional[StaticPage]:
        """Get static page by slug."""
        query = select(StaticPage).where(StaticPage.slug == slug)
        
        if tenant_id:
            query = query.where(
                or_(
                    StaticPage.tenant_id == tenant_id,
                    StaticPage.tenant_id.is_(None)
                )
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_static_pages(
        self,
        page_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        show_in_footer: Optional[bool] = None,
        show_in_header: Optional[bool] = None,
        tenant_id: Optional[int] = None
    ) -> List[StaticPage]:
        """Get static pages with filters."""
        query = select(StaticPage)
        
        conditions = []
        if page_type:
            conditions.append(StaticPage.page_type == page_type)
        if is_active is not None:
            conditions.append(StaticPage.is_active == is_active)
        if show_in_footer is not None:
            conditions.append(StaticPage.show_in_footer == show_in_footer)
        if show_in_header is not None:
            conditions.append(StaticPage.show_in_header == show_in_header)
        if tenant_id:
            conditions.append(
                or_(
                    StaticPage.tenant_id == tenant_id,
                    StaticPage.tenant_id.is_(None)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(StaticPage.display_order, StaticPage.title)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_navigation(
        self,
        tenant_id: Optional[int] = None
    ) -> NavigationResponse:
        """Get navigation items for header and footer."""
        header_pages = await self.get_static_pages(
            is_active=True,
            show_in_header=True,
            tenant_id=tenant_id
        )
        
        footer_pages = await self.get_static_pages(
            is_active=True,
            show_in_footer=True,
            tenant_id=tenant_id
        )
        
        return NavigationResponse(
            header_pages=[
                NavigationItem(
                    id=p.id,
                    title=p.title,
                    slug=p.slug,
                    url=f"/page/{p.slug}"
                ) for p in header_pages
            ],
            footer_pages=[
                NavigationItem(
                    id=p.id,
                    title=p.title,
                    slug=p.slug,
                    url=f"/page/{p.slug}"
                ) for p in footer_pages
            ]
        )
    
    async def delete_static_page(self, page_id: int) -> bool:
        """Delete a static page."""
        result = await self.db.execute(
            select(StaticPage).where(StaticPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return False
        
        await self.db.delete(page)
        await self.db.commit()
        return True
