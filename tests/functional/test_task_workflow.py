"""Functional tests for task management workflow."""

import pytest
from werkzeug.security import generate_password_hash
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.functional
@pytest.mark.tasks
def test_task_creation_workflow(client, init_database):
    """Test the complete workflow of creating and managing a task."""
    # Ensure test users and control exist
    execute_query(
        "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
        ('workflow_admin', generate_password_hash('test_password'), 1, 'workflow_admin@example.com'),
        commit=True
    )
    
    execute_query(
        "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
        ('workflow_user', generate_password_hash('test_password'), 0, 'workflow_user@example.com'),
        commit=True
    )
    
    execute_query(
        """
        INSERT INTO controls (
            controlid, controlname, controldescription, 
            nist_sp_800_171_mapping, policyreviewfrequency, 
            lastreviewdate, nextreviewdate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (controlid) DO NOTHING
        """,
        (
            'WORKFLOW.1.001', 
            'Workflow Test Control', 
            'This is a test control for workflow testing',
            'NIST.800.171.3.1.1',
            'Annual',
            '2023-01-01',
            '2024-01-01'
        ),
        commit=True
    )
    
    # Step 1: Admin logs in
    response = client.post(
        '/login',
        data={'username': 'workflow_admin', 'password': 'test_password'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data
    
    # Step 2: Admin creates a new task
    response = client.post(
        f'/add_task/WORKFLOW.1.001',
        data={
            'task_description': 'Test workflow task',
            'assigned_to': 'workflow_user',
            'due_date': '2024-12-31',
            'csrf_token': 'dummy_token'  # This will be handled by the test client
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Task added successfully' in response.data
    
    # Step 3: Admin logs out
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    
    # Step 4: User logs in
    response = client.post(
        '/login',
        data={'username': 'workflow_user', 'password': 'test_password'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data
    
    # Step 5: User views their tasks
    response = client.get('/tasks', follow_redirects=True)
    assert response.status_code == 200
    assert b'Test workflow task' in response.data
    
    # Get the task ID from the database
    task_data = execute_query(
        "SELECT taskid FROM tasks WHERE taskdescription = %s",
        ('Test workflow task',),
        fetch_one=True
    )
    task_id = task_data['taskid']
    
    # Step 6: User completes the task
    response = client.post(
        f'/complete_task/{task_id}',
        data={'csrf_token': 'dummy_token'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Task marked as completed' in response.data
    
    # Step 7: User logs out
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data
    
    # Step 8: Admin logs back in
    response = client.post(
        '/login',
        data={'username': 'workflow_admin', 'password': 'test_password'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data
    
    # Step 9: Admin confirms the task
    response = client.post(
        f'/confirm_task/{task_id}',
        data={'csrf_token': 'dummy_token'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Task confirmed' in response.data
    
    # Step 10: Verify task status in database
    task_data = execute_query(
        "SELECT status, confirmed FROM tasks WHERE taskid = %s",
        (task_id,),
        fetch_one=True
    )
    assert task_data['status'] == 'Completed'
    assert task_data['confirmed'] == 1
