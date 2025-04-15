"""Service for handling chunked file uploads."""

import os
import logging
import uuid
import json
import shutil
from flask import current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def get_temp_upload_dir():
    """
    Get the directory for storing temporary chunked uploads.
    
    Returns:
        str: Path to the temporary upload directory
    """
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def create_upload_session():
    """
    Create a new upload session with a unique ID.
    
    Returns:
        str: Unique session ID for the upload
    """
    session_id = uuid.uuid4().hex
    session_dir = os.path.join(get_temp_upload_dir(), session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Create metadata file
    metadata = {
        'session_id': session_id,
        'chunks_received': 0,
        'total_chunks': 0,
        'filename': '',
        'complete': False
    }
    
    with open(os.path.join(session_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)
    
    return session_id

def save_chunk(session_id, chunk_index, total_chunks, file_chunk, original_filename=None):
    """
    Save a chunk of a file being uploaded.
    
    Args:
        session_id (str): The upload session ID
        chunk_index (int): The index of this chunk (0-based)
        total_chunks (int): The total number of chunks expected
        file_chunk: The file chunk data
        original_filename (str, optional): The original filename (only needed for first chunk)
        
    Returns:
        dict: Updated metadata for the upload session
    """
    try:
        session_dir = os.path.join(get_temp_upload_dir(), session_id)
        
        # Ensure session directory exists
        if not os.path.exists(session_dir):
            logger.error(f"Upload session {session_id} not found")
            return None
        
        # Load metadata
        try:
            with open(os.path.join(session_dir, 'metadata.json'), 'r') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            logger.error(f"Metadata for upload session {session_id} not found")
            return None
        
        # Update metadata if this is the first chunk
        if chunk_index == 0 and original_filename:
            metadata['filename'] = secure_filename(original_filename)
            metadata['total_chunks'] = total_chunks
        
        # Save the chunk
        chunk_path = os.path.join(session_dir, f'chunk_{chunk_index}')
        file_chunk.save(chunk_path)
        
        # Update metadata
        metadata['chunks_received'] += 1
        
        # Check if upload is complete
        if metadata['chunks_received'] >= metadata['total_chunks']:
            metadata['complete'] = True
        
        # Save updated metadata
        with open(os.path.join(session_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error saving chunk for session {session_id}: {e}")
        return None

def get_session_status(session_id):
    """
    Get the status of an upload session.
    
    Args:
        session_id (str): The upload session ID
        
    Returns:
        dict: Metadata for the upload session or None if not found
    """
    try:
        session_dir = os.path.join(get_temp_upload_dir(), session_id)
        
        # Ensure session directory exists
        if not os.path.exists(session_dir):
            logger.error(f"Upload session {session_id} not found")
            return None
        
        # Load metadata
        try:
            with open(os.path.join(session_dir, 'metadata.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Metadata for upload session {session_id} not found")
            return None
            
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {e}")
        return None

def assemble_file(session_id):
    """
    Assemble the complete file from chunks.
    
    Args:
        session_id (str): The upload session ID
        
    Returns:
        tuple: (assembled_file_path, original_filename) or (None, None) on failure
    """
    try:
        session_dir = os.path.join(get_temp_upload_dir(), session_id)
        
        # Ensure session directory exists
        if not os.path.exists(session_dir):
            logger.error(f"Upload session {session_id} not found")
            return None, None
        
        # Load metadata
        try:
            with open(os.path.join(session_dir, 'metadata.json'), 'r') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            logger.error(f"Metadata for upload session {session_id} not found")
            return None, None
        
        # Check if upload is complete
        if not metadata.get('complete', False):
            logger.error(f"Upload session {session_id} is not complete")
            return None, None
        
        # Create the assembled file
        original_filename = metadata.get('filename', f'upload_{session_id}')
        assembled_path = os.path.join(session_dir, original_filename)
        
        with open(assembled_path, 'wb') as outfile:
            # Combine all chunks in order
            for i in range(metadata.get('total_chunks', 0)):
                chunk_path = os.path.join(session_dir, f'chunk_{i}')
                if os.path.exists(chunk_path):
                    with open(chunk_path, 'rb') as infile:
                        outfile.write(infile.read())
                else:
                    logger.error(f"Missing chunk {i} for session {session_id}")
                    return None, None
        
        return assembled_path, original_filename
        
    except Exception as e:
        logger.error(f"Error assembling file for session {session_id}: {e}")
        return None, None

def cleanup_session(session_id, keep_assembled=False):
    """
    Clean up an upload session directory.
    
    Args:
        session_id (str): The upload session ID
        keep_assembled (bool): Whether to keep the assembled file
        
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    try:
        session_dir = os.path.join(get_temp_upload_dir(), session_id)
        
        # Ensure session directory exists
        if not os.path.exists(session_dir):
            logger.warning(f"Upload session {session_id} not found for cleanup")
            return True  # Consider it a success if already gone
        
        if keep_assembled:
            # Load metadata to get filename
            try:
                with open(os.path.join(session_dir, 'metadata.json'), 'r') as f:
                    metadata = json.load(f)
                    filename = metadata.get('filename')
                    
                # Move assembled file out of session directory
                if filename:
                    assembled_path = os.path.join(session_dir, filename)
                    if os.path.exists(assembled_path):
                        temp_path = os.path.join(get_temp_upload_dir(), filename)
                        shutil.move(assembled_path, temp_path)
                        logger.info(f"Preserved assembled file at {temp_path}")
            except Exception as e:
                logger.error(f"Error preserving assembled file: {e}")
        
        # Remove the session directory and all contents
        shutil.rmtree(session_dir)
        logger.info(f"Cleaned up upload session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}")
        return False
