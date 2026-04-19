"""
Security Utilities Module

This module provides security-related functionality including:
- JWT token generation and validation
- Password hashing and verification
- Role-based access control
- Token blacklisting for logout functionality (Redis + Database fallback)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
import redis.asyncio as aioredis
import json
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
# Use pbkdf2_sha256 as primary to avoid bcrypt versioning issues on Azure/Windows.
# Retain bcrypt for backward compatibility with existing hashes.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


async def _get_redis_client():
    """Get an async Redis client for token blacklisting."""
    if not settings.redis_url or settings.redis_url.lower() == "none":
        return None
    return aioredis.from_url(settings.redis_url, decode_responses=True)


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

        except HTTPException:
            # Re-raise HTTPExceptions (our custom errors)
            raise
        except jwt.ExpiredSignatureError:
            # Specific handling for expired tokens
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError as jwt_err:
            # Specific handling for JWT errors
            import logging
            logging.debug(f"JWT validation error: {str(jwt_err)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            # Catch any other unforeseen errors
            import logging
            logging.error(f"Unexpected error during token verification: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def blacklist_token(token: str, expires_at: datetime) -> None:
        """
        Add a token to the blacklist (Redis primary, database fallback).

        Args:
            token (str): Token to blacklist
            expires_at (datetime): When the token would naturally expire
        """
        # Try Redis first
        client = await _get_redis_client()
        if client is not None:
            try:
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
                if ttl <= 0:
                    ttl = 1

                key = f"blacklist:{token}"
                if ttl:
                    await client.setex(key, ttl, "true")
                else:
                    await client.set(key, "true")
                return
            except Exception as e:
                logger.warning(f"Redis blacklist failed, falling back to database: {e}")
            finally:
                await client.aclose()

        # Database fallback when Redis unavailable
        try:
            from app.auth.models import TokenBlacklist
            from app.core.database import async_session

            async with async_session() as session:
                # Hash the token for security before storing
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                blacklist_entry = TokenBlacklist(
                    token_jti=token_hash,
                    expires_at=expires_at
                )
                session.add(blacklist_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to blacklist token in database: {e}", exc_info=True)

    @staticmethod
    async def is_token_blacklisted(token: str) -> bool:
        """
        Check if a token is blacklisted (Redis primary, database fallback).

        Returns:
            bool: True if token is blacklisted, False otherwise
        """
        # Try Redis first
        try:
            client = await _get_redis_client()
            if client is not None:
                try:
                    result = await client.exists(f"blacklist:{token}")
                    return result > 0
                finally:
                    await client.aclose()
        except Exception as e:
            logger.warning(f"Redis blacklist check failed: {e}")

        # Database fallback when Redis unavailable
        try:
            from app.auth.models import TokenBlacklist
            from app.core.database import async_session
            from sqlalchemy import select

            token_hash = hashlib.sha256(token.encode()).hexdigest()

            async with async_session() as session:
                stmt = select(TokenBlacklist).where(
                    TokenBlacklist.token_jti == token_hash,
                    TokenBlacklist.expires_at > datetime.utcnow()  # Not expired
                )
                result = await session.execute(stmt)
                return result.scalars().first() is not None
        except Exception as e:
            logger.warning(f"Database blacklist check failed, failing secure (rejecting token): {e}")
            # Fail secure: if we can't check the blacklist, reject the token to prevent reuse of stolen tokens
            return True
    
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
