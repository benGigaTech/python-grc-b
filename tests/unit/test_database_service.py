"""Unit tests for the database service."""

import pytest
from cmmc_tracker.app.services.database import execute_query, get_by_id, insert, update, delete

@pytest.mark.unit
@pytest.mark.services
def test_execute_query(init_database):
    """Test the execute_query function."""
    # Test SELECT query with fetch_one
    result = execute_query("SELECT 1 as test", fetch_one=True)
    assert result is not None
    assert result['test'] == 1

    # Test SELECT query with fetch_all
    results = execute_query("SELECT 1 as test UNION SELECT 2 as test", fetch_all=True)
    assert results is not None
    assert len(results) == 2
    assert results[0]['test'] in [1, 2]
    assert results[1]['test'] in [1, 2]

    # Test INSERT query
    execute_query(
        "INSERT INTO controls (controlid, controlname) VALUES (%s, %s)",
        ('TEST.DB.001', 'Database Test Control'),
        commit=True
    )

    # Verify the insert worked
    result = execute_query(
        "SELECT controlname FROM controls WHERE controlid = %s",
        ('TEST.DB.001',),
        fetch_one=True
    )
    assert result is not None
    assert result['controlname'] == 'Database Test Control'

    # Test UPDATE query
    execute_query(
        "UPDATE controls SET controlname = %s WHERE controlid = %s",
        ('Updated Database Test Control', 'TEST.DB.001'),
        commit=True
    )

    # Verify the update worked
    result = execute_query(
        "SELECT controlname FROM controls WHERE controlid = %s",
        ('TEST.DB.001',),
        fetch_one=True
    )
    assert result is not None
    assert result['controlname'] == 'Updated Database Test Control'

    # Test DELETE query
    execute_query(
        "DELETE FROM controls WHERE controlid = %s",
        ('TEST.DB.001',),
        commit=True
    )

    # Verify the delete worked
    result = execute_query(
        "SELECT controlname FROM controls WHERE controlid = %s",
        ('TEST.DB.001',),
        fetch_one=True
    )
    assert result is None

@pytest.mark.unit
@pytest.mark.services
@pytest.mark.skip(reason="Requires database connection, will be tested in integration tests")
def test_get_by_id(init_database):
    """Test the get_by_id function."""
    # This test requires a database connection and will be tested in integration tests
    pass

@pytest.mark.unit
@pytest.mark.services
@pytest.mark.skip(reason="Requires database connection, will be tested in integration tests")
def test_insert_update_delete(init_database):
    """Test the insert, update, and delete functions."""
    # This test requires a database connection and will be tested in integration tests
    pass
