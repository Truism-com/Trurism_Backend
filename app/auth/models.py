"""
Authentication Database Models

This module defines the database models for user authentication:
- User model with role-based access control
- User profile information
- Agent-specific fields for travel agents
- Audit fields for tracking user activity
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.core.database import Base
from app.core.mixins import TenantMixin


class UserRole(str, enum.Enum):
    """
    User roles in the travel booking system.
    
    - CUSTOMER: Regular users who can make bookings
    - AGENT: Travel agents who can make bookings for customers
    - ADMIN: System administrators with full access
    """
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"


class AgentApprovalStatus(str, enum.Enum):
    """
    Agent approval status for travel agents.
    
    - PENDING: Agent registration awaiting approval
    - APPROVED: Agent approved and can operate
    - REJECTED: Agent registration rejected
    - SUSPENDED: Agent temporarily suspended
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class User(Base, TenantMixin):
    """
    User model for authentication and authorization.
    
    This model stores user information including authentication details,
    role-based access control, and profile information for the travel
    booking platform.
    """
    __tablename__ = "users"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # User information
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Agent-specific fields
    company_name = Column(String(255), nullable=True)  # Required for agents
    pan_number = Column(String(20), nullable=True)     # Required for agents
    approval_status = Column(Enum(AgentApprovalStatus), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    flight_bookings = relationship("FlightBooking", back_populates="user", foreign_keys="[FlightBooking.user_id]")
    hotel_bookings = relationship("HotelBooking", back_populates="user", foreign_keys="[HotelBooking.user_id]")
    bus_bookings = relationship("BusBooking", back_populates="user", foreign_keys="[BusBooking.user_id]")
    # Refresh tokens relationship
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    # Wallet relationship
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    # Social accounts (dashboard module)
    social_accounts = relationship("SocialAccount", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_agent(self) -> bool:
        """Check if user is a travel agent."""
        return self.role == UserRole.AGENT
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an administrator."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_approved_agent(self) -> bool:
        """Check if agent is approved and can operate."""
        return self.is_agent and self.approval_status == AgentApprovalStatus.APPROVED


class RefreshToken(Base, TenantMixin):
    """
    Refresh token model to persist issued refresh tokens.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationship back to user (optional foreign key relationship is handled by migrations)
    user = relationship("User", back_populates="refresh_tokens")


class TokenBlacklist(Base):
    """
    Token blacklist model for revoking tokens when Redis is unavailable.

    Stores blacklisted access tokens (mainly for logout) as a database fallback
    when Redis is not configured. This ensures logout works even without Redis.
    """
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(500), unique=True, nullable=False, index=True)  # Token identifier
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional, for audit trail
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)  # When token naturally expires
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())  # When it was blacklisted
