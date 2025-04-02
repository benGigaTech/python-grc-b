"""Test script for database connection pooling."""

import os
import sys
import time
import argparse
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('connection_pool_test')

# Track app contexts per thread to prevent premature closing
_app_contexts = {}
_app_context_lock = Lock()

def setup_flask_app():
    """Setup Flask app to access database service."""
    # Add the parent directory to the Python path
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    sys.path.insert(0, parent_dir)
    
    # Import Flask app
    from cmmc_tracker.app import create_app
    app = create_app('development')
    return app

def get_app_context(app, thread_id=None):
    """Get or create an app context for the current thread."""
    if thread_id is None:
        thread_id = threading.get_ident()
    
    with _app_context_lock:
        if thread_id not in _app_contexts:
            logger.debug(f"Creating new app context for thread {thread_id}")
            ctx = app.app_context()
            ctx.push()
            _app_contexts[thread_id] = ctx
        return _app_contexts[thread_id]

def cleanup_app_contexts():
    """Clean up all app contexts at the end of the test."""
    with _app_context_lock:
        for thread_id, ctx in list(_app_contexts.items()):
            try:
                logger.debug(f"Popping app context for thread {thread_id}")
                ctx.pop()
            except Exception as e:
                logger.error(f"Error popping app context for thread {thread_id}: {e}")
            finally:
                del _app_contexts[thread_id]

def test_query(query_id, app):
    """Execute a simple query to test database connections."""
    thread_id = threading.get_ident()
    # Get app context for this thread
    get_app_context(app, thread_id)
    
    try:
        # Now we're in an app context
        from cmmc_tracker.app.services.database import execute_query, release_connection
        
        # Simple query to test connection
        try:
            start_time = time.time()
            result = execute_query("SELECT 1 as test", fetch_one=True)
            end_time = time.time()
            
            if result:
                logger.info(f"Query {query_id}: Successfully executed in {end_time - start_time:.4f} seconds")
                return True
            else:
                logger.error(f"Query {query_id}: No result returned")
                return False
        except Exception as e:
            logger.error(f"Query {query_id}: Error executing query: {e}")
            return False
        finally:
            # Always release connection back to pool when done
            try:
                release_connection()
                logger.debug(f"Query {query_id}: Connection released for thread {thread_id}")
            except Exception as e:
                logger.error(f"Query {query_id}: Error releasing connection: {e}")
    except Exception as e:
        logger.error(f"Query {query_id}: Unhandled error: {e}")
        return False

def run_concurrent_queries(num_queries, max_workers):
    """Run multiple queries concurrently to test connection pool."""
    logger.info(f"Starting test with {num_queries} concurrent queries using {max_workers} workers")
    
    app = setup_flask_app()
    success_count = 0
    
    try:
        # Use ThreadPoolExecutor to simulate concurrent requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all queries
            futures = [executor.submit(test_query, i, app) for i in range(num_queries)]
            
            # Wait for all to complete and count successes
            for future in futures:
                if future.result():
                    success_count += 1
    finally:
        # Clean up app contexts
        cleanup_app_contexts()
    
    logger.info(f"Test completed: {success_count}/{num_queries} queries succeeded")
    return success_count

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description='Test database connection pooling')
    parser.add_argument('--queries', type=int, default=50, help='Number of queries to execute')
    parser.add_argument('--workers', type=int, default=10, help='Maximum number of concurrent workers')
    args = parser.parse_args()
    
    start_time = time.time()
    run_concurrent_queries(args.queries, args.workers)
    end_time = time.time()
    
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == '__main__':
    main() 