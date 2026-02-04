"""
CMS Database Models

SQLAlchemy models for content management.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    ForeignKey, DateTime, Date, Enum, Index, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from typing import Optional, List
import enum

from app.core.database import Base


class SliderStatus(str, enum.Enum):
    """Slider status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCHEDULED = "scheduled"


class OfferStatus(str, enum.Enum):
    """Offer/coupon status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"


class PostStatus(str, enum.Enum):
    """Blog post status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Slider(Base):
    """
    Homepage/page sliders/banners.
    """
    __tablename__ = "cms_sliders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Slider info
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Media
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    mobile_image_url: Mapped[Optional[str]] = mapped_column(String(500))  # For mobile devices
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Link
    link_url: Mapped[Optional[str]] = mapped_column(String(500))
    link_text: Mapped[Optional[str]] = mapped_column(String(100))
    link_target: Mapped[str] = mapped_column(String(20), default="_self")  # _self, _blank
    
    # Placement
    placement: Mapped[str] = mapped_column(String(50), default="homepage")  # homepage, flights, hotels, etc.
    
    # Scheduling
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Status
    status: Mapped[SliderStatus] = mapped_column(
        Enum(SliderStatus),
        default=SliderStatus.ACTIVE
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Tenant (for white-label)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_slider_placement', 'placement'),
        Index('idx_slider_status', 'status'),
        Index('idx_slider_tenant', 'tenant_id'),
    )


class Offer(Base):
    """
    Offers, coupons, and promotional codes.
    """
    __tablename__ = "cms_offers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Offer info
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    terms_conditions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Coupon code
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)  # Promo code
    
    # Discount
    discount_type: Mapped[str] = mapped_column(String(20), default="percentage")  # percentage, fixed
    discount_value: Mapped[float] = mapped_column(Float, default=0)
    max_discount: Mapped[Optional[float]] = mapped_column(Float)  # Cap for percentage discounts
    min_order_value: Mapped[float] = mapped_column(Float, default=0)
    
    # Usage limits
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)  # Total uses allowed
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1)  # Uses per user
    current_usage: Mapped[int] = mapped_column(Integer, default=0)
    
    # Applicability
    applicable_to: Mapped[Optional[str]] = mapped_column(String(100))  # all, flights, hotels, holidays, etc.
    
    # Media
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    banner_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Scheduling
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus),
        default=OfferStatus.ACTIVE
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Tenant
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_offer_slug', 'slug'),
        Index('idx_offer_code', 'code'),
        Index('idx_offer_status', 'status'),
        Index('idx_offer_dates', 'start_date', 'end_date'),
    )


class BlogCategory(Base):
    """
    Blog post categories.
    """
    __tablename__ = "cms_blog_categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posts: Mapped[List["BlogPost"]] = relationship("BlogPost", back_populates="category")
    
    __table_args__ = (
        Index('idx_blog_cat_slug', 'slug'),
    )


class BlogPost(Base):
    """
    Blog posts/articles.
    """
    __tablename__ = "cms_blog_posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Post info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(520), nullable=False, unique=True)
    excerpt: Mapped[Optional[str]] = mapped_column(String(1000))  # Short summary
    content: Mapped[str] = mapped_column(Text, nullable=False)  # HTML content
    
    # Category
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cms_blog_categories.id"))
    
    # Media
    featured_image: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    gallery: Mapped[Optional[str]] = mapped_column(JSON)  # Additional images
    
    # Tags (JSON array)
    tags: Mapped[Optional[str]] = mapped_column(JSON)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    meta_keywords: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Status
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus),
        default=PostStatus.DRAFT
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Dates
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Author
    author_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    category: Mapped[Optional["BlogCategory"]] = relationship("BlogCategory", back_populates="posts")
    author: Mapped[Optional["User"]] = relationship("User")
    
    __table_args__ = (
        Index('idx_blog_slug', 'slug'),
        Index('idx_blog_status', 'status'),
        Index('idx_blog_category', 'category_id'),
        Index('idx_blog_published', 'published_at'),
    )


class StaticPage(Base):
    """
    Static pages like About Us, Terms, Privacy Policy, etc.
    """
    __tablename__ = "cms_static_pages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Page info
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # HTML content
    
    # Page type
    page_type: Mapped[str] = mapped_column(String(50), default="content")  # content, legal, faq
    
    # Media
    banner_image: Mapped[Optional[str]] = mapped_column(String(500))
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_footer: Mapped[bool] = mapped_column(Boolean, default=False)
    show_in_header: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Tenant
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tenants.id"))
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_page_slug', 'slug'),
        Index('idx_page_type', 'page_type'),
        Index('idx_page_tenant', 'tenant_id'),
    )


# Import for type hints
from app.auth.models import User
