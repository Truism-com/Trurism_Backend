"""
CMS API Endpoints

REST API for content management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.cms.models import SliderStatus, OfferStatus, PostStatus
from app.cms.services import CMSService
from app.cms.schemas import (
    SliderCreate, SliderUpdate, SliderResponse, SliderListResponse,
    OfferCreate, OfferUpdate, OfferResponse, OfferListResponse,
    CouponValidation, CouponValidationResponse,
    BlogCategoryCreate, BlogCategoryUpdate, BlogCategoryResponse,
    BlogPostCreate, BlogPostUpdate, BlogPostResponse,
    BlogPostListItem, BlogPostListResponse,
    StaticPageCreate, StaticPageUpdate, StaticPageResponse, StaticPageListResponse,
    NavigationResponse
)

router = APIRouter(prefix="/cms", tags=["CMS"])


# =============================================================================
# SLIDER ENDPOINTS
# =============================================================================

@router.get("/sliders", response_model=SliderListResponse)
async def get_sliders(
    placement: Optional[str] = Query(None, description="Filter by placement (homepage, flights, etc.)"),
    db: AsyncSession = Depends(get_db)
):
    """Get active sliders for a specific placement (public)."""
    service = CMSService(db)
    sliders = await service.get_sliders(
        placement=placement,
        active_only=True
    )
    return SliderListResponse(
        items=[SliderResponse.model_validate(s) for s in sliders],
        total=len(sliders),
        placement=placement
    )


@router.get("/admin/sliders", response_model=SliderListResponse)
async def admin_get_sliders(
    placement: Optional[str] = None,
    status: Optional[SliderStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all sliders (admin)."""
    service = CMSService(db)
    sliders = await service.get_sliders(
        placement=placement,
        status=status
    )
    return SliderListResponse(
        items=[SliderResponse.model_validate(s) for s in sliders],
        total=len(sliders),
        placement=placement
    )


@router.post("/admin/sliders", response_model=SliderResponse)
async def create_slider(
    data: SliderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new slider (admin)."""
    service = CMSService(db)
    slider = await service.create_slider(
        data=data,
        created_by_id=current_user.id
    )
    return SliderResponse.model_validate(slider)


@router.get("/admin/sliders/{slider_id}", response_model=SliderResponse)
async def get_slider(
    slider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get slider by ID (admin)."""
    service = CMSService(db)
    slider = await service.get_slider(slider_id)
    if not slider:
        raise HTTPException(status_code=404, detail="Slider not found")
    return SliderResponse.model_validate(slider)


@router.put("/admin/sliders/{slider_id}", response_model=SliderResponse)
async def update_slider(
    slider_id: int,
    data: SliderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a slider (admin)."""
    service = CMSService(db)
    slider = await service.update_slider(slider_id, data)
    if not slider:
        raise HTTPException(status_code=404, detail="Slider not found")
    return SliderResponse.model_validate(slider)


@router.delete("/admin/sliders/{slider_id}")
async def delete_slider(
    slider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a slider (admin)."""
    service = CMSService(db)
    deleted = await service.delete_slider(slider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Slider not found")
    return {"message": "Slider deleted successfully"}


# =============================================================================
# OFFER/COUPON ENDPOINTS
# =============================================================================

@router.get("/offers", response_model=OfferListResponse)
async def get_offers(
    applicable_to: Optional[str] = Query(None, description="Filter by service type"),
    featured_only: bool = Query(False, description="Show only featured offers"),
    db: AsyncSession = Depends(get_db)
):
    """Get active offers (public)."""
    service = CMSService(db)
    offers = await service.get_offers(
        applicable_to=applicable_to,
        is_featured=True if featured_only else None,
        active_only=True
    )
    return OfferListResponse(
        items=[OfferResponse.model_validate(o) for o in offers],
        total=len(offers)
    )


@router.get("/offers/{slug}", response_model=OfferResponse)
async def get_offer_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get offer by slug (public)."""
    service = CMSService(db)
    offer = await service.get_offer_by_slug(slug)
    if not offer or offer.status != OfferStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Offer not found")
    return OfferResponse.model_validate(offer)


@router.post("/offers/validate", response_model=CouponValidationResponse)
async def validate_coupon(
    data: CouponValidation,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Validate a coupon code and calculate discount."""
    service = CMSService(db)
    user_id = current_user.id if current_user else None
    return await service.validate_coupon(data, user_id)


@router.get("/admin/offers", response_model=OfferListResponse)
async def admin_get_offers(
    status: Optional[OfferStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all offers (admin)."""
    service = CMSService(db)
    offers = await service.get_offers(status=status)
    return OfferListResponse(
        items=[OfferResponse.model_validate(o) for o in offers],
        total=len(offers)
    )


@router.post("/admin/offers", response_model=OfferResponse)
async def create_offer(
    data: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new offer (admin)."""
    service = CMSService(db)
    offer = await service.create_offer(
        data=data,
        created_by_id=current_user.id
    )
    return OfferResponse.model_validate(offer)


@router.get("/admin/offers/{offer_id}", response_model=OfferResponse)
async def admin_get_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get offer by ID (admin)."""
    service = CMSService(db)
    offer = await service.get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return OfferResponse.model_validate(offer)


@router.put("/admin/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: int,
    data: OfferUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an offer (admin)."""
    service = CMSService(db)
    offer = await service.update_offer(offer_id, data)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return OfferResponse.model_validate(offer)


@router.delete("/admin/offers/{offer_id}")
async def delete_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete an offer (admin)."""
    service = CMSService(db)
    deleted = await service.delete_offer(offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found")
    return {"message": "Offer deleted successfully"}


# =============================================================================
# BLOG CATEGORY ENDPOINTS
# =============================================================================

@router.get("/blog/categories", response_model=list[BlogCategoryResponse])
async def get_blog_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get active blog categories (public)."""
    service = CMSService(db)
    categories = await service.get_blog_categories(active_only=True)
    return [BlogCategoryResponse.model_validate(c) for c in categories]


@router.get("/admin/blog/categories", response_model=list[BlogCategoryResponse])
async def admin_get_blog_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all blog categories (admin)."""
    service = CMSService(db)
    categories = await service.get_blog_categories()
    return [BlogCategoryResponse.model_validate(c) for c in categories]


@router.post("/admin/blog/categories", response_model=BlogCategoryResponse)
async def create_blog_category(
    data: BlogCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a blog category (admin)."""
    service = CMSService(db)
    category = await service.create_blog_category(data)
    return BlogCategoryResponse.model_validate(category)


@router.put("/admin/blog/categories/{category_id}", response_model=BlogCategoryResponse)
async def update_blog_category(
    category_id: int,
    data: BlogCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a blog category (admin)."""
    service = CMSService(db)
    category = await service.update_blog_category(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return BlogCategoryResponse.model_validate(category)


@router.delete("/admin/blog/categories/{category_id}")
async def delete_blog_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a blog category (admin)."""
    service = CMSService(db)
    deleted = await service.delete_blog_category(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


# =============================================================================
# BLOG POST ENDPOINTS
# =============================================================================

@router.get("/blog/posts", response_model=BlogPostListResponse)
async def get_blog_posts(
    category: Optional[str] = Query(None, description="Category slug"),
    search: Optional[str] = Query(None, description="Search in title/content"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    featured_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get published blog posts (public)."""
    service = CMSService(db)
    posts, total = await service.get_blog_posts(
        category_slug=category,
        status=PostStatus.PUBLISHED,
        is_featured=True if featured_only else None,
        search=search,
        tag=tag,
        page=page,
        page_size=page_size
    )
    return BlogPostListResponse(
        items=[BlogPostListItem.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/blog/posts/{slug}", response_model=BlogPostResponse)
async def get_blog_post_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get blog post by slug (public)."""
    service = CMSService(db)
    post = await service.get_blog_post_by_slug(slug, increment_views=True)
    if not post or post.status != PostStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Post not found")
    return BlogPostResponse.model_validate(post)


@router.get("/blog/posts/{slug}/related", response_model=list[BlogPostListItem])
async def get_related_posts(
    slug: str,
    limit: int = Query(4, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get related blog posts."""
    service = CMSService(db)
    post = await service.get_blog_post_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    related = await service.get_related_posts(post.id, limit)
    return [BlogPostListItem.model_validate(p) for p in related]


@router.get("/admin/blog/posts", response_model=BlogPostListResponse)
async def admin_get_blog_posts(
    category_id: Optional[int] = None,
    status: Optional[PostStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all blog posts (admin)."""
    service = CMSService(db)
    posts, total = await service.get_blog_posts(
        category_id=category_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )
    return BlogPostListResponse(
        items=[BlogPostListItem.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/admin/blog/posts", response_model=BlogPostResponse)
async def create_blog_post(
    data: BlogPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a blog post (admin)."""
    service = CMSService(db)
    post = await service.create_blog_post(
        data=data,
        author_id=current_user.id
    )
    return BlogPostResponse.model_validate(post)


@router.get("/admin/blog/posts/{post_id}", response_model=BlogPostResponse)
async def admin_get_blog_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get blog post by ID (admin)."""
    service = CMSService(db)
    post = await service.get_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BlogPostResponse.model_validate(post)


@router.put("/admin/blog/posts/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: int,
    data: BlogPostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a blog post (admin)."""
    service = CMSService(db)
    post = await service.update_blog_post(post_id, data)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BlogPostResponse.model_validate(post)


@router.delete("/admin/blog/posts/{post_id}")
async def delete_blog_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a blog post (admin)."""
    service = CMSService(db)
    deleted = await service.delete_blog_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}


# =============================================================================
# STATIC PAGE ENDPOINTS
# =============================================================================

@router.get("/pages/navigation", response_model=NavigationResponse)
async def get_navigation(
    db: AsyncSession = Depends(get_db)
):
    """Get navigation items for header and footer."""
    service = CMSService(db)
    return await service.get_navigation()


@router.get("/pages/{slug}", response_model=StaticPageResponse)
async def get_static_page_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get static page by slug (public)."""
    service = CMSService(db)
    page = await service.get_static_page_by_slug(slug)
    if not page or not page.is_active:
        raise HTTPException(status_code=404, detail="Page not found")
    return StaticPageResponse.model_validate(page)


@router.get("/admin/pages", response_model=StaticPageListResponse)
async def admin_get_static_pages(
    page_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all static pages (admin)."""
    service = CMSService(db)
    pages = await service.get_static_pages(page_type=page_type)
    return StaticPageListResponse(
        items=[StaticPageResponse.model_validate(p) for p in pages],
        total=len(pages)
    )


@router.post("/admin/pages", response_model=StaticPageResponse)
async def create_static_page(
    data: StaticPageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a static page (admin)."""
    service = CMSService(db)
    page = await service.create_static_page(
        data=data,
        created_by_id=current_user.id
    )
    return StaticPageResponse.model_validate(page)


@router.get("/admin/pages/{page_id}", response_model=StaticPageResponse)
async def admin_get_static_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get static page by ID (admin)."""
    service = CMSService(db)
    page = await service.get_static_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return StaticPageResponse.model_validate(page)


@router.put("/admin/pages/{page_id}", response_model=StaticPageResponse)
async def update_static_page(
    page_id: int,
    data: StaticPageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a static page (admin)."""
    service = CMSService(db)
    page = await service.update_static_page(page_id, data)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return StaticPageResponse.model_validate(page)


@router.delete("/admin/pages/{page_id}")
async def delete_static_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a static page (admin)."""
    service = CMSService(db)
    deleted = await service.delete_static_page(page_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": "Page deleted successfully"}
