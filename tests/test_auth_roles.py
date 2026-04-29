import pytest
from pydantic import ValidationError
from app.auth.schemas import UserRegisterRequest
from app.auth.models import User, UserRole

def test_admin_registration_rejected():
    data = {
        "email": "test@admin.com",
        "password": "strongpassword123",
        "first_name": "Test",
        "last_name": "Admin",
        "role": UserRole.ADMIN
    }
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**data)
    
    assert "Cannot register as admin or superadmin" in str(exc_info.value)

def test_superadmin_registration_rejected():
    data = {
        "email": "test@superadmin.com",
        "password": "strongpassword123",
        "first_name": "Test",
        "last_name": "SuperAdmin",
        "role": UserRole.SUPERADMIN
    }
    with pytest.raises(ValidationError) as exc_info:
        UserRegisterRequest(**data)
    
    assert "Cannot register as admin or superadmin" in str(exc_info.value)

def test_customer_registration_allowed():
    data = {
        "email": "test@customer.com",
        "password": "strongpassword123",
        "first_name": "Test",
        "last_name": "Customer",
        "role": UserRole.CUSTOMER
    }
    req = UserRegisterRequest(**data)
    assert req.role == UserRole.CUSTOMER

def test_user_is_admin_property():
    admin_user = User(role=UserRole.ADMIN)
    superadmin_user = User(role=UserRole.SUPERADMIN)
    customer_user = User(role=UserRole.CUSTOMER)
    
    # Both ADMIN and SUPERADMIN should be considered admins for backward compatibility
    assert admin_user.is_admin is True
    assert superadmin_user.is_admin is True
    assert customer_user.is_admin is False

def test_user_is_superadmin_property():
    admin_user = User(role=UserRole.ADMIN)
    superadmin_user = User(role=UserRole.SUPERADMIN)
    
    # Only SUPERADMIN is superadmin
    assert admin_user.is_superadmin is False
    assert superadmin_user.is_superadmin is True
