# Core Module Documentation

The Core module serves as the foundation of the Travel Booking Platform, providing shared utilities, configuration management, database connectivity, and security infrastructure that all other modules depend on.

## 🎯 Purpose

The Core module provides:
- **Configuration Management**: Environment-based settings and validation
- **Database Infrastructure**: Connection pooling, session management, and migrations
- **Security Utilities**: JWT handling, password hashing, and validation
- **Common Schemas**: Shared data models and utilities
- **Infrastructure Services**: Logging, caching, and monitoring

## 🏗️ Architecture

### Module Structure

```
app/core/
├── __init__.py          # Module initialization and exports
├── config.py           # Configuration management
├── database.py         # Database setup and session management
├── security.py         # Security utilities and JWT handling
├── middleware.py       # Custom middleware (if needed)
├── exceptions.py       # Custom exception classes
└── utils.py           # Common utility functions
```

### Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    Core Module Dependencies                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    External Dependencies                    ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ││
│  │  │ FastAPI     │  │ SQLAlchemy  │  │    Redis    │        ││
│  │  │ Pydantic    │  │   AsyncPG   │  │   Celery    │        ││
│  │  │ Python-Jose │  │   Alembic   │  │   Bcrypt    │        ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Core Components                         ││
│  │                                                             ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ││
│  │  │Configuration│  │  Database   │  │  Security   │        ││
│  │  │             │  │             │  │             │        ││
│  │  │ • Settings  │  │ • Sessions  │  │ • JWT       │        ││
│  │  │ • Validation│  │ • Pooling   │  │ • Hashing   │        ││
│  │  │ • Environment│  │ • Migrations│  │ • Validation│        ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Components

### 1. Configuration Management (`config.py`)

#### Purpose
Centralized configuration management with environment-based settings, validation, and type safety.

#### Key Features
- **Environment Variables**: Automatic loading from `.env` files
- **Type Validation**: Pydantic-based configuration validation
- **Default Values**: Sensible defaults for development
- **Security**: Sensitive data handling and validation

#### Configuration Categories

```python
class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Travel Booking Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database Settings
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Security Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # External API Settings
    xml_agency_base_url: str
    xml_agency_username: str
    xml_agency_password: str
    
    # Cache Settings
    redis_url: str
    search_cache_ttl: int = 900
    session_cache_ttl: int = 3600
```

#### Usage Example

```python
from app.core.config import settings

# Access configuration
database_url = settings.database_url
jwt_secret = settings.jwt_secret_key

# Environment-specific behavior
if settings.debug:
    # Development-specific code
    pass
```

### 2. Database Infrastructure (`database.py`)

#### Purpose
Database connection management, session handling, and migration support.

#### Key Features
- **Async Support**: Full async/await database operations
- **Connection Pooling**: Efficient connection management
- **Session Management**: Dependency injection for database sessions
- **Health Checks**: Database connectivity monitoring
- **Migration Support**: Alembic integration

#### Database Setup

```python
# Database engine configuration
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for all models
class Base(DeclarativeBase):
    pass
```

#### Session Management

```python
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logging.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
```

#### Usage Example

```python
from app.core.database import get_database_session

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_database_session)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### 3. Security Utilities (`security.py`)

#### Purpose
JWT token management, password hashing, and security-related utilities.

#### Key Features
- **JWT Handling**: Token generation, validation, and refresh
- **Password Security**: Bcrypt hashing and verification
- **Token Blacklisting**: Secure logout functionality
- **Role-Based Access**: Permission checking utilities

#### Security Manager Class

```python
class SecurityManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        # Implementation details...
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        # Implementation details...
```

#### Usage Example

```python
from app.core.security import SecurityManager

# Hash password during registration
hashed_password = SecurityManager.hash_password("user_password")

# Verify password during login
is_valid = SecurityManager.verify_password("user_password", hashed_password)

# Create JWT token
token = SecurityManager.create_access_token({"sub": str(user_id)})

# Verify token
payload = SecurityManager.verify_token(token)
```

## 🔧 Configuration Guide

### Environment Variables

#### Required Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/travel_booking

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# External APIs
XML_AGENCY_USERNAME=your_username
XML_AGENCY_PASSWORD=your_password
```

#### Optional Variables

```bash
# Application
APP_NAME="Travel Booking Platform"
APP_VERSION="1.0.0"
DEBUG=true
ENVIRONMENT=development

# Database Pool
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# JWT Expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cache TTL
SEARCH_CACHE_TTL=900
SESSION_CACHE_TTL=3600
```

### Configuration Validation

The Core module includes comprehensive configuration validation:

```python
@validator("environment")
def validate_environment(cls, v):
    """Validate that environment is one of the allowed values."""
    allowed_envs = ["development", "staging", "production"]
    if v not in allowed_envs:
        raise ValueError(f"Environment must be one of {allowed_envs}")
    return v
```

## 🔒 Security Implementation

### JWT Token Management

#### Token Types
- **Access Token**: Short-lived (15 minutes) for API access
- **Refresh Token**: Long-lived (7 days) for token renewal

#### Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "customer",
  "exp": 1234567890,
  "type": "access"
}
```

#### Security Features
- **Token Blacklisting**: Secure logout by blacklisting tokens
- **Expiration Handling**: Automatic token expiration
- **Refresh Mechanism**: Seamless token renewal
- **Role-Based Claims**: User roles in token payload

### Password Security

#### Hashing Algorithm
- **Algorithm**: Bcrypt with configurable rounds
- **Salt**: Automatic salt generation
- **Rounds**: Configurable complexity (default: 12)

#### Security Best Practices
- **Strong Passwords**: Validation requirements
- **Secure Storage**: Hashed passwords only
- **Verification**: Constant-time comparison
- **Reset Mechanism**: Secure password reset flow

## 📊 Database Management

### Connection Pooling

#### Pool Configuration
```python
engine = create_async_engine(
    database_url,
    pool_size=10,          # Base pool size
    max_overflow=20,       # Additional connections
    pool_timeout=30,       # Connection timeout
    pool_recycle=3600,     # Connection recycle time
    pool_pre_ping=True     # Connection validation
)
```

#### Performance Optimization
- **Connection Reuse**: Efficient connection management
- **Pool Monitoring**: Connection pool health tracking
- **Automatic Cleanup**: Idle connection cleanup
- **Error Handling**: Graceful connection failure handling

### Migration Management

#### Alembic Integration
```python
# Migration environment setup
from app.core.database import Base
from app.auth.models import User
from app.booking.models import FlightBooking, HotelBooking, BusBooking

# Create all tables
await conn.run_sync(Base.metadata.create_all)
```

#### Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🚀 Performance Considerations

### Database Optimization

#### Connection Management
- **Pool Sizing**: Optimal pool size configuration
- **Connection Reuse**: Minimize connection overhead
- **Query Optimization**: Efficient query patterns
- **Indexing Strategy**: Proper database indexing

#### Caching Strategy
- **Session Caching**: Database session reuse
- **Query Caching**: Result caching where appropriate
- **Connection Caching**: Persistent connections
- **Metadata Caching**: Schema metadata caching

### Security Performance

#### Token Operations
- **Fast Validation**: Optimized token verification
- **Efficient Blacklisting**: Redis-based token blacklisting
- **Minimal Payload**: Small token size
- **Batch Operations**: Efficient bulk operations

#### Password Operations
- **Async Hashing**: Non-blocking password operations
- **Configurable Rounds**: Balance security vs performance
- **Memory Management**: Efficient memory usage
- **Cache Optimization**: Strategic caching

## 🧪 Testing

### Unit Tests

#### Configuration Tests
```python
def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValidationError):
        Settings(environment="invalid")
```

#### Security Tests
```python
def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password"
    hashed = SecurityManager.hash_password(password)
    assert SecurityManager.verify_password(password, hashed)
    assert not SecurityManager.verify_password("wrong", hashed)
```

#### Database Tests
```python
async def test_database_session():
    """Test database session management."""
    async for session in get_database_session():
        assert isinstance(session, AsyncSession)
        break
```

### Integration Tests

#### Database Integration
```python
async def test_database_connection():
    """Test database connectivity."""
    assert await check_database_health()
```

#### Security Integration
```python
async def test_jwt_token_flow():
    """Test complete JWT token flow."""
    # Test token creation, validation, and blacklisting
    pass
```

## 🔧 Troubleshooting

### Common Issues

#### Configuration Issues
- **Missing Environment Variables**: Check `.env` file
- **Invalid Configuration**: Verify configuration validation
- **Environment Mismatch**: Ensure correct environment settings

#### Database Issues
- **Connection Failures**: Check database connectivity
- **Pool Exhaustion**: Adjust pool size configuration
- **Migration Errors**: Verify migration scripts

#### Security Issues
- **Token Validation Failures**: Check JWT secret and algorithm
- **Password Verification Issues**: Verify hashing configuration
- **Blacklist Problems**: Check Redis connectivity

### Debug Configuration

#### Development Mode
```python
# Enable debug mode
DEBUG=true

# Verbose logging
LOG_LEVEL=DEBUG

# Database query logging
SQLALCHEMY_ECHO=true
```

#### Production Monitoring
```python
# Health check endpoint
GET /health

# Database health
GET /health/database

# Redis health
GET /health/redis
```

## 📚 API Reference

### Configuration API

#### Settings Access
```python
from app.core.config import settings

# Access any configuration value
database_url = settings.database_url
jwt_secret = settings.jwt_secret_key
```

### Database API

#### Session Dependency
```python
from app.core.database import get_database_session

@router.get("/endpoint")
async def endpoint(db: AsyncSession = Depends(get_database_session)):
    # Use db session
    pass
```

#### Health Check
```python
from app.core.database import check_database_health

# Check database health
is_healthy = await check_database_health()
```

### Security API

#### Password Operations
```python
from app.core.security import SecurityManager

# Hash password
hashed = SecurityManager.hash_password(password)

# Verify password
is_valid = SecurityManager.verify_password(password, hashed)
```

#### Token Operations
```python
from app.core.security import SecurityManager

# Create token
token = SecurityManager.create_access_token(data)

# Verify token
payload = SecurityManager.verify_token(token)

# Blacklist token
SecurityManager.blacklist_token(token, expires_at)
```

---

The Core module provides the essential infrastructure for the Travel Booking Platform, ensuring consistent configuration management, secure database operations, and robust security utilities across all modules.
