"""Database service for the CMMC Tracker application."""

import logging
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import sql
from flask import current_app

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establish a new database connection.
    
    Returns:
        Connection: A PostgreSQL database connection
    """
    try:
        conn = psycopg2.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            database=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD']
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

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
        if conn:
            conn.close()

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