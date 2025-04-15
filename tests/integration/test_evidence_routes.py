"""Integration tests for evidence management routes."""

import os
import pytest
import io
from flask import url_for
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import FileStorage
from cmmc_tracker.app.models.evidence import Evidence
from cmmc_tracker.app.services.database import execute_query

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.evidence
def test_evidence_list_page(client, app, init_database):
    """Test that the evidence list page loads correctly."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('evidence_test_user', generate_password_hash('test_password'), 0, 'evidence_test@example.com'),
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
                'TEST.2.001',
                'Evidence Test Control',
                'This is a test control for evidence testing'
            ),
            commit=True
        )

        # Create test evidence
        execute_query(
            """
            INSERT INTO evidence (
                controlid, title, description, filepath, filetype, filesize,
                uploadedby, uploaddate, expirationdate, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                'TEST.2.001',
                'Test Evidence',
                'This is test evidence for integration testing',
                '/uploads/TEST.2.001/test_evidence.pdf',
                'application/pdf',
                1024,
                'evidence_test_user',
                '2023-01-01',
                '2024-01-01',
                'Current'
            ),
            commit=True
        )

    # Login
    client.post(
        '/login',
        data={'username': 'evidence_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Access the evidence list page
    response = client.get('/control/TEST.2.001/evidence')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Evidence for Control' in response.data
    assert b'Evidence Test Control' in response.data
    assert b'Test Evidence' in response.data
    assert b'This is test evidence for integration testing' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.evidence
def test_evidence_sorting(client, app, init_database):
    """Test the evidence sorting functionality."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('evidence_test_user', generate_password_hash('test_password'), 0, 'evidence_test@example.com'),
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
                'TEST.2.001',
                'Evidence Test Control',
                'This is a test control for evidence testing'
            ),
            commit=True
        )

        # Create test evidence with different upload dates to test sorting
        execute_query(
            """
            INSERT INTO evidence (
                controlid, title, description, filepath, filetype, filesize,
                uploadedby, uploaddate, expirationdate, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                'TEST.2.001',
                'A Test Evidence',
                'This is test evidence 1',
                '/uploads/TEST.2.001/test_evidence1.pdf',
                'application/pdf',
                1024,
                'evidence_test_user',
                '2023-01-01',
                '2024-01-01',
                'Current',
                'TEST.2.001',
                'B Test Evidence',
                'This is test evidence 2',
                '/uploads/TEST.2.001/test_evidence2.pdf',
                'application/pdf',
                2048,
                'evidence_test_user',
                '2023-02-01',
                '2024-02-01',
                'Current'
            ),
            commit=True
        )

    # Login
    client.post(
        '/login',
        data={'username': 'evidence_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Sort by upload date ascending
    response = client.get('/control/TEST.2.001/evidence?sort_by=uploaddate&sort_order=asc')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Evidence for Control' in response.data

    # Sort by upload date descending
    response = client.get('/control/TEST.2.001/evidence?sort_by=uploaddate&sort_order=desc')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Evidence for Control' in response.data

    # Sort by title ascending
    response = client.get('/control/TEST.2.001/evidence?sort_by=title&sort_order=asc')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Evidence for Control' in response.data

    # Sort by title descending
    response = client.get('/control/TEST.2.001/evidence?sort_by=title&sort_order=desc')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Evidence for Control' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.evidence
def test_evidence_add_page(client, app, init_database):
    """Test that the add evidence page loads correctly."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('evidence_test_user', generate_password_hash('test_password'), 0, 'evidence_test@example.com'),
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
                'TEST.2.001',
                'Evidence Test Control',
                'This is a test control for evidence testing'
            ),
            commit=True
        )

    # Login
    client.post(
        '/login',
        data={'username': 'evidence_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Access the add evidence page
    response = client.get('/control/TEST.2.001/evidence/add')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Add Evidence' in response.data
    assert b'Evidence Test Control' in response.data
    assert b'Title' in response.data
    assert b'Description' in response.data
    assert b'File' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.evidence
def test_evidence_detail_page(client, app, init_database):
    """Test that the evidence detail page loads correctly."""
    # Create a test user
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('evidence_test_user', generate_password_hash('test_password'), 0, 'evidence_test@example.com'),
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
                'TEST.2.001',
                'Evidence Test Control',
                'This is a test control for evidence testing'
            ),
            commit=True
        )

        # Create test evidence
        result = execute_query(
            """
            INSERT INTO evidence (
                controlid, title, description, filepath, filetype, filesize,
                uploadedby, uploaddate, expirationdate, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING evidenceid
            """,
            (
                'TEST.2.001',
                'Test Evidence',
                'This is test evidence for integration testing',
                '/uploads/TEST.2.001/test_evidence.pdf',
                'application/pdf',
                1024,
                'evidence_test_user',
                '2023-01-01',
                '2024-01-01',
                'Current'
            ),
            fetch_one=True,
            commit=True
        )
        evidence_id = result['evidenceid']

    # Login
    client.post(
        '/login',
        data={'username': 'evidence_test_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Access the evidence update page instead (there's no dedicated detail page)
    response = client.get(f'/evidence/{evidence_id}/update')

    # Check that the page loads correctly
    assert response.status_code == 200
    assert b'Update Evidence' in response.data
    assert b'Test Evidence' in response.data
    assert b'This is test evidence for integration testing' in response.data

@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.evidence
def test_evidence_status_update(client, app, init_database):
    """Test updating the status of evidence."""
    # Create a test user with admin privileges
    with app.app_context():
        execute_query(
            "INSERT INTO users (username, password, isadmin, email) VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING",
            ('evidence_admin_user', generate_password_hash('test_password'), 1, 'evidence_admin@example.com'),
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
                'TEST.2.001',
                'Evidence Test Control',
                'This is a test control for evidence testing'
            ),
            commit=True
        )

        # Create test evidence
        result = execute_query(
            """
            INSERT INTO evidence (
                controlid, title, description, filepath, filetype, filesize,
                uploadedby, uploaddate, expirationdate, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING evidenceid
            """,
            (
                'TEST.2.001',
                'Test Evidence',
                'This is test evidence for integration testing',
                '/uploads/TEST.2.001/test_evidence.pdf',
                'application/pdf',
                1024,
                'evidence_admin_user',
                '2023-01-01',
                '2024-01-01',
                'Current'
            ),
            fetch_one=True,
            commit=True
        )
        evidence_id = result['evidenceid']

    # Login as admin
    client.post(
        '/login',
        data={'username': 'evidence_admin_user', 'password': 'test_password'},
        follow_redirects=True
    )

    # Update the evidence status through the update page
    response = client.post(
        f'/evidence/{evidence_id}/update',
        data={
            'title': 'Test Evidence',
            'description': 'This is test evidence for integration testing',
            'expiration_date': '2024-01-01',
            'status': 'Expired'
        },
        follow_redirects=True
    )

    # Check that the status was updated
    assert response.status_code == 200
    assert b'Evidence updated successfully' in response.data

    # Verify in the database
    with app.app_context():
        evidence = execute_query(
            "SELECT status FROM evidence WHERE evidenceid = %s",
            (evidence_id,),
            fetch_one=True
        )
        assert evidence['status'] == 'Expired'
