"""Integration tests for authentication routes using direct database connections."""

import pytest
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash

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
def test_successful_login(client):
    """Test successful login with correct credentials."""
    # Create a test user directly in the database
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host='python-grc-b-db_test-1',
            port=5432,
            database='cmmc_test_db',
            user='cmmc_user',
            password='password'
        )
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=DictCursor)

        # Create the users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                userid SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                isadmin INTEGER DEFAULT 0,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret VARCHAR(255),
                mfa_backup_codes TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP
            )
        """)

        # Create the user
        cursor.execute(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('login_test_user', generate_password_hash('test_password'), 0, 'login_test@example.com')
        )

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating test user: {e}")

    # Test login
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
def test_failed_login(client):
    """Test failed login with incorrect credentials."""
    # Create a test user directly in the database
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host='python-grc-b-db_test-1',
            port=5432,
            database='cmmc_test_db',
            user='cmmc_user',
            password='password'
        )
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=DictCursor)

        # Create the users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                userid SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                isadmin INTEGER DEFAULT 0,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret VARCHAR(255),
                mfa_backup_codes TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP
            )
        """)

        # Create the user
        cursor.execute(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('login_test_user', generate_password_hash('test_password'), 0, 'login_test@example.com')
        )

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating test user: {e}")

    # Test login with wrong password
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
def test_logout(client):
    """Test logout functionality."""
    # Create a test user directly in the database
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host='python-grc-b-db_test-1',
            port=5432,
            database='cmmc_test_db',
            user='cmmc_user',
            password='password'
        )
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=DictCursor)

        # Create the users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                userid SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                isadmin INTEGER DEFAULT 0,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret VARCHAR(255),
                mfa_backup_codes TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP
            )
        """)

        # Create the user
        cursor.execute(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('logout_test_user', generate_password_hash('test_password'), 0, 'logout_test@example.com')
        )

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating test user: {e}")

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
