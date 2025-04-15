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

def save_evidence_file(file, control_id, detected_mime_type=None, assembled_file_path=None):
    """
    Save an uploaded evidence file to disk.

    Args:
        file: The uploaded file object or None if using assembled_file_path
        control_id: The ID of the control this evidence is for
        detected_mime_type (str, optional): MIME type detected by magic number validation.
                                          Defaults to None.
        assembled_file_path (str, optional): Path to an already assembled file from chunked upload.
                                           If provided, 'file' parameter is ignored.

    Returns:
        tuple: (relative_path, file_type, file_size) or (None, None, None) on failure
    """
    try:
        if not file and not assembled_file_path:
            return None, None, None

        # Handle regular file upload or assembled file
        if assembled_file_path:
            # For assembled files, extract the original filename from the path
            original_filename = os.path.basename(assembled_file_path)
            file_content_type = detected_mime_type or 'application/octet-stream'
        else:
            # For regular uploads, use the file object
            original_filename = file.filename
            file_content_type = file.content_type or 'application/octet-stream'

        # Secure the filename and add a UUID to prevent name collisions
        filename = secure_filename(original_filename)
        unique_id = uuid.uuid4().hex
        unique_filename = f"{unique_id}_{filename}"

        # Create a subdirectory for each control to organize files
        control_dir = os.path.join(get_evidence_upload_dir(), control_id)
        if not os.path.exists(control_dir):
            os.makedirs(control_dir, exist_ok=True)

        # Determine file path
        dest_file_path = os.path.join(control_dir, unique_filename)
        relative_path = os.path.join('evidence', control_id, unique_filename)

        # Save the file - either copy from assembled path or save from upload
        if assembled_file_path:
            shutil.copy2(assembled_file_path, dest_file_path)
        else:
            # Use streaming approach for regular uploads to reduce memory usage
            with open(dest_file_path, 'wb') as out_file:
                file.save(out_file)

        # Get file metadata
        file_size = os.path.getsize(dest_file_path)
        # Use detected MIME type if available and valid, otherwise fallback to browser-provided type
        file_type = detected_mime_type if detected_mime_type else file_content_type

        logger.info(f"Saved evidence file: {dest_file_path} (Type: {file_type}, Size: {file_size} bytes)")
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