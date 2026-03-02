"""
API Key API Endpoints

This module defines FastAPI endpoints for API key management:
- Create, list, update, and revoke API keys
- API key authentication dependency
- Usage statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_database_session
from app.auth.api import get_current_user, get_current_admin_user
from app.auth.models import User
from app.api_keys.models import APIKey
from app.api_keys.schemas import (
    APIKeyCreate, APIKeyResponse, APIKeyListResponse,
    APIKeyUpdate
)
from app.api_keys.services import APIKeyService

# Router for API key endpoints
router = APIRouter(prefix="/api-keys", tags=["API Keys"])


async def get_api_key_from_header(
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_database_session)
) -> APIKey:
    """
    Dependency to authenticate requests using API key.
    
    This dependency extracts the API key from the X-API-Key header
    and validates it.
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        APIKey: Validated API key object
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via X-API-Key header"
        )
    
    api_key_service = APIKeyService(db)
    api_key = await api_key_service.validate_api_key(x_api_key)
    
    # Check rate limit
    within_limit = await api_key_service.check_rate_limit(api_key)
    if not within_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {api_key.rate_limit} requests/minute"
        )
    
    return api_key


async def require_api_key_scope(
    required_scope: str,
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_database_session)
) -> APIKey:
    """
    Dependency to require specific API key scope.
    
    Args:
        required_scope: Required scope for the operation
        x_api_key: API key from header
        db: Database session
        
    Returns:
        APIKey: Validated API key with required scope
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via X-API-Key header"
        )
    
    api_key_service = APIKeyService(db)
    api_key = await api_key_service.validate_api_key(x_api_key, required_scope)
    
    # Check rate limit
    within_limit = await api_key_service.check_rate_limit(api_key)
    if not within_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {api_key.rate_limit} requests/minute"
        )
    
    return api_key


@router.post("/", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new API key.
    
    This endpoint creates a new API key for the authenticated user
    with specified scopes and rate limits.
    
    Args:
        key_data: API key creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyResponse: Created API key (with plain key shown once)
    """
    try:
        api_key_service = APIKeyService(db)
        api_key, plain_key = await api_key_service.create_api_key(
            current_user.id, key_data
        )
        
        response = APIKeyResponse.model_validate(api_key)
        response.key = plain_key  # Only shown once
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/", response_model=List[APIKeyListResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    List all API keys for the current user.
    
    This endpoint returns all API keys created by the authenticated user
    without exposing the actual key values.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[APIKeyListResponse]: List of API keys
    """
    try:
        api_key_service = APIKeyService(db)
        api_keys = await api_key_service.get_user_api_keys(current_user.id)
        
        return [APIKeyListResponse.model_validate(key) for key in api_keys]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )


@router.get("/{key_id}", response_model=APIKeyListResponse)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get details of a specific API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyListResponse: API key details
    """
    try:
        api_key_service = APIKeyService(db)
        api_key = await api_key_service.get_api_key_by_id(key_id, current_user.id)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return APIKeyListResponse.model_validate(api_key)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API key: {str(e)}"
        )


@router.put("/{key_id}", response_model=APIKeyListResponse)
async def update_api_key(
    key_id: int,
    update_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Update an API key.
    
    Args:
        key_id: API key ID
        update_data: Update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        APIKeyListResponse: Updated API key details
    """
    try:
        api_key_service = APIKeyService(db)
        api_key = await api_key_service.update_api_key(
            key_id, current_user.id, update_data
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return APIKeyListResponse.model_validate(api_key)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}"
        )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Revoke an API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Revocation confirmation
    """
    try:
        api_key_service = APIKeyService(db)
        success = await api_key_service.revoke_api_key(key_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return {"message": "API key revoked successfully", "key_id": key_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )
