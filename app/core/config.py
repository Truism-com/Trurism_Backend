"""
Configuration Management Module

This module handles all application configuration including:
- Environment-based settings (development, staging, production)
- Database connection parameters
- JWT and security settings
- External API configurations
- Cache and Redis settings
"""

from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class manages all configuration for the travel booking platform
    including database, security, caching, and external API settings.
    """
    
    # Application Settings
    app_name: str = "Travel Booking Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # CORS and Security Settings
    cors_origins: list = ["*"]  # Comma-separated list or "*" for all
    trusted_hosts: list = ["*"]  # Comma-separated list or "*" for all
    
    # Database Settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/travel_booking"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    @model_validator(mode="after")
    def post_init_processing(self):
        """Process configuration after initialization."""
        # Convert Render's postgresql:// URL to postgresql+asyncpg:// for asyncpg
        if self.database_url.startswith("postgresql://") and not self.database_url.startswith("postgresql+asyncpg://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Add SSL requirements for Render PostgreSQL if not already present
        # Render managed PostgreSQL requires SSL connections
        # Note: asyncpg only supports 'ssl' parameter, not 'sslmode'
        if "postgresql+asyncpg://" in self.database_url and "ssl=" not in self.database_url:
            # Check if URL already has query parameters
            separator = "&" if "?" in self.database_url else "?"
            # For asyncpg, use ssl=require for SSL connections
            self.database_url = f"{self.database_url}{separator}ssl=require"
        
        # Parse CORS origins if provided as comma-separated string
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",")] if self.cors_origins != "*" else ["*"]
        
        # Parse trusted hosts if provided as comma-separated string
        if isinstance(self.trusted_hosts, str):
            self.trusted_hosts = [host.strip() for host in self.trusted_hosts.split(",")] if self.trusted_hosts != "*" else ["*"]
        
        return self
    
    # Redis Settings
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # JWT Settings
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Celery / Background worker settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Security Settings
    bcrypt_rounds: int = 12
    rate_limit_per_minute: int = 60
    
    # External API Settings - XML.Agency
    xml_agency_base_url: str = "https://api.xmlagency.com"
    xml_agency_username: str = ""
    xml_agency_password: str = ""
    xml_agency_timeout: int = 30
    
    # Payment Gateway Settings - Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    
    # Email Settings
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_from: str = ""
    mail_password: str = ""
    
    # Cache Settings
    search_cache_ttl: int = 900  # 15 minutes
    session_cache_ttl: int = 3600  # 1 hour
    
    # File Upload Settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".jpg", ".jpeg", ".png", ".pdf"]
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate that environment is one of the allowed values."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Ensure a JWT secret is provided in non-development environments.

        This avoids accidental use of hard-coded secrets in production.
        """
        # Access other fields through info.data
        env = info.data.get("environment", "development")
        if env == "production" and (not v or v.strip() == ""):
            raise ValueError("JWT_SECRET_KEY must be set in production environment")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
