"""
Security Utilities Module

This module provides security-related functionality including:
- JWT token generation and validation
- Password hashing and verification
- Role-based access control
- Token blacklisting for logout functionality
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
import redis
import json
import hashlib

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Async Redis client for token blacklisting
if settings.redis_url and settings.redis_url.lower() != "none":
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
else:
    redis_client = None


class SecurityManager:
    """
    Security manager for handling authentication and authorization.
    
    This class provides methods for password hashing, JWT token management,
    and role-based access control for the travel booking platform.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password (str): Plain text password to hash
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password (str): Plain text password
            hashed_password (str): Hashed password to verify against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data (Dict[str, Any]): Data to encode in the token
            expires_delta (Optional[timedelta]): Token expiration time
            
        Returns:
            str: JWT access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data (Dict[str, Any]): Data to encode in the token
            
        Returns:
            str: JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    async def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token (str): JWT token to verify
            token_type (str): Expected token type ("access" or "refresh")
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Use PyJWT to decode token; this will raise PyJWTError on failure
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check if token is blacklisted
            if await SecurityManager.is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def blacklist_token(token: str, expires_at: datetime) -> None:
        """
        Add a token to the blacklist.
        
        Args:
            token (str): Token to blacklist
            expires_at (datetime): When the token would naturally expire
        """
        # Store token in Redis with expiration (ttl in seconds)
        try:
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl <= 0:
                ttl = 1
        except Exception:
            ttl = None

        key = f"blacklist:{token}"
        if redis_client is None:
            # Redis not configured, skip blacklisting
            return
        if ttl:
            redis_client.setex(key, ttl, "true")
        else:
            # fallback: set without expiry
            redis_client.set(key, "true")
    
    @staticmethod
    async def is_token_blacklisted(token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token (str): Token to check
            
        Returns:
            bool: True if token is blacklisted, False otherwise
        """
        try:
            if redis_client is None:
                # Redis not configured, fail open (do not block valid tokens)
                return False
            return redis_client.exists(f"blacklist:{token}") > 0
        except Exception:
            # If Redis is unavailable, fail open (do not block valid tokens)
            return False
    
    @staticmethod
    def get_token_expiration(token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token.
        
        Args:
            token (str): JWT token
            
        Returns:
            Optional[datetime]: Token expiration time, None if invalid
        """
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
        except jwt.PyJWTError:
            pass
        return None
