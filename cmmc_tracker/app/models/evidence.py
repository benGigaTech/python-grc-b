"""Evidence model for the CMMC Tracker application."""

import logging
import os
from datetime import datetime, date
from app.services.database import get_by_id, insert, update, delete, execute_query, count
from app.utils.date import parse_date, format_date, is_date_valid

logger = logging.getLogger(__name__)

class Evidence:
    """Evidence model class for storing compliance evidence metadata."""
    
    def __init__(self, evidence_id, control_id, title, description=None, 
                 file_path=None, file_type=None, file_size=None, uploaded_by=None, 
                 upload_date=None, expiration_date=None, status="Current"):
        self.evidence_id = evidence_id
        self.control_id = control_id
        self.title = title
        self.description = description
        self.file_path = file_path
        self.file_type = file_type
        self.file_size = file_size
        self.uploaded_by = uploaded_by
        self.upload_date = upload_date
        self.expiration_date = expiration_date
        self.status = status
        self._control_name = None  # Lazy-loaded
    
    @property
    def control_name(self):
        """Get the associated control name (lazy-loaded)."""
        if self._control_name is None:
            query = "SELECT controlname FROM controls WHERE controlid = %s"
            result = execute_query(query, (self.control_id,), fetch_one=True)
            self._control_name = result['controlname'] if result else None
        return self._control_name
    
    @property
    def is_expired(self):
        """Check if the evidence has expired."""
        if not self.expiration_date:
            return False
        
        try:
            expiration = parse_date(self.expiration_date)
            return expiration < date.today()
        except ValueError:
            logger.error(f"Invalid expiration date format for evidence {self.evidence_id}")
            return False
    
    @property
    def filename(self):
        """Extract just the filename from the file path."""
        if not self.file_path:
            return None
        return os.path.basename(self.file_path)
    
    @classmethod
    def get_by_id(cls, evidence_id):
        """
        Get evidence by ID.
        
        Args:
            evidence_id: The evidence ID
            
        Returns:
            Evidence: An Evidence object or None if not found
        """
        evidence_data = get_by_id('evidence', 'evidenceid', evidence_id)
        if evidence_data:
            return cls(
                evidence_data['evidenceid'],
                evidence_data['controlid'],
                evidence_data['title'],
                evidence_data['description'],
                evidence_data['filepath'],
                evidence_data['filetype'],
                evidence_data['filesize'],
                evidence_data['uploadedby'],
                evidence_data['uploaddate'],
                evidence_data['expirationdate'],
                evidence_data['status']
            )
        return None
    
    @classmethod
    def get_by_control(cls, control_id, sort_by='uploaddate', sort_order='desc', limit=None, offset=None):
        """
        Get evidence for a specific control.
        
        Args:
            control_id: The control ID
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            list: A list of Evidence objects
        """
        query = f"""
            SELECT * FROM evidence
            WHERE controlid = %s
            ORDER BY {sort_by} {sort_order.upper()}
            {"LIMIT %s" if limit else ""}
            {"OFFSET %s" if offset else ""}
        """
        
        params = [control_id]
        if limit:
            params.append(limit)
        if offset:
            params.append(offset)
            
        evidence_data_list = execute_query(query, tuple(params), fetch_all=True)
        
        return [
            cls(
                data['evidenceid'],
                data['controlid'],
                data['title'],
                data['description'],
                data['filepath'],
                data['filetype'],
                data['filesize'],
                data['uploadedby'],
                data['uploaddate'],
                data['expirationdate'],
                data['status']
            ) for data in evidence_data_list
        ]
    
    @classmethod
    def count_by_control(cls, control_id):
        """
        Count evidence for a specific control.
        
        Args:
            control_id: The control ID
            
        Returns:
            int: The number of evidence items
        """
        return count('evidence', 'controlid = %s', (control_id,))
    
    @classmethod
    def get_expired(cls):
        """
        Get all expired evidence.
        
        Returns:
            list: A list of expired Evidence objects
        """
        today = date.today().isoformat()
        query = """
            SELECT * FROM evidence 
            WHERE expirationdate IS NOT NULL 
            AND expirationdate != '' 
            AND expirationdate < %s
            ORDER BY expirationdate
        """
        evidence_data_list = execute_query(query, (today,), fetch_all=True)
        
        return [
            cls(
                data['evidenceid'],
                data['controlid'],
                data['title'],
                data['description'],
                data['filepath'],
                data['filetype'],
                data['filesize'],
                data['uploadedby'],
                data['uploaddate'],
                data['expirationdate'],
                data['status']
            ) for data in evidence_data_list
        ]
    
    @classmethod
    def create(cls, control_id, title, description, file_path, file_type, file_size, 
               uploaded_by, expiration_date=None):
        """
        Create a new evidence record.
        
        Args:
            control_id: The control ID
            title: The evidence title
            description: The evidence description
            file_path: Path to the stored file
            file_type: The file MIME type
            file_size: Size of the file in bytes
            uploaded_by: Username of the uploader
            expiration_date: Optional expiration date
            
        Returns:
            Evidence: The created Evidence object or None if creation failed
        """
        try:
            # Format date consistently
            upload_date = format_date(date.today().isoformat())
            formatted_expiration = format_date(expiration_date) if expiration_date else None
            
            evidence_data = insert('evidence', {
                'controlid': control_id,
                'title': title,
                'description': description,
                'filepath': file_path,
                'filetype': file_type,
                'filesize': file_size,
                'uploadedby': uploaded_by,
                'uploaddate': upload_date,
                'expirationdate': formatted_expiration,
                'status': 'Current'
            })
            
            if evidence_data:
                return cls(
                    evidence_data['evidenceid'],
                    evidence_data['controlid'],
                    evidence_data['title'],
                    evidence_data['description'],
                    evidence_data['filepath'],
                    evidence_data['filetype'],
                    evidence_data['filesize'],
                    evidence_data['uploadedby'],
                    evidence_data['uploaddate'],
                    evidence_data['expirationdate'],
                    evidence_data['status']
                )
            return None
        except Exception as e:
            logger.error(f"Error creating evidence: {e}")
            return None
    
    def update(self):
        """
        Update evidence in the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update('evidence', 'evidenceid', self.evidence_id, {
                'controlid': self.control_id,
                'title': self.title,
                'description': self.description,
                'filepath': self.file_path,
                'filetype': self.file_type,
                'filesize': self.file_size,
                'uploadedby': self.uploaded_by,
                'uploaddate': self.upload_date,
                'expirationdate': self.expiration_date,
                'status': self.status
            })
            return True
        except Exception as e:
            logger.error(f"Error updating evidence: {e}")
            return False
    
    def delete(self):
        """
        Delete evidence from the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            delete('evidence', 'evidenceid', self.evidence_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting evidence: {e}")
            return False
    
    def to_dict(self):
        """
        Convert the Evidence object to a dictionary for templates.
        
        Returns:
            dict: A dictionary representation of the evidence
        """
        return {
            'evidenceid': self.evidence_id,
            'controlid': self.control_id,
            'title': self.title,
            'description': self.description,
            'filepath': self.file_path,
            'filetype': self.file_type,
            'filesize': self.file_size,
            'uploadedby': self.uploaded_by,
            'uploaddate': self.upload_date,
            'expirationdate': self.expiration_date,
            'status': self.status,
            'filename': self.filename,
            'is_expired': self.is_expired,
            'control_name': self.control_name
        } 