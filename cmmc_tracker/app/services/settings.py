"""Settings service for the CMMC Tracker application."""

import logging
from flask import current_app
from app.services.database import execute_query
import json

logger = logging.getLogger(__name__)

# Cache settings to reduce database queries
_settings_cache = {}

def _get_setting_from_db(setting_key):
    """Get a setting value from database."""
    try:
        query = """
            SELECT setting_value, setting_type 
            FROM settings 
            WHERE setting_key = %s
        """
        result = execute_query(query, (setting_key,), fetch_one=True)
        
        if not result:
            logger.warning(f"Setting '{setting_key}' not found in database")
            return None
            
        return result
    except Exception as e:
        logger.error(f"Error getting setting '{setting_key}': {e}")
        return None

def _convert_value_to_type(value, setting_type):
    """Convert string value to appropriate Python type."""
    if value is None:
        return None
        
    if setting_type == 'boolean':
        return value.lower() in ('true', 'yes', '1', 'on')
    elif setting_type == 'integer':
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.error(f"Failed to convert '{value}' to integer")
            return 0
    elif setting_type == 'float':
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.error(f"Failed to convert '{value}' to float")
            return 0.0
    elif setting_type == 'json':
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse '{value}' as JSON")
            return {}
    else:  # 'string' or any other type
        return value

def get_setting(setting_key, default=None):
    """
    Get a setting value by key.
    
    Args:
        setting_key (str): The setting key
        default: Default value if setting not found
        
    Returns:
        The setting value with appropriate type conversion
    """
    # Check cache first
    if setting_key in _settings_cache:
        return _settings_cache[setting_key]
    
    # Get from database
    result = _get_setting_from_db(setting_key)
    
    if not result:
        return default
        
    value = result['setting_value']
    setting_type = result['setting_type']
    
    # Convert to appropriate type
    converted_value = _convert_value_to_type(value, setting_type)
    
    # Update cache
    _settings_cache[setting_key] = converted_value
    
    return converted_value

def update_setting(setting_key, value, username=None):
    """
    Update a setting value.
    
    Args:
        setting_key (str): The setting key
        value: The new value (will be converted to string)
        username (str, optional): Username of the user making the change
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # If value is boolean, convert to string 'true'/'false'
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
        # If value is None, store as NULL
        elif value is None:
            str_value = None
        # If value is a dict or list, convert to JSON string
        elif isinstance(value, (dict, list)):
            str_value = json.dumps(value)
        else:
            str_value = str(value)
            
        # Update the setting in the database
        query = """
            UPDATE settings
            SET setting_value = %s,
                last_updated = CURRENT_TIMESTAMP,
                updated_by = %s
            WHERE setting_key = %s
        """
        execute_query(query, (str_value, username, setting_key), commit=True)
        
        # Clear the cache for this setting
        if setting_key in _settings_cache:
            del _settings_cache[setting_key]
            
        logger.info(f"Setting '{setting_key}' updated to '{str_value}' by '{username}'")
        return True
        
    except Exception as e:
        logger.error(f"Error updating setting '{setting_key}': {e}")
        return False

def get_settings_by_prefix(prefix):
    """
    Get all settings with keys starting with the given prefix.
    
    Args:
        prefix (str): The prefix to filter settings by
        
    Returns:
        dict: Dictionary of settings with their values
    """
    try:
        query = """
            SELECT setting_key, setting_value, setting_type, description
            FROM settings
            WHERE setting_key LIKE %s
            ORDER BY setting_key
        """
        results = execute_query(query, (f"{prefix}%",), fetch_all=True)
        
        settings = {}
        for row in results:
            key = row['setting_key']
            value = _convert_value_to_type(row['setting_value'], row['setting_type'])
            settings[key] = {
                'value': value,
                'type': row['setting_type'],
                'description': row['description']
            }
            
        return settings
        
    except Exception as e:
        logger.error(f"Error getting settings with prefix '{prefix}': {e}")
        return {}

def get_all_settings():
    """
    Get all settings with their values and metadata.
    
    Returns:
        dict: Dictionary with setting categories as keys
    """
    try:
        query = """
            SELECT setting_key, setting_value, setting_type, description, last_updated, updated_by
            FROM settings
            ORDER BY setting_key
        """
        results = execute_query(query, fetch_all=True)
        
        # Group settings by category (first part of the key)
        categories = {}
        for row in results:
            key = row['setting_key']
            category = key.split('.')[0] if '.' in key else 'other'
            
            if category not in categories:
                categories[category] = {}
                
            setting_name = key.split('.', 1)[1] if '.' in key else key
            
            categories[category][setting_name] = {
                'key': key,
                'value': _convert_value_to_type(row['setting_value'], row['setting_type']),
                'type': row['setting_type'],
                'description': row['description'],
                'last_updated': row['last_updated'],
                'updated_by': row['updated_by']
            }
            
        return categories
        
    except Exception as e:
        logger.error(f"Error getting all settings: {e}")
        return {}

def clear_cache():
    """Clear the settings cache."""
    global _settings_cache
    _settings_cache = {}
    logger.info("Settings cache cleared") 