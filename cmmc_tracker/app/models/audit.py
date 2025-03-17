"""Audit log model for the CMMC Tracker application."""

import logging
from datetime import datetime, timezone
from app.services.database import insert, execute_query

logger = logging.getLogger(__name__)

class AuditLog:
    """Audit log model class."""
    
    def __init__(self, log_id, timestamp, username, action, object_type, object_id=None, details=None):
        self.log_id = log_id
        self.timestamp = timestamp
        self.username = username
        self.action = action
        self.object_type = object_type
        self.object_id = object_id
        self.details = details

    @classmethod
    def get_by_id(cls, log_id):
        """
        Get an audit log entry by ID.
        
        Args:
            log_id: The log ID
            
        Returns:
            AuditLog: An AuditLog object or None if not found
        """
        query = "SELECT * FROM auditlogs WHERE logid = %s"
        log_data = execute_query(query, (log_id,), fetch_one=True)
        
        if log_data:
            return cls(
                log_data['logid'],
                log_data['timestamp'],
                log_data['username'],
                log_data['action'],
                log_data['objecttype'],
                log_data['objectid'],
                log_data['details']
            )
        return None

    @classmethod
    def get_by_object(cls, object_type, object_id, limit=None):
        """
        Get audit logs for a specific object.
        
        Args:
            object_type: The object type (e.g. 'Control', 'Task', 'User')
            object_id: The object ID
            limit: Maximum number of records to return
            
        Returns:
            list: A list of AuditLog objects
        """
        query = """
            SELECT * FROM auditlogs 
            WHERE objecttype = %s AND objectid = %s 
            ORDER BY timestamp DESC
            {"LIMIT %s" if limit else ""}
        """
        
        params = [object_type, object_id]
        if limit:
            params.append(limit)
            
        log_data_list = execute_query(query, tuple(params), fetch_all=True)
        
        return [
            cls(
                data['logid'],
                data['timestamp'],
                data['username'],
                data['action'],
                data['objecttype'],
                data['objectid'],
                data['details']
            ) for data in log_data_list
        ]

    @classmethod
    def get_by_user(cls, username, limit=None):
        """
        Get audit logs for a specific user.
        
        Args:
            username: The username
            limit: Maximum number of records to return
            
        Returns:
            list: A list of AuditLog objects
        """
        query = """
            SELECT * FROM auditlogs 
            WHERE username = %s 
            ORDER BY timestamp DESC
            {"LIMIT %s" if limit else ""}
        """
        
        params = [username]
        if limit:
            params.append(limit)
            
        log_data_list = execute_query(query, tuple(params), fetch_all=True)
        
        return [
            cls(
                data['logid'],
                data['timestamp'],
                data['username'],
                data['action'],
                data['objecttype'],
                data['objectid'],
                data['details']
            ) for data in log_data_list
        ]

    @classmethod
    def get_recent(cls, limit=100):
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            list: A list of AuditLog objects
        """
        query = "SELECT * FROM auditlogs ORDER BY timestamp DESC LIMIT %s"
        log_data_list = execute_query(query, (limit,), fetch_all=True)
        
        return [
            cls(
                data['logid'],
                data['timestamp'],
                data['username'],
                data['action'],
                data['objecttype'],
                data['objectid'],
                data['details']
            ) for data in log_data_list
        ]

    @classmethod
    def add_entry(cls, username, action, object_type, object_id=None, details=None):
        """
        Add a new audit log entry.
        
        Args:
            username: The username
            action: The action performed
            object_type: The object type
            object_id: The object ID
            details: Additional details
            
        Returns:
            AuditLog: The created AuditLog object or None if creation failed
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            log_data = insert('auditlogs', {
                'timestamp': timestamp,
                'username': username,
                'action': action,
                'objecttype': object_type,
                'objectid': object_id,
                'details': details
            })
            
            return cls(
                log_data['logid'],
                log_data['timestamp'],
                log_data['username'],
                log_data['action'],
                log_data['objecttype'],
                log_data['objectid'],
                log_data['details']
            )
        except Exception as e:
            logger.error(f"Error adding audit log entry: {e}")
            return None

    def to_dict(self):
        """
        Convert the audit log entry to a dictionary.
        
        Returns:
            dict: A dictionary representation of the audit log entry
        """
        return {
            'logid': self.log_id,
            'timestamp': self.timestamp,
            'username': self.username,
            'action': self.action,
            'objecttype': self.object_type,
            'objectid': self.object_id,
            'details': self.details
        }