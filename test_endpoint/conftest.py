import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import get_database_session


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    from app.core.database import Base          # import your declarative Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    """Each test gets a fresh transaction that is rolled back after."""
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await conn.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    """HTTP client with DB overridden to the test session."""
    async def override_db():
        yield db_session

    app.dependency_overrides[get_database_session] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def tenant_headers():
    """Pass a tenant ID header — required by TenantMiddleware on non-auth routes."""
    return {"X-Tenant-ID": "1"}

def no_tenant_headers():
    return {}  

@pytest_asyncio.fixture
async def auth_tokens(client):
    """Register + login a customer, return access/refresh tokens."""
    await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "Test1234!",
        "name": "Test User",
        "role": "customer",
    })
    resp = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!",
    })
    return resp.json()

@pytest.fixture
def auth_header(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}

@pytest.fixture(scope="session")
def event_loop():
    """Override event_loop to session scope to match the engine fixture."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()