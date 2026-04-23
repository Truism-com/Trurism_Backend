# Travel Booking Platform

A comprehensive, modular travel booking platform built with FastAPI, featuring flight, hotel, and bus booking capabilities with a modern, scalable architecture.

## 🚀 Features

### Core Functionality
- **Flight Booking**: Search and book flights with multiple airlines
- **Hotel Booking**: Find and reserve accommodations with filtering
- **Bus Booking**: Inter-city bus ticket booking and management
- **User Management**: Customer and travel agent registration
- **Payment Processing**: Multiple payment methods integration
- **Booking Management**: Full booking lifecycle management

### Technical Features
- **Modular Architecture**: Clean separation of concerns with independent modules
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-Based Access Control**: Customer, Agent, and Admin roles
- **Real-time Search**: Cached search results with Redis
- **Background Processing**: Async task processing with Celery
- **Comprehensive API**: RESTful API with automatic documentation
- **Database Migrations**: Alembic for schema management
- **Testing Suite**: Comprehensive test coverage
- **Code Quality**: Linting, formatting, and type checking

## 🏗️ Architecture

The platform follows a modular architecture with the following modules:

```
app/
├── core/                    # Shared utilities and configuration
│   ├── config.py           # Environment configuration
│   ├── database.py         # Database setup and sessions
│   └── security.py         # JWT and security utilities
├── auth/                   # Authentication module
│   ├── models.py          # User models
│   ├── schemas.py         # Request/response schemas
│   ├── services.py        # Business logic
│   └── api.py             # API endpoints
├── search/                 # Search module
│   ├── schemas.py         # Search request/response schemas
│   ├── services.py        # Search business logic
│   └── api.py             # Search endpoints
├── booking/                # Booking module
│   ├── models.py          # Booking models
│   ├── schemas.py         # Booking schemas
│   ├── services.py        # Booking business logic
│   └── api.py             # Booking endpoints
├── admin/                  # Admin module
│   ├── schemas.py         # Admin schemas
│   ├── services.py        # Admin business logic
│   └── api.py             # Admin endpoints
└── main.py                # Main FastAPI application
```

## 🛠️ Technology Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.0**: Async ORM for database operations
- **PostgreSQL**: Primary database with async support
- **Redis**: Caching and session management
- **Celery**: Background task processing

### Security & Authentication
- **JWT**: Token-based authentication with refresh tokens
- **Bcrypt**: Password hashing
- **Pydantic**: Data validation and serialization
- **Rate Limiting**: API rate limiting with slowapi

### Development Tools
- **Pytest**: Testing framework with async support
- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking
- **Alembic**: Database migrations
- **Pre-commit**: Git hooks for code quality

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/travel-booking-platform.git
cd travel-booking-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Update the `.env` file with your configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/travel_booking

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
ACCESS_TOKEN_EXPIRE_MINUTES=120

# External APIs
XML_AGENCY_USERNAME=your_username
XML_AGENCY_PASSWORD=your_password
```

### 5. Database Setup

Create the database:

```bash
# Create PostgreSQL database
createdb travel_booking
```

Run migrations:

```bash
alembic upgrade head
```

### 6. Start the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Documentation

### Authentication Endpoints

```http
POST /auth/register          # User registration
POST /auth/login             # User login
POST /auth/refresh           # Refresh token
POST /auth/logout            # User logout
GET  /auth/me                # Get current user
PUT  /auth/me                # Update profile
PUT  /auth/me/password       # Change password
```

### Search Endpoints

```http
GET  /search/flights         # Search flights
POST /search/flights         # Search flights (POST)
GET  /search/hotels          # Search hotels
POST /search/hotels          # Search hotels (POST)
GET  /search/buses           # Search buses
POST /search/buses           # Search buses (POST)
```

### Booking Endpoints

```http
POST /bookings/flights       # Create flight booking
POST /bookings/hotels        # Create hotel booking
POST /bookings/buses         # Create bus booking
GET  /bookings               # List user bookings
GET  /bookings/{id}          # Get booking details
PUT  /bookings/{id}/cancel   # Cancel booking
```

### Admin Endpoints

```http
GET  /admin/dashboard/stats  # Dashboard statistics
GET  /admin/users            # List all users
PUT  /admin/agents/{id}/approve  # Approve agent
GET  /admin/bookings         # List all bookings
PUT  /admin/bookings/{id}/status  # Update booking status
```

## 🚢 Deploying to Render

This project can be deployed to Render using Docker. A `Dockerfile` and a `render.yaml` manifest are included to help you get started.

Quick steps:

1. Push this repository to a Git provider (GitHub/GitLab).
2. Sign in to Render and create a new service by connecting your repository. Render will read `render.yaml` if you use the "Use a render.yaml" option.
3. Ensure the service environment has these environment variables set (use Render's Dashboard -> Environment):

	- DATABASE_URL (e.g. postgresql+asyncpg://user:pass@host:5432/travel_booking_prod?sslmode=require)
	- REDIS_URL (e.g. redis://:<password>@<host>:6379)
	- JWT_SECRET_KEY (strong secret)
	- DEBUG=false
	- CELERY_BROKER_URL (if you run Celery)
	- CELERY_RESULT_BACKEND (if you run Celery)

4. Provision a managed Postgres database in Render (or provide an external one) and set `DATABASE_URL` accordingly. Provision Redis separately and set `REDIS_URL`.
5. On the Render instance (or via a deployment shell), run database migrations:

```bash
alembic upgrade head
```

6. The web service runs Uvicorn inside the Docker container and listens on the `$PORT` provided by Render.

Notes:
- The included `Dockerfile` installs system libraries required by `lxml` and `asyncpg`. If you add packages that require additional system libraries, update the Dockerfile.
- An optional worker service is included in `render.yaml` for Celery; enable it after you configure Celery (the repo expects `app.celery` to exist for Celery configuration).
- Use Render's encrypted environment variables to keep secrets safe.


## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## 🔧 Development

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy app/

# Install pre-commit hooks
pre-commit install
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Background Tasks

Start Celery worker:

```bash
celery -A app.celery worker --loglevel=info
```

Start Celery beat (for scheduled tasks):

```bash
celery -A app.celery beat --loglevel=info
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t travel-booking-platform .

# Run container
docker run -p 8000:8000 travel-booking-platform
```

### Production Environment

1. Set `DEBUG=false` in environment variables
2. Use production database and Redis instances
3. Configure proper CORS origins
4. Set up SSL/TLS certificates
5. Configure reverse proxy (nginx)
6. Set up monitoring and logging

## 📊 Monitoring

The platform includes comprehensive monitoring:

- **Health Checks**: `/health` endpoint for monitoring
- **Metrics**: Prometheus metrics integration
- **Logging**: Structured logging with configurable levels
- **Error Tracking**: Comprehensive error handling and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use type hints
- Follow the modular architecture

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in the GitHub repository
- Check the API documentation at `/docs`
- Review the code examples in the tests

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core booking functionality
- ✅ User authentication and management
- ✅ Basic search capabilities
- ✅ Admin dashboard

### Phase 2 (Planned)
- 🔄 Payment gateway integration
- 🔄 Email/SMS notifications
- 🔄 Advanced search filters
- 🔄 Mobile app API

### Phase 3 (Future)
- 📋 AI-powered recommendations
- 📋 Multi-language support
- 📋 Advanced analytics
- 📋 Third-party integrations

---

**Built with ❤️ using FastAPI and modern Python practices**
