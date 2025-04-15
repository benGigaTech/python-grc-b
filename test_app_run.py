#!/usr/bin/env python3
"""Test application run."""

from cmmc_tracker.app import create_app
from cmmc_tracker.app.services.database import get_db_connection
from redis import Redis

def test_app_run():
    """Test application run."""
    app = create_app()
    print('Application created successfully!')

    # Test database connection
    with app.app_context():
        conn = get_db_connection()
        print('Database connection successful!')
        conn.close()

    # Test Redis connection
    redis_host = app.config.get('REDIS_HOST')
    redis_port = app.config.get('REDIS_PORT')
    print(f'Connecting to Redis at {redis_host}:{redis_port}')

    try:
        redis_client = Redis(host=redis_host, port=redis_port)
        if redis_client.ping():
            print('Redis connection successful!')
        else:
            print('Redis ping failed!')
    except Exception as e:
        print(f'Redis connection failed: {e}')

if __name__ == '__main__':
    test_app_run()
