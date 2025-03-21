"""Storage service for the CMMC Tracker application."""

import os
import logging
import uuid
import shutil
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

def get_evidence_upload_dir():
    """
    Get the directory for storing evidence files.
    
    Returns:
        str: Path to the evidence upload directory
    """
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'evidence')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def save_evidence_file(file, control_id):
    """
    Save an uploaded evidence file to disk.
    
    Args:
        file: The uploaded file object
        control_id: The ID of the control this evidence is for
        
    Returns:
        tuple: (file_path, file_type, file_size) or (None, None, None) on failure
    """
    try:
        if not file:
            return None, None, None
            
        # Secure the filename and add a UUID to prevent name collisions
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        unique_filename = f"{unique_id}_{filename}"
        
        # Create a subdirectory for each control to organize files
        control_dir = os.path.join(get_evidence_upload_dir(), control_id)
        if not os.path.exists(control_dir):
            os.makedirs(control_dir, exist_ok=True)
        
        # Determine file path
        file_path = os.path.join(control_dir, unique_filename)
        relative_path = os.path.join('evidence', control_id, unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        file_type = file.content_type or 'application/octet-stream'
        
        logger.info(f"Saved evidence file: {file_path}")
        return relative_path, file_type, file_size
        
    except Exception as e:
        logger.error(f"Error saving evidence file: {e}")
        return None, None, None

def get_evidence_file_path(relative_path):
    """
    Get the full file path for a stored evidence file.
    
    Args:
        relative_path: The relative path stored in the database
        
    Returns:
        str: Full file path or None if invalid
    """
    if not relative_path:
        return None
    
    # Ensure the path is relative to the upload folder
    if relative_path.startswith('/'):
        relative_path = relative_path[1:]
    
    # Build the full path
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
    
    # Validate the path (security check)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.normpath(full_path).startswith(os.path.normpath(upload_folder)):
        logger.warning(f"Attempted to access file outside upload folder: {relative_path}")
        return None
    
    if not os.path.exists(full_path):
        logger.warning(f"Evidence file not found: {full_path}")
        return None
    
    return full_path

def delete_evidence_file(relative_path):
    """
    Delete an evidence file from disk.
    
    Args:
        relative_path: The relative path stored in the database
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        full_path = get_evidence_file_path(relative_path)
        if full_path and os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted evidence file: {full_path}")
            
            # Clean up empty directories
            dir_path = os.path.dirname(full_path)
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
                logger.info(f"Removed empty directory: {dir_path}")
                
            return True
            
        logger.warning(f"Could not delete evidence file (not found): {relative_path}")
        return False
    except Exception as e:
        logger.error(f"Error deleting evidence file: {e}")
        return False 