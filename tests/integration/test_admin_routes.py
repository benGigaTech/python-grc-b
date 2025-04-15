"""Integration tests for admin routes."""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_admin_access_control(client, app, init_database):
    """Test that only admin users can access admin pages."""
    # Create a regular user and an admin user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'regular_user', generate_password_hash('test_password'), 0, 'regular@example.com',
                'admin_user', generate_password_hash('test_password'), 1, 'admin@example.com'
            ),
            commit=True
        )
    
    # Login as regular user
    client.post(
        '/login',
        data={'username': 'regular_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Try to access admin page
    response = client.get('/admin/users')
    
    # Should be redirected with an error message
    assert response.status_code == 200
    assert b'Administrator privileges required' in response.data
    
    # Logout
    client.get('/logout', follow_redirects=True)
    
    # Login as admin user
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Try to access admin page
    response = client.get('/admin/users')
    
    # Should be able to access the page
    assert response.status_code == 200
    assert b'User Management' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_admin_users_page(client, app, init_database):
    """Test that the admin users page loads correctly."""
    # Create an admin user and some regular users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'admin_user', generate_password_hash('test_password'), 1, 'admin@example.com',
                'user1', generate_password_hash('test_password'), 0, 'user1@example.com',
                'user2', generate_password_hash('test_password'), 0, 'user2@example.com'
            ),
            commit=True
        )
    
    # Login as admin
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the users page
    response = client.get('/admin/users')
    
    # Check that the page loads correctly and shows all users
    assert response.status_code == 200
    assert b'User Management' in response.data
    assert b'admin_user' in response.data
    assert b'user1' in response.data
    assert b'user2' in response.data
    assert b'admin@example.com' in response.data
    assert b'user1@example.com' in response.data
    assert b'user2@example.com' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_add_user(client, app, init_database):
    """Test adding a new user through the admin interface."""
    # Create an admin user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('admin_user', generate_password_hash('test_password'), 1, 'admin@example.com'),
            commit=True
        )
    
    # Login as admin
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Add a new user
    response = client.post(
        '/admin/add_user',
        data={
            'username': 'new_test_user',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'email': 'new_test@example.com',
            'is_admin': '0'
        },
        follow_redirects=True
    )
    
    # Check that the user was added successfully
    assert response.status_code == 200
    assert b'User added successfully' in response.data
    assert b'new_test_user' in response.data
    assert b'new_test@example.com' in response.data
    
    # Verify in the database
    with app.app_context():
        user = execute_query(
            "SELECT * FROM users WHERE username = %s",
            ('new_test_user',),
            fetch_one=True
        )
        assert user is not None
        assert user['username'] == 'new_test_user'
        assert user['email'] == 'new_test@example.com'
        assert user['isadmin'] == 0
        assert check_password_hash(user['password'], 'StrongPassword123!')

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_edit_user(client, app, init_database):
    """Test editing a user through the admin interface."""
    # Create an admin user and a user to edit
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'admin_user', generate_password_hash('test_password'), 1, 'admin@example.com',
                'edit_test_user', generate_password_hash('old_password'), 0, 'old_email@example.com'
            ),
            commit=True
        )
        
        # Get the user ID
        user = execute_query(
            "SELECT userid FROM users WHERE username = %s",
            ('edit_test_user',),
            fetch_one=True
        )
        user_id = user['userid']
    
    # Login as admin
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Get the edit user page
    response = client.get(f'/admin/edit_user/{user_id}')
    assert response.status_code == 200
    assert b'Edit User' in response.data
    assert b'edit_test_user' in response.data
    assert b'old_email@example.com' in response.data
    
    # Edit the user
    response = client.post(
        f'/admin/edit_user/{user_id}',
        data={
            'email': 'new_email@example.com',
            'is_admin': '1',
            'password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        },
        follow_redirects=True
    )
    
    # Check that the user was updated successfully
    assert response.status_code == 200
    assert b'User updated successfully' in response.data
    assert b'new_email@example.com' in response.data
    
    # Verify in the database
    with app.app_context():
        user = execute_query(
            "SELECT * FROM users WHERE userid = %s",
            (user_id,),
            fetch_one=True
        )
        assert user['email'] == 'new_email@example.com'
        assert user['isadmin'] == 1
        assert check_password_hash(user['password'], 'NewPassword123!')

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_delete_user(client, app, init_database):
    """Test deleting a user through the admin interface."""
    # Create an admin user and a user to delete
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'admin_user', generate_password_hash('test_password'), 1, 'admin@example.com',
                'delete_test_user', generate_password_hash('test_password'), 0, 'delete@example.com'
            ),
            commit=True
        )
        
        # Get the user ID
        user = execute_query(
            "SELECT userid FROM users WHERE username = %s",
            ('delete_test_user',),
            fetch_one=True
        )
        user_id = user['userid']
    
    # Login as admin
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Delete the user
    response = client.post(
        f'/admin/delete_user/{user_id}',
        follow_redirects=True
    )
    
    # Check that the user was deleted successfully
    assert response.status_code == 200
    assert b'User deleted successfully' in response.data
    assert b'delete_test_user' not in response.data
    
    # Verify in the database
    with app.app_context():
        user = execute_query(
            "SELECT * FROM users WHERE userid = %s",
            (user_id,),
            fetch_one=True
        )
        assert user is None

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_admin_settings_page(client, app, init_database):
    """Test that the admin settings page loads correctly."""
    # Create an admin user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('admin_user', generate_password_hash('test_password'), 1, 'admin@example.com'),
            commit=True
        )
        
        # Create some settings
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS settings (
                setting_key VARCHAR(100) PRIMARY KEY,
                setting_value TEXT,
                setting_type VARCHAR(20),
                description TEXT
            )
            """,
            commit=True
        )
        
        execute_query(
            """
            INSERT INTO settings (setting_key, setting_value, setting_type, description)
            VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)
            ON CONFLICT (setting_key) DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description
            """,
            (
                'app.name', 'CMMC Compliance Tracker', 'string', 'Application name displayed in the UI',
                'notification.enabled', 'true', 'boolean', 'Enable email notifications'
            ),
            commit=True
        )
    
    # Login as admin
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the settings page
    response = client.get('/admin/settings')
    
    # Check that the page loads correctly and shows the settings
    assert response.status_code == 200
    assert b'Application Settings' in response.data
    assert b'app.name' in response.data
    assert b'CMMC Compliance Tracker' in response.data
    assert b'notification.enabled' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.admin
def test_update_settings(client, app, init_database):
    """Test updating settings through the admin interface."""
    # Create an admin user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('admin_user', generate_password_hash('test_password'), 1, 'admin@example.com'),
            commit=True
        )
        
        # Create some settings
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS settings (
                setting_key VARCHAR(100) PRIMARY KEY,
                setting_value TEXT,
                setting_type VARCHAR(20),
                description TEXT
            )
            """,
            commit=True
        )
        
        execute_query(
            """
            INSERT INTO settings (setting_key, setting_value, setting_type, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (setting_key) DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description
            """,
            (
                'app.name', 'Old App Name', 'string', 'Application name displayed in the UI'
            ),
            commit=True
        )
    
    # Login as admin
    client.post(
        '/login',
        data={'username': 'admin_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Update the setting
    response = client.post(
        '/admin/settings',
        data={
            'app.name': 'New App Name'
        },
        follow_redirects=True
    )
    
    # Check that the setting was updated successfully
    assert response.status_code == 200
    assert b'Settings updated successfully' in response.data
    assert b'New App Name' in response.data
    
    # Verify in the database
    with app.app_context():
        setting = execute_query(
            "SELECT setting_value FROM settings WHERE setting_key = %s",
            ('app.name',),
            fetch_one=True
        )
        assert setting['setting_value'] == 'New App Name'
