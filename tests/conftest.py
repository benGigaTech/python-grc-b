"""Pytest configuration file for the CMMC Tracker application."""

import os
import sys
import pytest
from flask import Flask

# Add the parent directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Import the create_app function
from cmmc_tracker.app import create_app
# Import database services if needed
# from cmmc_tracker.app.services.database import get_db_connection, execute_query

@pytest.fixture
def app():
    """Create and configure a Flask application for testing."""
    # Create the app with the testing configuration
    app = create_app('testing')

    # Establish application context
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def db_connection(app):
    """Get a database connection for testing."""
    # Import here to avoid circular imports
    from cmmc_tracker.app.services.database import get_db_connection

    # Create a fresh connection for each test
    with app.app_context():
        conn = get_db_connection()
        yield conn
        # Make sure to close the connection properly
        try:
            conn.close()
        except Exception:
            pass

@pytest.fixture
def init_database(app):
    """Initialize the test database with minimal test data."""
    # Import here to avoid circular imports
    from cmmc_tracker.app.services.database import execute_query

    with app.app_context():
        # Create test controls table if it doesn't exist
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS controls (
                controlid VARCHAR(50) PRIMARY KEY,
                controlname VARCHAR(255) NOT NULL,
                controldescription TEXT,
                nist_sp_800_171_mapping VARCHAR(255),
                policyreviewfrequency VARCHAR(50),
                lastreviewdate DATE,
                nextreviewdate DATE
            )
            """,
            commit=True
        )

        # Create test evidence table if it doesn't exist
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                evidenceid SERIAL PRIMARY KEY,
                controlid VARCHAR(50) REFERENCES controls(controlid),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                filepath VARCHAR(255),
                filetype VARCHAR(100),
                filesize INTEGER,
                uploadedby VARCHAR(100),
                uploaddate DATE,
                expirationdate DATE,
                status VARCHAR(50) DEFAULT 'Current'
            )
            """,
            commit=True
        )

        # Create test tasks table if it doesn't exist
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                taskid SERIAL PRIMARY KEY,
                controlid VARCHAR(50) REFERENCES controls(controlid),
                taskdescription TEXT NOT NULL,
                assignedto VARCHAR(100),
                duedate DATE,
                status VARCHAR(50) DEFAULT 'Open',
                confirmed INTEGER DEFAULT 0,
                reviewer VARCHAR(100)
            )
            """,
            commit=True
        )

        yield app

