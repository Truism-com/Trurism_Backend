import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select
from app.admin.services import AdminAnalyticsService
from app.auth.models import User
from app.booking.models import FlightBooking

class MockModel:
    id = 1
    tenant_id = 2

@pytest.fixture
def db_session():
    return AsyncMock()

def test_scoped_count_with_tenant(db_session):
    service = AdminAnalyticsService(db=db_session, tenant_id=5)
    
    # We use User model which has a tenant_id
    query = service._scoped_count(User)
    
    query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant_id = 5" in query_str

def test_scoped_count_superadmin(db_session):
    # Superadmin has no tenant_id attached to the service instance
    service = AdminAnalyticsService(db=db_session, tenant_id=None)
    
    query = service._scoped_count(User)
    
    query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant_id =" not in query_str

def test_user_count_with_tenant(db_session):
    service = AdminAnalyticsService(db=db_session, tenant_id=5)
    
    query = service._user_count(User.is_active == True)
    
    query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant_id = 5" in query_str
    assert "is_active = true" in query_str.lower() or "is_active = 1" in query_str.lower()

def test_scoped_sum_with_tenant(db_session):
    service = AdminAnalyticsService(db=db_session, tenant_id=10)
    
    query = service._scoped_sum(FlightBooking, FlightBooking.total_amount)
    
    query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "tenant_id = 10" in query_str
