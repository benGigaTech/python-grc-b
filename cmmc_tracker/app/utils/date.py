"""Date utility functions for the CMMC Tracker application."""

from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

def parse_date(date_str):
    """
    Parse a date string into a date object.
    Returns None if the date string is invalid or empty.
    
    Args:
        date_str (str): A date string in YYYY-MM-DD format
        
    Returns:
        date: A date object or None if invalid
    """
    if not date_str or date_str.strip() == '':
        return None
        
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}")
        return None

def format_date(date_obj):
    """
    Format a date object into a standardized string (YYYY-MM-DD).
    Returns empty string if date_obj is None or invalid.
    
    Args:
        date_obj (date or str): A date object or date string
        
    Returns:
        str: Formatted date string or empty string if invalid
    """
    if not date_obj:
        return ''
        
    try:
        if isinstance(date_obj, str):
            # If it's already a string, try to parse and format it
            parsed = parse_date(date_obj)
            return parsed.strftime('%Y-%m-%d') if parsed else date_obj
        return date_obj.strftime('%Y-%m-%d')
    except (AttributeError, ValueError):
        logger.warning(f"Failed to format date: {date_obj}")
        return ''

def is_date_valid(date_str):
    """
    Check if a date string is valid.
    
    Args:
        date_str (str): A date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return parse_date(date_str) is not None

def is_future_date(date_str):
    """
    Check if a date string represents a future date.
    
    Args:
        date_str (str): A date string to check
        
    Returns:
        bool: True if future date, False otherwise
    """
    parsed = parse_date(date_str)
    return parsed is not None and parsed > date.today()

def is_past_date(date_str):
    """
    Check if a date string represents a past date.
    
    Args:
        date_str (str): A date string to check
        
    Returns:
        bool: True if past date, False otherwise
    """
    parsed = parse_date(date_str)
    return parsed is not None and parsed < date.today()

def days_between(start_date_str, end_date_str):
    """
    Calculate the number of days between two date strings.
    
    Args:
        start_date_str (str): Start date in YYYY-MM-DD format
        end_date_str (str): End date in YYYY-MM-DD format
        
    Returns:
        int: Number of days between dates or None if invalid
    """
    start = parse_date(start_date_str)
    end = parse_date(end_date_str)
    
    if start and end:
        return (end - start).days
    return None

def add_days(date_str, days):
    """
    Add a specified number of days to a date string.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        days (int): Number of days to add (can be negative)
        
    Returns:
        str: New date string or empty string if invalid
    """
    parsed = parse_date(date_str)
    if parsed:
        new_date = parsed + timedelta(days=days)
        return format_date(new_date)
    return ''