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
from pydantic import BaseSettings, validator


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
    
    # Database Settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/travel_booking"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis Settings
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Security Settings
    bcrypt_rounds: int = 12
    rate_limit_per_minute: int = 60
    
    # External API Settings
    xml_agency_base_url: str = "https://api.xmlagency.com"
    xml_agency_username: str = ""
    xml_agency_password: str = ""
    api_timeout_seconds: int = 30
    
    # Cache Settings
    search_cache_ttl: int = 900  # 15 minutes
    session_cache_ttl: int = 3600  # 1 hour
    
    # File Upload Settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".jpg", ".jpeg", ".png", ".pdf"]
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate that environment is one of the allowed values."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
