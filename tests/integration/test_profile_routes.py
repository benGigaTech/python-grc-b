"""Integration tests for user profile routes."""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.profile
def test_view_profile(client, app, init_database):
    """Test that the profile page loads correctly."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('profile_test_user', generate_password_hash('test_password'), 0, 'profile_test@example.com'),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'profile_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the profile page
    response = client.get('/profile')
    
    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'User Profile' in response.data
    assert b'profile_test_user' in response.data
    assert b'profile_test@example.com' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.profile
def test_change_password(client, app, init_database):
    """Test changing password through the profile page."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('password_test_user', generate_password_hash('old_password'), 0, 'password_test@example.com'),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'password_test_user', 'password': 'old_password'},
        follow_redirects=True
    )
    
    # Change password
    response = client.post(
        '/profile/change_password',
        data={
            'current_password': 'old_password',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        },
        follow_redirects=True
    )
    
    # Check that the password was changed successfully
    assert response.status_code == 200
    assert b'Password changed successfully' in response.data
    
    # Verify in the database
    with app.app_context():
        user = execute_query(
            "SELECT password FROM users WHERE username = %s",
            ('password_test_user',),
            fetch_one=True
        )
        assert check_password_hash(user['password'], 'NewPassword123!')
        assert not check_password_hash(user['password'], 'old_password')
    
    # Logout
    client.get('/logout', follow_redirects=True)
    
    # Try to login with the new password
    response = client.post(
        '/login',
        data={'username': 'password_test_user', 'password': 'NewPassword123!'},
        follow_redirects=True
    )
    
    # Should be able to login with the new password
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.profile
def test_change_password_validation(client, app, init_database):
    """Test password validation when changing password."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('password_test_user', generate_password_hash('test_password'), 0, 'password_test@example.com'),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'password_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Test with incorrect current password
    response = client.post(
        '/profile/change_password',
        data={
            'current_password': 'wrong_password',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        },
        follow_redirects=True
    )
    
    # Should show an error message
    assert response.status_code == 200
    assert b'Current password is incorrect' in response.data
    
    # Test with weak new password
    response = client.post(
        '/profile/change_password',
        data={
            'current_password': 'test_password',
            'new_password': 'weak',
            'confirm_password': 'weak'
        },
        follow_redirects=True
    )
    
    # Should show an error message
    assert response.status_code == 200
    assert b'Password must be at least 8 characters' in response.data
    
    # Test with mismatched passwords
    response = client.post(
        '/profile/change_password',
        data={
            'current_password': 'test_password',
            'new_password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        },
        follow_redirects=True
    )
    
    # Should show an error message
    assert response.status_code == 200
    assert b'Passwords do not match' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.profile
def test_setup_mfa_page(client, app, init_database):
    """Test that the MFA setup page loads correctly."""
    # Create a test user without MFA enabled
    with app.app_context():
        execute_query(
            """
            INSERT INTO users (
                username, password, isadmin, email, mfa_enabled
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                mfa_enabled = EXCLUDED.mfa_enabled
            """,
            ('mfa_test_user', generate_password_hash('test_password'), 0, 'mfa_test@example.com', False),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'mfa_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the MFA setup page
    response = client.get('/profile/setup-mfa')
    
    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Set Up Multi-Factor Authentication' in response.data
    assert b'Scan the QR code with your authenticator app' in response.data
    assert b'data:image/png;base64' in response.data  # QR code image

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.profile
def test_manage_mfa_page(client, app, init_database):
    """Test that the MFA management page loads correctly for users with MFA enabled."""
    # Create a test user with MFA enabled
    with app.app_context():
        execute_query(
            """
            INSERT INTO users (
                username, password, isadmin, email, mfa_enabled, mfa_secret, mfa_backup_codes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                mfa_enabled = EXCLUDED.mfa_enabled,
                mfa_secret = EXCLUDED.mfa_secret,
                mfa_backup_codes = EXCLUDED.mfa_backup_codes
            """,
            (
                'mfa_enabled_user', 
                generate_password_hash('test_password'), 
                0, 
                'mfa_enabled@example.com', 
                True,
                'TESTSECRETKEY123456',
                '["BACKUP1", "BACKUP2"]'
            ),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'mfa_enabled_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the MFA management page
    response = client.get('/profile/manage-mfa')
    
    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Manage Multi-Factor Authentication' in response.data
    assert b'MFA is currently enabled' in response.data
    assert b'Disable MFA' in response.data
