"""
Authentication API Endpoints

This module defines FastAPI endpoints for authentication operations:
- User registration and login
- Token refresh and logout
- User profile management
- Password change functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import timedelta

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.core.database import get_database_session
from app.core.security import SecurityManager
from app.auth.models import User
from app.auth.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    RefreshTokenRequest, UserProfileResponse, UserProfileUpdate,
    PasswordChangeRequest
)
from app.auth.services import AuthService
from app.core.config import settings
from app.auth.schemas import GoogleLoginRequest
from app.auth.models import User, UserRole

# Router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["Authentication"])

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    This dependency extracts the user from the JWT token and returns
    the user object for use in protected endpoints.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = await SecurityManager.verify_token(token, "access")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and verify admin role.
    
    This dependency ensures only admin users can access admin endpoints.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current authenticated admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Register a new user in the system.
    
    Creates a new user account with the provided information.
    Agents require additional company and PAN information.
    
    Args:
        user_data: User registration data
        request: Request object (for tenant context)
        db: Database session
        
    Returns:
        UserProfileResponse: Created user information
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    auth_service = AuthService(db)
    try:
        user = await auth_service.register_user(user_data, tenant_id=tenant_id)
        return UserProfileResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Registration failed: {str(e)}", exc_info=True)
        # Do NOT expose internal error details in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Authenticate user and return JWT tokens.
    
    Validates user credentials and returns access and refresh tokens
    for authenticated sessions.
    
    Args:
        login_data: User login credentials
        db: Database session
        
    Returns:
        TokenResponse: JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(login_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    
    try:
        access_token = SecurityManager.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        refresh_token = SecurityManager.create_refresh_token(data=token_data)
    except Exception as token_err:
        logging.error(f"Token creation failed: {str(token_err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )
    
    # Persist refresh token in DB
    try:
        from app.core.security import SecurityManager as _SM
        expires_at = _SM.get_token_expiration(refresh_token)
        
        # CRITICAL: Check expiration is not None (prevents SQL constraint errors)
        if expires_at is None:
            logging.warning(f"Token expiration extraction failed for user {user.id}, skipping DB persistence")
        else:
            await auth_service.create_refresh_token_record(user.id, refresh_token, expires_at)
    except Exception as db_err:
        # If storing refresh token fails, log but don't block login (keep flow resilient)
        logging.warning(f"Failed to persist refresh token for user {user.id}: {str(db_err)}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Refresh access token using refresh token.
    
    Exchanges a valid refresh token for a new access token.
    
    Args:
        refresh_data: Refresh token request
        db: Database session
        
    Returns:
        Dict: New access token and expiration time
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    payload = await SecurityManager.verify_token(refresh_data.refresh_token, "refresh")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(int(user_id))
    # Verify refresh token persisted and valid
    stored_rt = await auth_service.verify_refresh_token(refresh_data.refresh_token)
    if not stored_rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    access_token = SecurityManager.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout user by blacklisting the access token.
    
    Adds the current access token to the blacklist to prevent
    further use until it naturally expires.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Dict: Logout confirmation message
    """
    token = credentials.credentials
    payload = await SecurityManager.verify_token(token, "access")
    
    # Get token expiration time
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        from datetime import datetime
        expires_at = datetime.fromtimestamp(exp_timestamp)
        await SecurityManager.blacklist_token(token, expires_at)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Returns the profile information of the currently authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserProfileResponse: User profile information
    """
    return UserProfileResponse.model_validate(current_user)


@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update current user's profile information.
    
    Allows users to update their name, phone, and address information.
    
    Args:
        profile_data: Profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserProfileResponse: Updated user profile information
    """
    auth_service = AuthService(db)
    updated_user = await auth_service.update_user_profile(current_user.id, profile_data)
    return UserProfileResponse.model_validate(updated_user)


@router.put("/me/password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Change current user's password.
    
    Validates the current password and updates to the new password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    auth_service = AuthService(db)
    await auth_service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}

@router.post("/google",response_model=TokenResponse)
async def google_login(
    data: GoogleLoginRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    login or register user using google oauth
    verifies the google id token server-side and then returns JWS tokens
    """
    
    # verift the token with google and get user info
    try:
        idinfo = google_id_token.verify_oauth2_token(
            data.id_token,
            google_requests.Request(),
            settings.google_client_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired google token",
        )
    
    google_sub = idinfo["sub"]
    email = idinfo["email"]
    name = idinfo.get("name", "")
    
    # find existinf user or create new one
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_email(email)
    
    if not user:
        user = User(
            email=email,
            password_hash="",   #no password since it's google auth       
            name=name or email.split("@")[0],
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,   #asume google already verified the email      
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    else:
        
        if not user.is_verified:
            user.is_verified = True
            await db.commit()
            
    # issue JWT tokens
    token_data = {"sub":str(user.id), "email": user.email, "role":user.role.value}
    access_token = SecurityManager.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=setting.access_token_expire_minutes)
    )
    refresh_access_token = SecurityManager.create_refresh_token(data=token_data)    
    
    try: 
        from app.core.security import SecurityManager as _SM
        expires_at = _SM.get_token_expireation(refresh_access_token)
        if expires_at:
            await auth_service.create_refresh_token_record(user.id,refresh_access_token, expires_at)
    except Exception:
        pass
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_access_token,
        expires_in=settings.access_token_expire_minutes * 60
    )       
                
    
    