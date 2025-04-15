"""Routes for handling chunked file uploads."""

import os
import logging
import magic
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.chunked_upload import (
    create_upload_session, save_chunk, get_session_status,
    assemble_file, cleanup_session
)
from app.services.audit import add_audit_log

logger = logging.getLogger(__name__)

# Create blueprint
chunked_upload_bp = Blueprint('chunked_upload', __name__)

def validate_file_type(file_path):
    """Validate the file type using magic numbers and check against allowed MIME types."""
    try:
        # Read the first few bytes to determine the file type
        with open(file_path, 'rb') as f:
            file_header = f.read(2048)
        
        # Use python-magic to get the MIME type
        detected_mime_type = magic.from_buffer(file_header, mime=True)
        
        # Check if the detected MIME type is allowed
        allowed_mime_types = current_app.config.get('ALLOWED_MIME_TYPES', set())
        is_allowed = detected_mime_type in allowed_mime_types
        
        return is_allowed, detected_mime_type
        
    except Exception as e:
        logger.error(f"Error validating file type: {e}")
        return False, None

@chunked_upload_bp.route('/api/upload/create-session', methods=['POST'])
@login_required
def create_session():
    """Create a new chunked upload session."""
    try:
        # Create a new upload session
        session_id = create_upload_session()
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Failed to create upload session'
            }), 500
        
        # Log the action
        add_audit_log(
            current_user.username,
            'Create Upload Session',
            'System',
            session_id,
            f"Created chunked upload session {session_id}"
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'chunk_size': current_app.config.get('CHUNK_SIZE', 2 * 1024 * 1024)  # Default 2MB
        })
        
    except Exception as e:
        logger.error(f"Error creating upload session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chunked_upload_bp.route('/api/upload/chunk/<session_id>', methods=['POST'])
@login_required
def upload_chunk(session_id):
    """Upload a chunk of a file."""
    try:
        # Get chunk information from request
        chunk_index = int(request.form.get('chunk_index', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        original_filename = request.form.get('filename', '')
        
        # Check if file chunk was uploaded
        if 'file_chunk' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file chunk provided'
            }), 400
        
        file_chunk = request.files['file_chunk']
        if file_chunk.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty file chunk'
            }), 400
        
        # Save the chunk
        metadata = save_chunk(
            session_id,
            chunk_index,
            total_chunks,
            file_chunk,
            original_filename if chunk_index == 0 else None
        )
        
        if not metadata:
            return jsonify({
                'success': False,
                'error': 'Failed to save chunk'
            }), 500
        
        # Return the updated status
        return jsonify({
            'success': True,
            'chunks_received': metadata.get('chunks_received', 0),
            'total_chunks': metadata.get('total_chunks', 0),
            'complete': metadata.get('complete', False)
        })
        
    except Exception as e:
        logger.error(f"Error uploading chunk: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chunked_upload_bp.route('/api/upload/status/<session_id>', methods=['GET'])
@login_required
def check_status(session_id):
    """Check the status of an upload session."""
    try:
        # Get session status
        metadata = get_session_status(session_id)
        
        if not metadata:
            return jsonify({
                'success': False,
                'error': 'Upload session not found'
            }), 404
        
        # Return the status
        return jsonify({
            'success': True,
            'session_id': session_id,
            'chunks_received': metadata.get('chunks_received', 0),
            'total_chunks': metadata.get('total_chunks', 0),
            'filename': metadata.get('filename', ''),
            'complete': metadata.get('complete', False)
        })
        
    except Exception as e:
        logger.error(f"Error checking upload status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chunked_upload_bp.route('/api/upload/complete/<session_id>', methods=['POST'])
@login_required
def complete_upload(session_id):
    """Complete an upload by assembling the chunks."""
    try:
        # Assemble the file
        assembled_path, original_filename = assemble_file(session_id)
        
        if not assembled_path:
            return jsonify({
                'success': False,
                'error': 'Failed to assemble file'
            }), 500
        
        # Validate the assembled file
        is_valid, detected_mime = validate_file_type(assembled_path)
        if not is_valid:
            # Clean up the session
            cleanup_session(session_id)
            return jsonify({
                'success': False,
                'error': f'File type validation failed. Detected type "{detected_mime}" is not allowed.'
            }), 400
        
        # Log the action
        add_audit_log(
            current_user.username,
            'Complete Upload',
            'System',
            session_id,
            f"Completed chunked upload for file {original_filename}"
        )
        
        # Return success with file information
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': original_filename,
            'file_path': assembled_path,
            'mime_type': detected_mime
        })
        
    except Exception as e:
        logger.error(f"Error completing upload: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chunked_upload_bp.route('/api/upload/cancel/<session_id>', methods=['POST'])
@login_required
def cancel_upload(session_id):
    """Cancel an upload and clean up the session."""
    try:
        # Clean up the session
        success = cleanup_session(session_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to clean up upload session'
            }), 500
        
        # Log the action
        add_audit_log(
            current_user.username,
            'Cancel Upload',
            'System',
            session_id,
            f"Cancelled chunked upload session {session_id}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Upload cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling upload: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
