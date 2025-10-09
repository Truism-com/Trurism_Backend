# Getting Started Guide

This guide will help you set up the Travel Booking Platform development environment and get started with development.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

- **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 14+**: [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis 6+**: [Download Redis](https://redis.io/download)
- **Git**: [Download Git](https://git-scm.com/downloads)

### Optional Software

- **Docker**: [Download Docker](https://www.docker.com/get-started) (for containerized development)
- **VS Code**: [Download VS Code](https://code.visualstudio.com/) (recommended editor)
- **Postman**: [Download Postman](https://www.postman.com/downloads/) (for API testing)

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 2GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/travel-booking-platform.git
cd travel-booking-platform

# Verify the structure
ls -la
```

Expected directory structure:
```
travel-booking-platform/
├── app/
├── docs/
├── migrations/
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env.example
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv path)
which python
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your configuration
# Use your preferred editor (VS Code, vim, nano, etc.)
code .env  # or nano .env
```

#### Essential Environment Variables

Update these variables in your `.env` file:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/travel_booking

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Secret (CHANGE THIS!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# External API Configuration (for production)
XML_AGENCY_USERNAME=your_xml_agency_username
XML_AGENCY_PASSWORD=your_xml_agency_password
```

### 5. Database Setup

#### Option A: Local PostgreSQL

```bash
# Create PostgreSQL database
createdb travel_booking

# Or using psql
psql -U postgres
CREATE DATABASE travel_booking;
\q
```

#### Option B: Docker PostgreSQL

```bash
# Run PostgreSQL in Docker
docker run --name travel-postgres \
  -e POSTGRES_DB=travel_booking \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:14
```

### 6. Redis Setup

#### Option A: Local Redis

```bash
# Install and start Redis
# On macOS with Homebrew:
brew install redis
brew services start redis

# On Ubuntu:
sudo apt-get install redis-server
sudo systemctl start redis-server

# On Windows:
# Download and install Redis from https://github.com/microsoftarchive/redis/releases
```

#### Option B: Docker Redis

```bash
# Run Redis in Docker
docker run --name travel-redis \
  -p 6379:6379 \
  -d redis:6-alpine
```

### 7. Run Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Run migrations
alembic upgrade head

# Verify tables were created
psql -d travel_booking -c "\dt"
```

### 8. Start the Development Server

```bash
# Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 9. Verify Installation

Open your browser and visit:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Root**: http://localhost:8000/

You should see the API documentation and a healthy status response.

## 🧪 Testing Your Setup

### 1. Test API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "development"
}
```

#### User Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "name": "Test User",
    "role": "customer"
  }'
```

#### User Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### 3. Check Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy app/
```

## 🛠️ Development Workflow

### 1. Code Structure

```
app/
├── core/           # Shared utilities and configuration
├── auth/           # Authentication module
├── search/         # Search functionality
├── booking/        # Booking management
├── admin/          # Admin operations
└── main.py         # Main FastAPI application
```

### 2. Making Changes

#### Adding a New Endpoint

1. **Define Schema** (`schemas.py`):
```python
class NewRequestSchema(BaseModel):
    field1: str
    field2: int
```

2. **Implement Service** (`services.py`):
```python
class NewService:
    async def process_request(self, data: NewRequestSchema):
        # Business logic
        pass
```

3. **Add API Endpoint** (`api.py`):
```python
@router.post("/new-endpoint")
async def new_endpoint(
    request: NewRequestSchema,
    service: NewService = Depends(get_service)
):
    return await service.process_request(request)
```

#### Adding a New Model

1. **Define Model** (`models.py`):
```python
class NewModel(Base):
    __tablename__ = "new_table"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
```

2. **Create Migration**:
```bash
alembic revision --autogenerate -m "Add new model"
alembic upgrade head
```

### 3. Testing Changes

```bash
# Run specific test
pytest tests/test_new_feature.py

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Run linting
ruff check app/new_feature.py

# Run type checking
mypy app/new_feature.py
```

## 🔧 Development Tools

### 1. Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 2. VS Code Extensions

Recommended extensions for VS Code:

- **Python**: Microsoft Python extension
- **Pylance**: Fast Python language server
- **Ruff**: Fast Python linter
- **Thunder Client**: API testing
- **GitLens**: Enhanced Git capabilities

### 3. Database Tools

#### PostgreSQL GUI Tools

- **pgAdmin**: Web-based PostgreSQL administration
- **DBeaver**: Universal database tool
- **TablePlus**: Modern database management

#### Command Line Tools

```bash
# Connect to database
psql -d travel_booking -U username

# List tables
\dt

# Describe table
\d table_name

# Run SQL queries
SELECT * FROM users LIMIT 10;
```

### 4. Redis Tools

#### Redis CLI

```bash
# Connect to Redis
redis-cli

# List keys
KEYS *

# Get value
GET key_name

# Set value
SET key_name "value"
```

#### Redis GUI Tools

- **RedisInsight**: Official Redis GUI
- **Redis Commander**: Web-based Redis management

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check connection
psql -d travel_booking -U username
```

#### 2. Redis Connection Error

**Error**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
sudo systemctl start redis-server

# Or using Docker
docker start travel-redis
```

#### 3. Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

#### 4. Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Make sure you're in the project root
pwd

# Install in development mode
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 5. Migration Issues

**Error**: `alembic.util.exc.CommandError: Can't locate revision`

**Solution**:
```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Reset to base (CAUTION: This will delete data!)
alembic downgrade base
alembic upgrade head
```

### Debug Mode

Enable debug mode for detailed error information:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Logs

Check application logs for detailed error information:

```bash
# If running with uvicorn
uvicorn app.main:app --reload --log-level debug

# Check application logs
tail -f logs/app.log
```

## 📚 Next Steps

### 1. Explore the Codebase

- Read the [Architecture Documentation](../architecture/README.md)
- Review [Module Documentation](../modules/README.md)
- Check [API Documentation](../api/README.md)

### 2. Run the Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### 3. Try the API

- Use the interactive documentation at http://localhost:8000/docs
- Test endpoints with curl or Postman
- Create a test user and make a booking

### 4. Set Up Development Tools

- Install VS Code extensions
- Configure pre-commit hooks
- Set up database GUI tools

### 5. Start Contributing

- Read [Contributing Guidelines](contributing.md)
- Check [Code Standards](standards.md)
- Review [Testing Guide](testing.md)

## 🆘 Getting Help

### Resources

- **Documentation**: Check the `/docs` directory
- **API Docs**: Interactive documentation at `/docs` endpoint
- **GitHub Issues**: Report bugs and request features
- **Community**: Join our developer community

### Support Channels

- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Comprehensive guides and references
- **Code Examples**: Working examples in the repository
- **API Documentation**: Interactive endpoint documentation

---

Congratulations! You now have a fully functional development environment for the Travel Booking Platform. Happy coding! 🚀
