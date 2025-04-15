"""Integration tests for authentication routes."""

import pytest
from flask import session, url_for
from werkzeug.security import generate_password_hash
from cmmc_tracker.app.models.user import User
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.auth
def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Username' in response.data
    assert b'Password' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.auth
def test_successful_login(client, app, init_database):
    """Test successful login with correct credentials."""
    # Ensure test user exists
    execute_query(
        "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
        ('login_test_user', generate_password_hash('test_password'), 0, 'login_test@example.com'),
        commit=True
    )
    
    response = client.post(
        '/login',
        data={'username': 'login_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data
    
    # Check that we're redirected to the dashboard
    assert b'Dashboard' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.auth
def test_failed_login(client, init_database):
    """Test failed login with incorrect credentials."""
    # Ensure test user exists
    execute_query(
        "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
        ('login_test_user', generate_password_hash('test_password'), 0, 'login_test@example.com'),
        commit=True
    )
    
    response = client.post(
        '/login',
        data={'username': 'login_test_user', 'password': 'wrong_password'},
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data
    
    # Check that we're still on the login page
    assert b'Login' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.auth
def test_logout(client, init_database):
    """Test logout functionality."""
    # Ensure test user exists
    execute_query(
        "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
        ('logout_test_user', generate_password_hash('test_password'), 0, 'logout_test@example.com'),
        commit=True
    )
    
    # Login first
    client.post(
        '/login',
        data={'username': 'logout_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    
    # Check that we're redirected to the login page
    assert b'Login' in response.data
