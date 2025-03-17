"""Audit service for logging user actions."""

import logging
from flask import current_app
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

def add_audit_log(username, action, object_type, object_id=None, details=None):
    """
    Add an entry to the audit log.
    
    Args:
        username (str): The username of the user who performed the action
        action (str): The action performed (e.g., 'Create', 'Update', 'Delete')
        object_type (str): The type of object affected (e.g., 'User', 'Control', 'Task')
        object_id (str, optional): The ID of the object affected
        details (str, optional): Additional details about the action
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        AuditLog.add_entry(username, action, object_type, object_id, details)
        logger.info(f"Audit log added: {username} - {action} - {object_type} - {object_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to add audit log: {e}")
        return False

def get_audit_logs_for_object(object_type, object_id, limit=50):
    """
    Get audit logs for a specific object.
    
    Args:
        object_type (str): The type of object
        object_id (str): The ID of the object
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: List of AuditLog objects
    """
    try:
        return AuditLog.get_by_object(object_type, object_id, limit)
    except Exception as e:
        logger.error(f"Failed to get audit logs for {object_type} {object_id}: {e}")
        return []

def get_audit_logs_for_user(username, limit=50):
    """
    Get audit logs for a specific user.
    
    Args:
        username (str): The username
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: List of AuditLog objects
    """
    try:
        return AuditLog.get_by_user(username, limit)
    except Exception as e:
        logger.error(f"Failed to get audit logs for user {username}: {e}")
        return []

def get_recent_audit_logs(limit=100):
    """
    Get recent audit logs.
    
    Args:
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: List of AuditLog objects
    """
    try:
        return AuditLog.get_recent(limit)
    except Exception as e:
        logger.error(f"Failed to get recent audit logs: {e}")
        return []