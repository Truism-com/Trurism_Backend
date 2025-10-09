"""
Authentication Services

This module contains business logic for authentication operations:
- User registration and validation
- User authentication and login
- Profile management
- Agent approval workflow
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime

from app.auth.models import User, UserRole, AgentApprovalStatus
from app.auth.schemas import (
    UserRegisterRequest, UserLoginRequest, UserProfileUpdate,
    PasswordChangeRequest, AgentApprovalRequest
)
from app.core.security import SecurityManager


class AuthService:
    """
    Authentication service for user management operations.
    
    This service handles all authentication-related business logic
    including user registration, login, profile management, and
    agent approval workflows.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, user_data: UserRegisterRequest) -> User:
        """
        Register a new user in the system.
        
        Args:
            user_data (UserRegisterRequest): User registration data
            
        Returns:
            User: Created user object
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            email=user_data.email,
            password_hash=SecurityManager.hash_password(user_data.password),
            name=user_data.name,
            phone=user_data.phone,
            address=user_data.address,
            role=user_data.role,
            company_name=user_data.company_name,
            pan_number=user_data.pan_number,
            approval_status=AgentApprovalStatus.PENDING if user_data.role == UserRole.AGENT else None
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def authenticate_user(self, login_data: UserLoginRequest) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            login_data (UserLoginRequest): Login credentials
            
        Returns:
            Optional[User]: User object if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(login_data.email)
        
        if not user or not SecurityManager.verify_password(login_data.password, user.password_hash):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email (str): User email address
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def update_user_profile(self, user_id: int, profile_data: UserProfileUpdate) -> User:
        """
        Update user profile information.
        
        Args:
            user_id (int): User ID
            profile_data (UserProfileUpdate): Profile update data
            
        Returns:
            User: Updated user object
            
        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update profile fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def change_password(self, user_id: int, password_data: PasswordChangeRequest) -> bool:
        """
        Change user password.
        
        Args:
            user_id (int): User ID
            password_data (PasswordChangeRequest): Password change data
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            HTTPException: If current password is incorrect or user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not SecurityManager.verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = SecurityManager.hash_password(password_data.new_password)
        await self.db.commit()
        
        return True
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get all users with pagination (admin only).
        
        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            
        Returns:
            list[User]: List of users
        """
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    async def approve_agent(self, agent_id: int, approval_data: AgentApprovalRequest) -> User:
        """
        Approve or reject an agent application (admin only).
        
        Args:
            agent_id (int): Agent ID
            approval_data (AgentApprovalRequest): Approval decision
            
        Returns:
            User: Updated agent user object
            
        Raises:
            HTTPException: If agent not found or not an agent
        """
        agent = await self.get_user_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if agent.role != UserRole.AGENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an agent"
            )
        
        agent.approval_status = approval_data.approval_status
        await self.db.commit()
        await self.db.refresh(agent)
        
        return agent
    
    async def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account (admin only).
        
        Args:
            user_id (int): User ID
            
        Returns:
            bool: True if user deactivated successfully
            
        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        await self.db.commit()
        
        return True
