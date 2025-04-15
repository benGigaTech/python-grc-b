"""Unit tests for the User model."""

import pytest
from werkzeug.security import generate_password_hash
from cmmc_tracker.app.models.user import User

@pytest.mark.unit
@pytest.mark.models
def test_user_creation():
    """Test creating a User object."""
    user = User(
        id=1,
        username='test_user',
        password_hash=generate_password_hash('password'),
        is_admin=0,
        email='test@example.com'
    )

    assert user.id == 1
    assert user.username == 'test_user'
    assert user.email == 'test@example.com'
    assert user.is_admin == 0
    assert user.check_password('password')
    assert not user.check_password('wrong_password')

@pytest.mark.unit
@pytest.mark.models
def test_user_password_hashing():
    """Test password hashing functionality."""
    user = User(
        id=1,
        username='test_user',
        password_hash=generate_password_hash('password'),
        is_admin=0
    )

    # Test password verification
    assert user.check_password('password')
    assert not user.check_password('wrong_password')

    # Test direct password hash setting (without database update)
    user.password = generate_password_hash('new_password')
    assert user.check_password('new_password')
    assert not user.check_password('password')

@pytest.mark.unit
@pytest.mark.models
def test_user_is_admin():
    """Test is_admin property."""
    admin_user = User(
        id=1,
        username='admin',
        password_hash=generate_password_hash('password'),
        is_admin=1
    )

    regular_user = User(
        id=2,
        username='user',
        password_hash=generate_password_hash('password'),
        is_admin=0
    )

    assert admin_user.is_admin == 1
    assert regular_user.is_admin == 0
