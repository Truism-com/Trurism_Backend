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
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
# Use pbkdf2_sha256 as primary to avoid bcrypt versioning issues on Azure/Windows.
# Retain bcrypt for backward compatibility with existing hashes.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def _hash_token(token: str) -> str:
    """Produce a consistent SHA-256 fingerprint for a token."""
    return hashlib.sha256(token.encode()).hexdigest()


class SecurityManager:
    """
    Security manager for handling authentication and authorization.

    Provides password hashing, JWT token management, and role-based
    access control for the travel booking platform.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using the configured scheme."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its stored hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
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
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    @staticmethod
    async def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if await SecurityManager.is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except HTTPException:
            raise
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def blacklist_token(token: str, expires_at: datetime) -> None:
        """
        Add a token to the blacklist.

        Uses the shared Redis connection pool as primary storage.
        Falls back to database when Redis is unavailable.
        Token is always hashed before storage.
        """
        token_hash = _hash_token(token)

        from app.core.redis import get_redis_client
        client = get_redis_client()
        if client is not None:
            try:
                ttl = max(int((expires_at - datetime.utcnow()).total_seconds()), 1)
                await client.setex(f"blacklist:{token_hash}", ttl, "1")
                return
            except Exception as e:
                logger.warning(f"Redis blacklist failed, falling back to database: {e}")

        try:
            from app.auth.models import TokenBlacklist
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                blacklist_entry = TokenBlacklist(
                    token_jti=token_hash,
                    expires_at=expires_at,
                )
                session.add(blacklist_entry)
                await session.commit()
        except ImportError:
            logger.warning("TokenBlacklist model not available, token blacklist not persisted")
        except Exception as e:
            logger.error(f"Failed to blacklist token in database: {e}", exc_info=True)

    @staticmethod
    async def is_token_blacklisted(token: str) -> bool:
        """
        Check if a token is blacklisted.

        Uses shared Redis pool as primary, database as fallback.
        Fails open to prevent full auth lockout during infrastructure issues.
        """
        token_hash = _hash_token(token)

        try:
            from app.core.redis import get_redis_client
            client = get_redis_client()
            if client is not None:
                return await client.exists(f"blacklist:{token_hash}") > 0
        except Exception as e:
            logger.warning(f"Redis blacklist check failed: {e}")

        try:
            from app.auth.models import TokenBlacklist
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select

            async with AsyncSessionLocal() as session:
                stmt = select(TokenBlacklist).where(
                    TokenBlacklist.token_jti == token_hash,
                    TokenBlacklist.expires_at > datetime.utcnow(),
                )
                result = await session.execute(stmt)
                return result.scalars().first() is not None
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Database blacklist check failed, failing open: {e}")
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
