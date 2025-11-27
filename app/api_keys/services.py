"""
API Key Services

This module contains business logic for API key management:
- API key generation and validation
- Redis caching for performance
- Usage tracking and rate limiting
- Scope verification
"""

import secrets
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
import redis.asyncio as redis
import json

from app.api_keys.models import APIKey, APIKeyScope
from app.api_keys.schemas import APIKeyCreate, APIKeyUpdate
from app.core.config import settings

# Async Redis client for API key caching
if settings.redis_url and settings.redis_url.lower() != "none":
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
else:
    redis_client = None


class APIKeyService:
    """
    API key service for managing partner API keys.
    
    This service handles API key creation, validation, caching,
    and usage tracking for the travel booking platform.
    """
    
    # Cache TTL for API keys (1 hour)
    CACHE_TTL = 3600
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = redis_client
    
    def _generate_api_key(self, environment: str = "production") -> tuple[str, str, str]:
        """
        Generate a new API key with prefix and hash.
        
        Args:
            environment: Environment type (production, staging, development)
            
        Returns:
            tuple: (plain_key, key_hash, key_prefix)
        """
        # Generate random 32-byte key
        random_key = secrets.token_urlsafe(32)
        
        # Create prefix based on environment
        if environment == "production":
            prefix = "tk_live_"
        elif environment == "staging":
            prefix = "tk_test_"
        else:
            prefix = "tk_dev_"
        
        # Create full key
        plain_key = f"{prefix}{random_key}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        return plain_key, key_hash, prefix
    
    async def create_api_key(
        self,
        user_id: int,
        key_data: APIKeyCreate
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID creating the API key
            key_data: API key creation data
            
        Returns:
            tuple: (APIKey object, plain API key)
        """
        # Generate API key
        plain_key, key_hash, key_prefix = self._generate_api_key(key_data.environment)
        
        # Calculate expiration
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
        
        # Create API key record
        api_key = APIKey(
            key=key_hash,
            key_prefix=key_prefix,
            name=key_data.name,
            user_id=user_id,
            scopes=[scope.value for scope in key_data.scopes],
            rate_limit=key_data.rate_limit,
            description=key_data.description,
            environment=key_data.environment,
            expires_at=expires_at
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        # Cache the key
        await self._cache_api_key(key_hash, api_key)
        
        return api_key, plain_key
    
    async def validate_api_key(
        self,
        plain_key: str,
        required_scope: Optional[str] = None
    ) -> Optional[APIKey]:
        """
        Validate an API key and check scope.
        
        Args:
            plain_key: Plain API key to validate
            required_scope: Required scope for the operation
            
        Returns:
            APIKey object if valid, None otherwise
            
        Raises:
            HTTPException: If key is invalid or lacks required scope
        """
        # Hash the key
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        # Try to get from cache first
        cached_key = await self._get_cached_api_key(key_hash)
        if cached_key:
            api_key = cached_key
        else:
            # Get from database
            result = await self.db.execute(
                select(APIKey).where(APIKey.key == key_hash)
            )
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            
            # Cache for future requests
            await self._cache_api_key(key_hash, api_key)
        
        # Validate key status
        if not api_key.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is expired or revoked"
            )
        
        # Check scope if required
        if required_scope and not api_key.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key lacks required scope: {required_scope}"
            )
        
        # Track usage
        await self._track_usage(api_key.id, key_hash)
        
        return api_key
    
    async def _cache_api_key(self, key_hash: str, api_key: APIKey) -> None:
        """Cache API key in Redis."""
        cache_key = f"api_key:{key_hash}"
        cache_data = {
            "id": api_key.id,
            "user_id": api_key.user_id,
            "scopes": api_key.scopes,
            "is_active": api_key.is_active,
            "rate_limit": api_key.rate_limit,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "revoked_at": api_key.revoked_at.isoformat() if api_key.revoked_at else None
        }
        await self.redis.setex(cache_key, self.CACHE_TTL, json.dumps(cache_data))
    
    async def _get_cached_api_key(self, key_hash: str) -> Optional[APIKey]:
        """Get API key from cache."""
        cache_key = f"api_key:{key_hash}"
        cached_data = await self.redis.get(cache_key)
        
        if not cached_data:
            return None
        
        data = json.loads(cached_data)
        
        # Reconstruct APIKey object
        api_key = APIKey(
            id=data["id"],
            key=key_hash,
            user_id=data["user_id"],
            scopes=data["scopes"],
            is_active=data["is_active"],
            rate_limit=data["rate_limit"],
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            revoked_at=datetime.fromisoformat(data["revoked_at"]) if data["revoked_at"] else None
        )
        
        return api_key
    
    async def _track_usage(self, key_id: int, key_hash: str) -> None:
        """Track API key usage."""
        # Update database usage count and last_used_at
        await self.db.execute(
            update(APIKey)
            .where(APIKey.id == key_id)
            .values(
                usage_count=APIKey.usage_count + 1,
                last_used_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Track in Redis for rate limiting
        rate_limit_key = f"api_key_rate:{key_hash}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        await self.redis.incr(rate_limit_key)
        await self.redis.expire(rate_limit_key, 120)  # Keep for 2 minutes
    
    async def check_rate_limit(self, api_key: APIKey) -> bool:
        """
        Check if API key has exceeded rate limit.
        
        Args:
            api_key: API key to check
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        key_hash = api_key.key
        current_minute = datetime.utcnow().strftime('%Y%m%d%H%M')
        rate_limit_key = f"api_key_rate:{key_hash}:{current_minute}"
        
        count = await self.redis.get(rate_limit_key)
        if count and int(count) >= api_key.rate_limit:
            return False
        
        return True
    
    async def get_user_api_keys(self, user_id: int) -> List[APIKey]:
        """Get all API keys for a user."""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_api_key_by_id(self, key_id: int, user_id: int) -> Optional[APIKey]:
        """Get a specific API key by ID for a user."""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.id == key_id, APIKey.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_api_key(
        self,
        key_id: int,
        user_id: int,
        update_data: APIKeyUpdate
    ) -> Optional[APIKey]:
        """Update an API key."""
        api_key = await self.get_api_key_by_id(key_id, user_id)
        
        if not api_key:
            return None
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        if "scopes" in update_dict:
            update_dict["scopes"] = [scope.value for scope in update_dict["scopes"]]
        
        for field, value in update_dict.items():
            setattr(api_key, field, value)
        
        await self.db.commit()
        await self.db.refresh(api_key)
        
        # Invalidate cache
        await self.redis.delete(f"api_key:{api_key.key}")
        
        return api_key
    
    async def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """Revoke an API key."""
        api_key = await self.get_api_key_by_id(key_id, user_id)
        
        if not api_key:
            return False
        
        api_key.revoked_at = datetime.utcnow()
        api_key.is_active = False
        
        await self.db.commit()
        
        # Invalidate cache
        await self.redis.delete(f"api_key:{api_key.key}")
        
        return True
