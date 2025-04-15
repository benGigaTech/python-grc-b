#!/usr/bin/env python3
"""Test database connection."""

from cmmc_tracker.app import create_app
from cmmc_tracker.app.services.database import get_db_connection

def test_db_connection():
    """Test database connection."""
    app = create_app()
    with app.app_context():
        conn = get_db_connection()
        print('Database connection successful!')
        conn.close()

if __name__ == '__main__':
    test_db_connection()
