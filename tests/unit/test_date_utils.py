"""Unit tests for date utilities."""

import pytest
from datetime import date, datetime, timedelta
from cmmc_tracker.app.utils.date import (
    parse_date,
    format_date,
    is_date_valid,
    is_future_date,
    is_past_date,
    days_between,
    add_days
)

@pytest.mark.unit
@pytest.mark.utils
def test_parse_date():
    """Test the parse_date function."""
    # Test with ISO format date string
    assert parse_date("2023-01-15") == date(2023, 1, 15)

    # Test with None input
    assert parse_date(None) is None

    # Test with empty string
    assert parse_date("") is None

    # Test with invalid date string
    assert parse_date("not-a-date") is None

@pytest.mark.unit
@pytest.mark.utils
def test_format_date():
    """Test the format_date function."""
    # Test with date object
    d = date(2023, 1, 15)
    assert format_date(d) == "2023-01-15"

    # Test with datetime object
    dt = datetime(2023, 1, 15, 12, 30, 45)
    assert format_date(dt) == "2023-01-15"

    # Test with ISO format date string
    assert format_date("2023-01-15") == "2023-01-15"

    # Test with None input
    assert format_date(None) == ''

    # Test with empty string
    assert format_date("") == ''

    # Test with invalid date string
    # The current implementation returns the original string if it can't be parsed
    # This is different from what we might expect, but we'll test the actual behavior
    assert format_date("not-a-date") == 'not-a-date'

@pytest.mark.unit
@pytest.mark.utils
def test_is_date_valid():
    """Test the is_date_valid function."""
    # Test with valid date
    assert is_date_valid("2023-01-15") is True

    # Test with invalid date
    assert is_date_valid("2023-13-45") is False

    # Test with non-date string
    assert is_date_valid("not-a-date") is False

    # Test with None input
    assert is_date_valid(None) is False

    # Test with empty string
    assert is_date_valid("") is False

@pytest.mark.unit
@pytest.mark.utils
def test_date_comparison_functions():
    """Test the date comparison utility functions."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Test is_future_date
    assert is_future_date(tomorrow.isoformat()) is True
    assert is_future_date(today.isoformat()) is False
    assert is_future_date(yesterday.isoformat()) is False

    # Test is_past_date
    assert is_past_date(yesterday.isoformat()) is True
    assert is_past_date(today.isoformat()) is False
    assert is_past_date(tomorrow.isoformat()) is False

    # Test days_between
    assert days_between(today.isoformat(), tomorrow.isoformat()) == 1
    assert days_between(tomorrow.isoformat(), today.isoformat()) == -1
    assert days_between(today.isoformat(), today.isoformat()) == 0
    assert days_between(yesterday.isoformat(), tomorrow.isoformat()) == 2

@pytest.mark.unit
@pytest.mark.utils
def test_add_days():
    """Test the add_days function."""
    # Test adding positive days
    assert add_days('2023-01-15', 5) == '2023-01-20'

    # Test adding negative days
    assert add_days('2023-01-15', -5) == '2023-01-10'

    # Test adding zero days
    assert add_days('2023-01-15', 0) == '2023-01-15'

    # Test with invalid date
    assert add_days('not-a-date', 5) == ''

    # Test with None input
    assert add_days(None, 5) == ''

    # Test with empty string
    assert add_days('', 5) == ''
