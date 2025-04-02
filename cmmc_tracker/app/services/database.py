"""Database service for the CMMC Tracker application."""

import logging
import threading
import atexit
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import sql
from psycopg2.pool import ThreadedConnectionPool
from flask import current_app, g

logger = logging.getLogger(__name__)

# Global connection pool and lock
_pool = None
_pool_lock = threading.Lock()

# Track connections globally by thread ID to avoid issues with g context
_thread_local = threading.local()

def get_pool():
    """
    Get or create the database connection pool.
    
    Returns:
        ThreadedConnectionPool: The connection pool
    """
    global _pool
    
    # If pool exists and is not closed, return it
    if _pool is not None and not _pool.closed:
        return _pool
    
    # Use lock to prevent multiple threads from creating pools simultaneously
    with _pool_lock:
        # Check again inside the lock
        if _pool is not None and not _pool.closed:
            return _pool
            
        # Create a new pool
        try:
            _pool = ThreadedConnectionPool(
                current_app.config['DB_POOL_MIN_CONN'],
                current_app.config['DB_POOL_MAX_CONN'],
                host=current_app.config['DB_HOST'],
                port=current_app.config['DB_PORT'],
                database=current_app.config['DB_NAME'],
                user=current_app.config['DB_USER'],
                password=current_app.config['DB_PASSWORD']
            )
            logger.info(f"Created new database connection pool with min={current_app.config['DB_POOL_MIN_CONN']}, max={current_app.config['DB_POOL_MAX_CONN']} connections")
            return _pool
        except psycopg2.Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

def get_db_connection():
    """
    Get a connection from the pool.
    
    Returns:
        Connection: A PostgreSQL database connection from the pool
    """
    # Get thread ID for this request
    thread_id = threading.get_ident()
    
    # Check if we already have a connection for this thread
    if hasattr(_thread_local, 'connection'):
        logger.debug(f"Reusing existing connection for thread {thread_id}")
        return _thread_local.connection
    
    # Otherwise, get a new connection from the pool
    pool = get_pool()
    try:
        conn = pool.getconn(key=thread_id)
        _thread_local.connection = conn
        
        # Track this connection in Flask context for teardown if available
        if has_app_context():
            if not hasattr(g, 'db_connections'):
                g.db_connections = {}
            g.db_connections[thread_id] = conn
            
        logger.debug(f"Obtained new connection from pool for thread {thread_id}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to get connection from pool: {e}")
        raise

def has_app_context():
    """Check if we're in a Flask application context"""
    try:
        return current_app is not None
    except RuntimeError:
        return False

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query with standardized error handling.
    
    Args:
        query (str or sql.Composable): SQL query to execute
        params (tuple, optional): Parameters for the query
        fetch_one (bool): Whether to fetch one result
        fetch_all (bool): Whether to fetch all results
        commit (bool): Whether to commit the transaction
        
    Returns:
        The result of the query if fetch_one or fetch_all is True, otherwise None
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Handle different query types
        if isinstance(query, sql.Composable):
            # It's a SQL composition object
            cursor.execute(query, params)
        else:
            # It's a regular string query
            cursor.execute(query, params)
            
        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
            
        if commit:
            conn.commit()
            
        return result
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        # Rethrow as a custom exception that can be caught and handled appropriately
        raise Exception(f"Database operation failed: {str(e)}")
    finally:
        # Don't close connections here, they're managed by thread local and app context
        pass

def release_connection():
    """Release the current thread's database connection back to the pool."""
    thread_id = threading.get_ident()
    
    if hasattr(_thread_local, 'connection'):
        try:
            # Get the pool, but don't create a new one if it doesn't exist
            global _pool
            if _pool is not None and not _pool.closed:
                _pool.putconn(_thread_local.connection, key=thread_id)
                logger.debug(f"Released connection back to pool for thread {thread_id}")
        except Exception as e:
            logger.error(f"Error returning connection to pool for thread {thread_id}: {e}")
        finally:
            # Clean up thread local storage
            delattr(_thread_local, 'connection')

def close_pool():
    """Close the connection pool."""
    global _pool
    
    with _pool_lock:
        if _pool is not None:
            try:
                # Release all thread-local connections before closing pool
                _pool.closeall()
                logger.info("Closed all database connections in the pool")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
            finally:
                _pool = None

# Register functions to be called when the application starts and shuts down
def init_app(app):
    """Initialize the database service with the application."""
    # Close all database connections when the request ends
    @app.teardown_appcontext
    def close_db_connections(exception=None):
        """Release database connections when the application context ends."""
        if hasattr(g, 'db_connections'):
            pool = get_pool()
            for thread_id, conn in list(g.db_connections.items()):
                try:
                    if pool is not None and not pool.closed:
                        pool.putconn(conn, key=thread_id)
                        logger.debug(f"Released connection back to pool for thread {thread_id}")
                except Exception as e:
                    logger.error(f"Error returning connection to pool for thread {thread_id}: {e}")
                finally:
                    try:
                        if hasattr(_thread_local, 'connection') and _thread_local.connection == conn:
                            delattr(_thread_local, 'connection')
                    except:
                        pass
                    
                    if thread_id in g.db_connections:
                        del g.db_connections[thread_id]
    
    # Register cleanup function to close pool at process shutdown
    atexit.register(close_pool)

def get_by_id(table, id_column, id_value):
    """
    Get a record by ID.
    
    Args:
        table (str): The table name
        id_column (str): The ID column name
        id_value: The ID value
        
    Returns:
        dict: The record as a dictionary or None if not found
    """
    query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
        sql.Identifier(table),
        sql.Identifier(id_column)
    )
    return execute_query(query, (id_value,), fetch_one=True)

def get_all(table, order_by=None, order_direction='ASC', limit=None, offset=None):
    """
    Get all records from a table with optional ordering and pagination.
    
    Args:
        table (str): The table name
        order_by (str, optional): Column to order by
        order_direction (str): 'ASC' or 'DESC'
        limit (int, optional): Maximum number of records to return
        offset (int, optional): Number of records to skip
        
    Returns:
        list: A list of records as dictionaries
    """
    query_parts = [sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))]
    
    if order_by:
        query_parts.append(
            sql.SQL("ORDER BY {} {}").format(
                sql.Identifier(order_by),
                sql.SQL(order_direction)
            )
        )
    
    if limit:
        query_parts.append(sql.SQL("LIMIT %s"))
    
    if offset:
        query_parts.append(sql.SQL("OFFSET %s"))
    
    query = sql.SQL(" ").join(query_parts)
    
    params = []
    if limit:
        params.append(limit)
    if offset:
        params.append(offset)
    
    return execute_query(query, tuple(params) if params else None, fetch_all=True)

def insert(table, data):
    """
    Insert a new record into a table.
    
    Args:
        table (str): The table name
        data (dict): The data to insert as a dictionary
        
    Returns:
        The primary key of the inserted record
    """
    columns = list(data.keys())
    values = list(data.values())
    
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(', ').join(map(sql.Identifier, columns)),
        sql.SQL(', ').join(sql.Placeholder() * len(columns))
    )
    
    result = execute_query(query, values, fetch_one=True, commit=True)
    return result

def update(table, id_column, id_value, data):
    """
    Update a record in a table.
    
    Args:
        table (str): The table name
        id_column (str): The ID column name
        id_value: The ID value
        data (dict): The data to update as a dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    columns = list(data.keys())
    values = list(data.values())
    
    set_clause = sql.SQL(', ').join(
        sql.SQL("{} = %s").format(sql.Identifier(column)) 
        for column in columns
    )
    
    query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
        sql.Identifier(table),
        set_clause,
        sql.Identifier(id_column)
    )
    
    values.append(id_value)
    
    execute_query(query, values, commit=True)
    return True

def delete(table, id_column, id_value):
    """
    Delete a record from a table.
    
    Args:
        table (str): The table name
        id_column (str): The ID column name
        id_value: The ID value
        
    Returns:
        bool: True if successful, False otherwise
    """
    query = sql.SQL("DELETE FROM {} WHERE {} = %s").format(
        sql.Identifier(table),
        sql.Identifier(id_column)
    )
    
    execute_query(query, (id_value,), commit=True)
    return True

def count(table, where_clause=None, params=None):
    """
    Count records in a table.
    
    Args:
        table (str): The table name
        where_clause (str, optional): WHERE clause
        params (tuple, optional): Parameters for the WHERE clause
        
    Returns:
        int: The number of records
    """
    if where_clause:
        query = sql.SQL("SELECT COUNT(*) FROM {} WHERE {}").format(
            sql.Identifier(table),
            sql.SQL(where_clause)
        )
    else:
        query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table))
    
    result = execute_query(query, params, fetch_one=True)
    return result[0]

def search(table, columns, search_term, limit=None, offset=None):
    """
    Search for records in a table.
    
    Args:
        table (str): The table name
        columns (list): The columns to search in
        search_term (str): The search term
        limit (int, optional): Maximum number of records to return
        offset (int, optional): Number of records to skip
        
    Returns:
        list: A list of matching records as dictionaries
    """
    like_clauses = []
    for column in columns:
        like_clauses.append(
            sql.SQL("{} LIKE %s").format(sql.Identifier(column))
        )
    
    where_clause = sql.SQL(" OR ").join(like_clauses)
    
    query_parts = [
        sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)),
        sql.SQL("WHERE"),
        where_clause
    ]
    
    if limit:
        query_parts.append(sql.SQL("LIMIT %s"))
    
    if offset:
        query_parts.append(sql.SQL("OFFSET %s"))
    
    query = sql.SQL(" ").join(query_parts)
    
    # Prepare parameters with wildcards
    params = [f"%{search_term}%"] * len(columns)
    if limit:
        params.append(limit)
    if offset:
        params.append(offset)
    
    return execute_query(query, params, fetch_all=True)