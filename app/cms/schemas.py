"""
CMS Pydantic Schemas

Schemas for content management validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime, date

from app.cms.models import SliderStatus, OfferStatus, PostStatus


# =============================================================================
# SLIDER SCHEMAS
# =============================================================================

class SliderBase(BaseModel):
    """Base slider schema."""
    title: str = Field(..., max_length=300)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    image_url: str = Field(..., max_length=500)
    mobile_image_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    link_text: Optional[str] = Field(None, max_length=100)
    link_target: str = Field("_self", max_length=20)
    placement: str = Field("homepage", max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    display_order: int = Field(0, ge=0)


class SliderCreate(SliderBase):
    """Schema for creating a slider."""
    status: SliderStatus = SliderStatus.ACTIVE


class SliderUpdate(BaseModel):
    """Schema for updating a slider."""
    title: Optional[str] = Field(None, max_length=300)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    mobile_image_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    link_text: Optional[str] = Field(None, max_length=100)
    link_target: Optional[str] = Field(None, max_length=20)
    placement: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SliderStatus] = None
    display_order: Optional[int] = Field(None, ge=0)


class SliderResponse(SliderBase):
    """Slider response schema."""
    id: int
    status: SliderStatus
    tenant_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SliderListResponse(BaseModel):
    """List of sliders response."""
    items: List[SliderResponse]
    total: int
    placement: Optional[str] = None


# =============================================================================
# OFFER SCHEMAS
# =============================================================================

class OfferBase(BaseModel):
    """Base offer schema."""
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    terms_conditions: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    discount_type: str = Field("percentage", pattern="^(percentage|fixed)$")
    discount_value: float = Field(..., ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    min_order_value: float = Field(0, ge=0)
    usage_limit: Optional[int] = Field(None, ge=1)
    per_user_limit: int = Field(1, ge=1)
    applicable_to: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    start_date: date
    end_date: date
    is_featured: bool = False
    display_order: int = Field(0, ge=0)
    
    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v, info):
        if info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class OfferCreate(OfferBase):
    """Schema for creating an offer."""
    status: OfferStatus = OfferStatus.ACTIVE


class OfferUpdate(BaseModel):
    """Schema for updating an offer."""
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    terms_conditions: Optional[str] = None
    code: Optional[str] = Field(None, max_length=50)
    discount_type: Optional[str] = Field(None, pattern="^(percentage|fixed)$")
    discount_value: Optional[float] = Field(None, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    min_order_value: Optional[float] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, ge=1)
    per_user_limit: Optional[int] = Field(None, ge=1)
    applicable_to: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[OfferStatus] = None
    is_featured: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class OfferResponse(BaseModel):
    """Offer response schema."""
    id: int
    title: str
    slug: str
    description: Optional[str] = None
    terms_conditions: Optional[str] = None
    code: Optional[str] = None
    discount_type: str
    discount_value: float
    max_discount: Optional[float] = None
    min_order_value: float
    usage_limit: Optional[int] = None
    per_user_limit: int
    current_usage: int
    applicable_to: Optional[str] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None
    start_date: date
    end_date: date
    status: OfferStatus
    is_featured: bool
    display_order: int
    tenant_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OfferListResponse(BaseModel):
    """List of offers response."""
    items: List[OfferResponse]
    total: int


class CouponValidation(BaseModel):
    """Coupon validation request."""
    code: str
    order_value: float = Field(..., ge=0)
    service_type: Optional[str] = None  # flights, hotels, etc.


class CouponValidationResponse(BaseModel):
    """Coupon validation response."""
    valid: bool
    discount_amount: float = 0
    message: str
    offer: Optional[OfferResponse] = None


# =============================================================================
# BLOG CATEGORY SCHEMAS
# =============================================================================

class BlogCategoryBase(BaseModel):
    """Base blog category schema."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    display_order: int = Field(0, ge=0)


class BlogCategoryCreate(BlogCategoryBase):
    """Schema for creating a blog category."""
    pass


class BlogCategoryUpdate(BaseModel):
    """Schema for updating a blog category."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class BlogCategoryResponse(BlogCategoryBase):
    """Blog category response schema."""
    id: int
    slug: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# BLOG POST SCHEMAS
# =============================================================================

class BlogPostBase(BaseModel):
    """Base blog post schema."""
    title: str = Field(..., max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: str
    category_id: Optional[int] = None
    featured_image: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    gallery: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    is_featured: bool = False


class BlogPostCreate(BlogPostBase):
    """Schema for creating a blog post."""
    status: PostStatus = PostStatus.DRAFT
    publish_now: bool = False


class BlogPostUpdate(BaseModel):
    """Schema for updating a blog post."""
    title: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None
    category_id: Optional[int] = None
    featured_image: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    gallery: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    status: Optional[PostStatus] = None
    is_featured: Optional[bool] = None


class BlogPostResponse(BaseModel):
    """Blog post response schema."""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    category_id: Optional[int] = None
    category: Optional[BlogCategoryResponse] = None
    featured_image: Optional[str] = None
    thumbnail_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    status: PostStatus
    is_featured: bool
    published_at: Optional[datetime] = None
    view_count: int
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BlogPostListItem(BaseModel):
    """Blog post list item (without full content)."""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    category: Optional[BlogCategoryResponse] = None
    featured_image: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = None
    status: PostStatus
    is_featured: bool
    published_at: Optional[datetime] = None
    view_count: int
    author_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BlogPostListResponse(BaseModel):
    """List of blog posts response."""
    items: List[BlogPostListItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# STATIC PAGE SCHEMAS
# =============================================================================

class StaticPageBase(BaseModel):
    """Base static page schema."""
    title: str = Field(..., max_length=300)
    content: str
    page_type: str = Field("content", max_length=50)
    banner_image: Optional[str] = Field(None, max_length=500)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    show_in_footer: bool = False
    show_in_header: bool = False
    display_order: int = Field(0, ge=0)


class StaticPageCreate(StaticPageBase):
    """Schema for creating a static page."""
    slug: Optional[str] = Field(None, max_length=320)  # Auto-generated if not provided


class StaticPageUpdate(BaseModel):
    """Schema for updating a static page."""
    title: Optional[str] = Field(None, max_length=300)
    slug: Optional[str] = Field(None, max_length=320)
    content: Optional[str] = None
    page_type: Optional[str] = Field(None, max_length=50)
    banner_image: Optional[str] = Field(None, max_length=500)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    show_in_footer: Optional[bool] = None
    show_in_header: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class StaticPageResponse(StaticPageBase):
    """Static page response schema."""
    id: int
    slug: str
    tenant_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StaticPageListResponse(BaseModel):
    """List of static pages response."""
    items: List[StaticPageResponse]
    total: int


# =============================================================================
# NAVIGATION SCHEMAS (for header/footer)
# =============================================================================

class NavigationItem(BaseModel):
    """Navigation menu item."""
    id: int
    title: str
    slug: str
    url: str


class NavigationResponse(BaseModel):
    """Navigation response for header/footer."""
    header_pages: List[NavigationItem]
    footer_pages: List[NavigationItem]
