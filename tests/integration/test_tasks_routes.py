"""Integration tests for task management routes."""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from cmmc_tracker.app.models.task import Task
from cmmc_tracker.app.services.database import execute_query
from datetime import date, timedelta

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tasks
def test_add_task_page(client, app, init_database):
    """Test that the add task page loads correctly."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('tasks_test_user', generate_password_hash('test_password'), 0, 'tasks_test@example.com'),
            commit=True
        )

        # Create a test control
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription
            ) VALUES (%s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.3.001',
                'Tasks Test Control',
                'This is a test control for tasks testing'
            ),
            commit=True
        )

    # Login
    client.post(
        '/login',
        data={'username': 'tasks_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Access the add task page
    response = client.get('/add_task/TEST.3.001')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Add Task' in response.data
    assert b'Task Description' in response.data
    assert b'Assigned To' in response.data
    assert b'Due Date' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tasks
def test_add_task(client, app, init_database):
    """Test adding a new task."""
    # Create test users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'tasks_test_user', generate_password_hash('test_password'), 0, 'tasks_test@example.com',
                'tasks_assignee', generate_password_hash('test_password'), 0, 'assignee@example.com'
            ),
            commit=True
        )

        # Create a test control
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription
            ) VALUES (%s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.3.001',
                'Tasks Test Control',
                'This is a test control for tasks testing'
            ),
            commit=True
        )

    # Login
    client.post(
        '/login',
        data={'username': 'tasks_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Get tomorrow's date for the due date
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Add a new task
    response = client.post(
        '/add_task/TEST.3.001',
        data={
            'task_description': 'Test Task Description',
            'assigned_to': 'tasks_assignee',
            'due_date': tomorrow,
            'reviewer': 'tasks_test_user'
        },
        follow_redirects=True
    )

    # Check that the task was added successfully
    assert response.status_code == 200
    assert b'Task added successfully' in response.data
    assert b'Test Task Description' in response.data
    assert b'tasks_assignee' in response.data
    assert b'Open' in response.data

    # Verify in the database
    with app.app_context():
        task = execute_query(
            "SELECT * FROM tasks WHERE taskdescription = %s",
            ('Test Task Description',),
            fetch_one=True
        )
        assert task is not None
        assert task['controlid'] == 'TEST.3.001'
        assert task['assignedto'] == 'tasks_assignee'
        assert task['status'] == 'Open'
        assert task['reviewer'] == 'tasks_test_user'

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tasks
def test_complete_task(client, app, init_database):
    """Test completing a task."""
    # Create test users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'tasks_test_user', generate_password_hash('test_password'), 0, 'tasks_test@example.com',
                'tasks_assignee', generate_password_hash('test_password'), 0, 'assignee@example.com'
            ),
            commit=True
        )

        # Create a test control
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription
            ) VALUES (%s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.3.001',
                'Tasks Test Control',
                'This is a test control for tasks testing'
            ),
            commit=True
        )

        # Create a test task
        result = execute_query(
            """
            INSERT INTO tasks (
                controlid, taskdescription, assignedto, duedate, status, reviewer
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING taskid
            """,
            (
                'TEST.3.001',
                'Test Task to Complete',
                'tasks_assignee',
                (date.today() + timedelta(days=1)).isoformat(),
                'Open',
                'tasks_test_user'
            ),
            fetch_one=True,
            commit=True
        )
        task_id = result['taskid']

    # Login as the assignee
    client.post(
        '/login',
        data={'username': 'tasks_assignee', 'password': 'test_password'},
        follow_redirects=True
    )

    # Complete the task
    response = client.post(
        f'/complete_task/{task_id}',
        follow_redirects=True
    )

    # Check that the task was marked as pending confirmation
    assert response.status_code == 200
    assert b'Task marked as complete' in response.data
    assert b'Pending Confirmation' in response.data

    # Verify in the database
    with app.app_context():
        task = execute_query(
            "SELECT status FROM tasks WHERE taskid = %s",
            (task_id,),
            fetch_one=True
        )
        assert task['status'] == 'Pending Confirmation'

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tasks
def test_confirm_task(client, app, init_database):
    """Test confirming a completed task."""
    # Create test users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'tasks_test_user', generate_password_hash('test_password'), 0, 'tasks_test@example.com',
                'tasks_assignee', generate_password_hash('test_password'), 0, 'assignee@example.com'
            ),
            commit=True
        )

        # Create a test control
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription
            ) VALUES (%s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.3.001',
                'Tasks Test Control',
                'This is a test control for tasks testing'
            ),
            commit=True
        )

        # Create a test task that is pending confirmation
        result = execute_query(
            """
            INSERT INTO tasks (
                controlid, taskdescription, assignedto, duedate, status, reviewer
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING taskid
            """,
            (
                'TEST.3.001',
                'Test Task to Confirm',
                'tasks_assignee',
                (date.today() + timedelta(days=1)).isoformat(),
                'Pending Confirmation',
                'tasks_test_user'
            ),
            fetch_one=True,
            commit=True
        )
        task_id = result['taskid']

    # Login as the reviewer
    client.post(
        '/login',
        data={'username': 'tasks_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Confirm the task
    response = client.post(
        f'/confirm_task/{task_id}',
        follow_redirects=True
    )

    # Check that the task was marked as completed
    assert response.status_code == 200

    # Verify in the database that the task was marked as completed

    # Verify in the database
    with app.app_context():
        task = execute_query(
            "SELECT status FROM tasks WHERE taskid = %s",
            (task_id,),
            fetch_one=True
        )
        assert task['status'] == 'Completed'

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tasks
def test_edit_task(client, app, init_database):
    """Test editing a task."""
    # Create test users
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s), (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            (
                'tasks_test_user', generate_password_hash('test_password'), 0, 'tasks_test@example.com',
                'tasks_assignee', generate_password_hash('test_password'), 0, 'assignee@example.com'
            ),
            commit=True
        )

        # Create a test control
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription
            ) VALUES (%s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.3.001',
                'Tasks Test Control',
                'This is a test control for tasks testing'
            ),
            commit=True
        )

        # Create a test task
        result = execute_query(
            """
            INSERT INTO tasks (
                controlid, taskdescription, assignedto, duedate, status, reviewer
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING taskid
            """,
            (
                'TEST.3.001',
                'Original Task Description',
                'tasks_assignee',
                (date.today() + timedelta(days=1)).isoformat(),
                'Open',
                'tasks_test_user'
            ),
            fetch_one=True,
            commit=True
        )
        task_id = result['taskid']

    # Login as an admin
    client.post(
        '/login',
        data={'username': 'tasks_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Get the edit task page
    response = client.get(f'/edit_task/{task_id}')
    assert response.status_code == 200
    assert b'Edit Task' in response.data
    assert b'Original Task Description' in response.data

    # Edit the task
    new_due_date = (date.today() + timedelta(days=2)).isoformat()
    response = client.post(
        f'/edit_task/{task_id}',
        data={
            'task_description': 'Updated Task Description',
            'assigned_to': 'tasks_assignee',
            'due_date': new_due_date,
            'reviewer': 'tasks_test_user'
        },
        follow_redirects=True
    )

    # Check that the task was updated successfully
    assert response.status_code == 200

    # Verify in the database that the task was updated

    # Verify in the database
    with app.app_context():
        task = execute_query(
            "SELECT * FROM tasks WHERE taskid = %s",
            (task_id,),
            fetch_one=True
        )
        assert task['taskdescription'] == 'Updated Task Description'
        assert task['duedate'] == new_due_date

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tasks
def test_delete_task(client, app, init_database):
    """Test deleting a task."""
    # Create a test user with admin privileges
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('tasks_admin_user', generate_password_hash('test_password'), 1, 'tasks_admin@example.com'),
            commit=True
        )

        # Create a test control
        execute_query(
            """
            INSERT INTO controls (
                controlid, controlname, controldescription
            ) VALUES (%s, %s, %s)
            ON CONFLICT (controlid) DO NOTHING
            """,
            (
                'TEST.3.001',
                'Tasks Test Control',
                'This is a test control for tasks testing'
            ),
            commit=True
        )

        # Create a test task
        result = execute_query(
            """
            INSERT INTO tasks (
                controlid, taskdescription, assignedto, duedate, status, reviewer
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING taskid
            """,
            (
                'TEST.3.001',
                'Task to Delete',
                'tasks_admin_user',
                (date.today() + timedelta(days=1)).isoformat(),
                'Open',
                'tasks_admin_user'
            ),
            fetch_one=True,
            commit=True
        )
        task_id = result['taskid']

    # Login as admin
    client.post(
        '/login',
        data={'username': 'tasks_admin_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Delete the task
    response = client.post(
        f'/delete_task/{task_id}',
        follow_redirects=True
    )

    # Check that the task was deleted successfully
    assert response.status_code == 200
    assert b'Task deleted successfully' in response.data

    # Verify in the database
    with app.app_context():
        task = execute_query(
            "SELECT * FROM tasks WHERE taskid = %s",
            (task_id,),
            fetch_one=True
        )
        assert task is None
