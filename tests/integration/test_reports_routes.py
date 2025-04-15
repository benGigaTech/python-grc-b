"""Integration tests for reports routes."""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from cmmc_tracker.app.services.database import execute_query
from datetime import date, timedelta

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.reports
def test_reports_page(client, app, init_database):
    """Test that the reports page loads correctly."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('reports_test_user', generate_password_hash('test_password'), 0, 'reports_test@example.com'),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'reports_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the reports page
    response = client.get('/reports')
    
    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Compliance Reports' in response.data
    assert b'Overdue Tasks' in response.data
    assert b'Tasks by User' in response.data
    assert b'Upcoming Control Reviews' in response.data
    assert b'Past Due Control Reviews' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.reports
def test_reports_with_data(client, app, init_database):
    """Test the reports page with test data."""
    # Create test users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'reports_test_user', generate_password_hash('test_password'), 0, 'reports_test@example.com',
                'reports_assignee', generate_password_hash('test_password'), 0, 'assignee@example.com'
            ),
            commit=True
        )
        
        # Create test controls with different review dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        last_week = today - timedelta(days=7)
        
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription, policyreviewfrequency, lastreviewdate, nextreviewdate
            ) VALUES 
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.4.001', 'Past Due Control', 'This control is past due', 'Annual', last_week.isoformat(), yesterday.isoformat(),
                'TEST.4.002', 'Upcoming Control', 'This control is due soon', 'Annual', last_week.isoformat(), tomorrow.isoformat(),
                'TEST.4.003', 'Future Control', 'This control is due in the future', 'Annual', last_week.isoformat(), next_week.isoformat()
            ),
            commit=True
        )
        
        # Create test tasks with different statuses and due dates
        execute_query(
            """
            INSERT INTO tasks (
                controlid, taskdescription, assignedto, duedate, status, reviewer
            ) VALUES 
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s)
            """,
            (
                'TEST.4.001', 'Overdue Task', 'reports_assignee', yesterday.isoformat(), 'Open', 'reports_test_user',
                'TEST.4.002', 'Current Task', 'reports_assignee', tomorrow.isoformat(), 'Open', 'reports_test_user',
                'TEST.4.002', 'Pending Task', 'reports_assignee', tomorrow.isoformat(), 'Pending Confirmation', 'reports_test_user',
                'TEST.4.003', 'Completed Task', 'reports_assignee', next_week.isoformat(), 'Completed', 'reports_test_user'
            ),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'reports_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Access the reports page with default date range (30 days)
    response = client.get('/reports')
    
    # Check that the page shows the correct data
    assert response.status_code == 200
    
    # Overdue tasks section should show the overdue task
    assert b'Overdue Task' in response.data
    
    # Tasks by user section should show the assignee with their tasks
    assert b'reports_assignee' in response.data
    
    # Upcoming controls section should show the controls due within 30 days
    assert b'Upcoming Control' in response.data
    assert b'TEST.4.002' in response.data
    
    # Past due controls section should show the past due control
    assert b'Past Due Control' in response.data
    assert b'TEST.4.001' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.reports
def test_reports_date_range_filter(client, app, init_database):
    """Test the date range filter on the reports page."""
    # Create test users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('reports_test_user', generate_password_hash('test_password'), 0, 'reports_test@example.com'),
            commit=True
        )
        
        # Create test controls with different review dates
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        next_month = today + timedelta(days=31)
        last_month = today - timedelta(days=31)
        
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription, policyreviewfrequency, lastreviewdate, nextreviewdate
            ) VALUES 
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.4.001', 'Tomorrow Control', 'This control is due tomorrow', 'Annual', last_month.isoformat(), tomorrow.isoformat(),
                'TEST.4.002', 'Next Week Control', 'This control is due next week', 'Annual', last_month.isoformat(), next_week.isoformat(),
                'TEST.4.003', 'Next Month Control', 'This control is due next month', 'Annual', last_month.isoformat(), next_month.isoformat()
            ),
            commit=True
        )
    
    # Login
    client.post(
        '/login',
        data={'username': 'reports_test_user', 'password': 'test_password'},
        follow_redirects=True
    )
    
    # Test with 7-day filter
    response = client.get('/reports?date_range=7')
    
    # Should include tomorrow's control but not next week or next month
    assert response.status_code == 200
    assert b'Tomorrow Control' in response.data
    assert b'TEST.4.001' in response.data
    assert b'Next Week Control' not in response.data
    assert b'Next Month Control' not in response.data
    
    # Test with 14-day filter
    response = client.get('/reports?date_range=14')
    
    # Should include tomorrow's and next week's controls but not next month
    assert response.status_code == 200
    assert b'Tomorrow Control' in response.data
    assert b'Next Week Control' in response.data
    assert b'TEST.4.001' in response.data
    assert b'TEST.4.002' in response.data
    assert b'Next Month Control' not in response.data
    
    # Test with 'all' filter
    response = client.get('/reports?date_range=all')
    
    # Should include all controls
    assert response.status_code == 200
    assert b'Tomorrow Control' in response.data
    assert b'Next Week Control' in response.data
    assert b'Next Month Control' in response.data
    assert b'TEST.4.001' in response.data
    assert b'TEST.4.002' in response.data
    assert b'TEST.4.003' in response.data
