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
    
    # CORS and Security Settings (comma-separated strings, parsed in main.py)
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    trusted_hosts: str = "localhost,127.0.0.1"

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str, info) -> str:
        """Reject wildcard CORS origins in production to prevent credential theft."""
        env = info.data.get("environment", "development")
        if env == "production" and v.strip() == "*":
            raise ValueError(
                "CORS wildcard origin '*' is not allowed in production. "
                "Set CORS_ORIGINS to explicit frontend domain(s) to prevent credential theft."
            )
        return v
    
    # Request Size Limits
    max_request_body_size: int = 10 * 1024 * 1024  # 10MB
    
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
        
        # Add SSL requirements only for remote/production databases (e.g., Render PostgreSQL)
        # Local databases typically don't require SSL
        # Note: asyncpg only supports 'ssl' parameter, not 'sslmode'
        if "postgresql+asyncpg://" in self.database_url:
            # Map sslmode=require to ssl=require for asyncpg
            if "sslmode=require" in self.database_url and "ssl=" not in self.database_url:
                separator = "&" if "?" in self.database_url else "?"
                self.database_url = f"{self.database_url}{separator}ssl=require"
            # Remove sslmode parameter entirely (asyncpg doesn't accept it)
            if "sslmode=" in self.database_url:
                self.database_url = self.database_url.replace("sslmode=require", "")
                # Clean up any leftover query artifacts
                self.database_url = self.database_url.replace("?&", "?").replace("&&", "&").rstrip("?&")
            
            if "ssl=" not in self.database_url:
                # Check if this is a remote database that requires SSL
                is_local = "localhost" in self.database_url or "127.0.0.1" in self.database_url
                is_production = self.environment in ["production", "staging"]
                is_remote_host = any(host in self.database_url for host in ["render.com", ".onrender.com", ".amazonaws.com", "cloud", "managed", ".supabase.co", ".azure.com", ".postgres.database.azure.com"])
                
                # Only add SSL for remote/production databases, not local development
                if (is_production or is_remote_host) and not is_local:
                    separator = "&" if "?" in self.database_url else "?"
                    # For asyncpg, use ssl=require for SSL connections
                    self.database_url = f"{self.database_url}{separator}ssl=require"
        
        return self
    
    # Redis Settings (Optional - set via environment variable)
    redis_url: Optional[str] = None
    redis_db: int = 0
    
    # JWT Settings
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 5  # Reduced from 15 to 5 minutes as compensating control for Redis-unavailable token blacklist
    refresh_token_expire_days: int = 7
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # Celery / Background worker settings (Optional - set via environment variable)
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Security Settings
    bcrypt_rounds: int = 12
    
    # External API Settings - XML.Agency (Flights)
    xml_agency_base_url: str = "https://api.xmlagency.com"
    xml_agency_username: str = ""
    xml_agency_password: str = ""
    xml_agency_timeout: int = 30
    
    # Flight API Settings (Generic)
    flight_api_url: str = ""
    flight_api_key: str = ""
    flight_api_secret: str = ""
    
    # Bus API Settings
    bus_api_url: str = ""
    bus_api_key: str = ""
    bus_api_secret: str = ""
    
    # Hotel API Settings
    hotel_api_url: str = ""
    hotel_api_key: str = ""
    hotel_api_secret: str = ""
    
    # Payment Gateway Settings - Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    
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
        """Ensure a JWT secret is provided in non-development environments."""
        import secrets
        env = info.data.get("environment", "development")
        if env in ("production", "staging") and (not v or v.strip() == ""):
            raise ValueError("JWT_SECRET_KEY must be set in production/staging environment")
        if not v or v.strip() == "":
            return secrets.token_hex(32)
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    # Note: cors_origins and trusted_hosts are parsed in main.py
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # ignore unrelated env vars like SUPABASE_URL
    }


# Global settings instance
settings = Settings()
