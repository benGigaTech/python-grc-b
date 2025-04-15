"""Pytest configuration file for the CMMC Tracker application."""

import os
import sys
import pytest
from flask import Flask

# Add the parent directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Import the create_app function
from cmmc_tracker.app import create_app, login_manager
from cmmc_tracker.app.models.user import User

@pytest.fixture
def app():
    """Create and configure a Flask application for testing."""
    # Create the app with the testing configuration
    app = create_app('testing')

    # Register the user_loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from cmmc_tracker.app.models.user import User
        return User.get_by_id(user_id)

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
    import os

    # Override the DB_HOST environment variable for testing
    original_db_host = os.environ.get('DB_HOST')
    os.environ['DB_HOST'] = 'db_test'

    # Create a fresh connection for each test
    with app.app_context():
        conn = get_db_connection()
        yield conn
        # Make sure to close the connection properly
        try:
            conn.close()
        except Exception:
            pass

    # Restore the original DB_HOST
    if original_db_host:
        os.environ['DB_HOST'] = original_db_host
    else:
        os.environ.pop('DB_HOST', None)

@pytest.fixture
def init_database(app):
    """Initialize the test database with minimal test data."""
    # Import here to avoid circular imports
    from cmmc_tracker.app.services.database import execute_query
    import psycopg2
    from psycopg2.extras import DictCursor
    import os

    # Get database connection parameters from environment
    db_host = os.environ.get('DB_HOST', 'db_test')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'cmmc_test_db')
    db_user = os.environ.get('DB_USER', 'cmmc_user')
    db_password = os.environ.get('DB_PASSWORD', 'password')

    # Create the database if it doesn't exist
    try:
        # Connect to default postgres database to create test database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cursor.fetchone() is None:
            # Create database
            cursor.execute(f"CREATE DATABASE {db_name}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

    with app.app_context():
        try:
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

            # Create users table if it doesn't exist
            execute_query(
                """
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
                """,
                commit=True
            )

            # Create settings table if it doesn't exist
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
        except Exception as e:
            print(f"Error setting up test database: {e}")

        yield app

