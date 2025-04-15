"""Evidence management routes for the CMMC Tracker application."""

import os
import logging
import magic
from datetime import date, timedelta # Add date and timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.services.settings import get_setting # Import get_setting
from app.models.evidence import Evidence
from app.models.control import Control
from app.services.audit import add_audit_log
from app.services.storage import save_evidence_file, get_evidence_file_path, delete_evidence_file
from app.utils.date import is_date_valid, format_date
from app import limiter
import math

logger = logging.getLogger(__name__)

# Create blueprint
evidence_bp = Blueprint('evidence', __name__)

def allowed_file(filename):
    """Check if a filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_file_type(file_stream):
    """Validate the file type using magic numbers and check against allowed MIME types."""
    try:
        # Read the first few bytes to determine the file type
        # Increasing buffer size for better detection of certain formats (e.g., docx)
        file_header = file_stream.read(2048)
        file_stream.seek(0) # Reset stream position after reading

        # Use python-magic to get the MIME type
        detected_mime_type = magic.from_buffer(file_header, mime=True)

        # Check if the detected MIME type is in the allowed list
        allowed_mime_types = current_app.config.get('ALLOWED_MIME_TYPES', set())
        if detected_mime_type in allowed_mime_types:
            logger.info(f"File type validated via magic number: {detected_mime_type}")
            return True, detected_mime_type
        else:
            logger.warning(f"File type validation failed. Detected MIME type: {detected_mime_type}, Allowed: {allowed_mime_types}")
            return False, detected_mime_type

    except Exception as e:
        logger.error(f"Error during file type validation: {e}")
        return False, None

def validate_file_type_path(file_path):
    """Validate the file type of a file on disk using magic numbers."""
    try:
        # Read the first few bytes to determine the file type
        with open(file_path, 'rb') as f:
            file_header = f.read(2048)

        # Use python-magic to get the MIME type
        detected_mime_type = magic.from_buffer(file_header, mime=True)

        # Check if the detected MIME type is in the allowed list
        allowed_mime_types = current_app.config.get('ALLOWED_MIME_TYPES', set())
        if detected_mime_type in allowed_mime_types:
            logger.info(f"File type validated via magic number: {detected_mime_type}")
            return True, detected_mime_type
        else:
            logger.warning(f"File type validation failed. Detected MIME type: {detected_mime_type}, Allowed: {allowed_mime_types}")
            return False, detected_mime_type

    except Exception as e:
        logger.error(f"Error during file type validation: {e}")
        return False, None

@evidence_bp.route('/control/<control_id>/evidence')
@login_required
def list_evidence(control_id):
    """Display evidence for a specific control."""
    try:
        # Verify control exists
        control = Control.get_by_id(control_id)
        if not control:
            flash('Control not found!', 'danger')
            return redirect(url_for('controls.index'))

        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        items_per_page = 5
        offset = (page - 1) * items_per_page

        # Sorting parameters
        sort_by = request.args.get('sort_by', 'uploaddate')
        sort_order = request.args.get('sort_order', 'desc')

        # Validate sort parameters
        valid_sort_columns = ['title', 'uploaddate', 'expirationdate', 'status']
        if sort_by not in valid_sort_columns:
            sort_by = 'uploaddate'

        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'

        # Get evidence for this control with pagination
        evidence_list = Evidence.get_by_control(
            control_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=items_per_page,
            offset=offset
        )

        # Convert to dictionaries for the template
        evidence_dicts = [evidence.to_dict() for evidence in evidence_list]

        # Get total count for pagination
        total_count = Evidence.count_by_control(control_id)
        total_pages = math.ceil(total_count / items_per_page) if total_count > 0 else 1

        return render_template(
            'evidence_list.html',
            control=control.to_dict(),
            evidence_list=evidence_dicts,
            page=page,
            total_pages=total_pages,
            sort_by=sort_by,
            sort_order=sort_order,
            total_count=total_count
        )

    except Exception as e:
        logger.error(f"Error listing evidence for control {control_id}: {e}")
        flash('An error occurred while retrieving evidence.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=control_id))

@evidence_bp.route('/control/<control_id>/evidence/add', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def add_evidence(control_id):
    """Add new evidence for a control."""
    try:
        # Verify control exists
        control = Control.get_by_id(control_id)
        if not control:
            flash('Control not found!', 'danger')
            return redirect(url_for('controls.index'))

        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            expiration_date = request.form.get('expiration_date', '')
            # Check if this is a chunked upload completion
            upload_session_id = request.form.get('upload_session_id', '')

            # Validate inputs
            if not title:
                flash('Evidence title is required.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())

            # Validate expiration date if provided
            if expiration_date and not is_date_valid(expiration_date):
                flash('Invalid expiration date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())

            # Handle file upload - either chunked or regular
            file_path = None
            saved_file_type = None
            file_size = None
            detected_mime = None

            if upload_session_id:
                # This is a chunked upload completion
                from app.services.chunked_upload import assemble_file, cleanup_session
                assembled_path, original_filename = assemble_file(upload_session_id)
                
                if not assembled_path:
                    flash('Failed to assemble uploaded file chunks.', 'danger')
                    return render_template('add_evidence.html', control=control.to_dict())
                
                # Validate the assembled file type
                is_valid_type, detected_mime = validate_file_type_path(assembled_path)
                if not is_valid_type:
                    cleanup_session(upload_session_id)
                    flash(f'File content validation failed. Detected type "{detected_mime}" is not allowed.', 'danger')
                    return render_template('add_evidence.html', control=control.to_dict())
                
                # Save the assembled file
                file_path, saved_file_type, file_size = save_evidence_file(
                    None, control_id, detected_mime, assembled_path
                )
                
                # Clean up the session directory (file has been copied to final location)
                cleanup_session(upload_session_id)
            else:
                # Regular file upload
                if 'evidence_file' not in request.files:
                    flash('No file selected.', 'danger')
                    return render_template('add_evidence.html', control=control.to_dict())

                file = request.files['evidence_file']
                if file.filename == '':
                    flash('No file selected.', 'danger')
                    return render_template('add_evidence.html', control=control.to_dict())

                # --- Enhanced File Validation ---
                # 1. Check extension first (quick check)
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else None
                if file_extension not in current_app.config['ALLOWED_EXTENSIONS']:
                    flash(f'File extension ".{file_extension}" not allowed. Allowed extensions: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}', 'danger')
                    return render_template('add_evidence.html', control=control.to_dict())

                # 2. Validate content using magic numbers
                is_valid_type, detected_mime = validate_file_type(file.stream)
                if not is_valid_type:
                    flash(f'File content validation failed. Detected type "{detected_mime}" is not allowed. Allowed MIME types: {", ".join(current_app.config.get("ALLOWED_MIME_TYPES", set()))}', 'danger')
                    return render_template('add_evidence.html', control=control.to_dict())
                # --- End Enhanced File Validation ---

                # Save the file (use detected_mime if available, otherwise fallback)
                file_path, saved_file_type, file_size = save_evidence_file(file, control_id, detected_mime or file.content_type)
            
            if not file_path:
                flash('Failed to save evidence file.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())

            # --- Calculate Expiration Date based on Settings ---
            final_expiration_date_str = None
            user_expiration_date_str = expiration_date # Already fetched from form on line 126

            enable_auto_expiration = get_setting('evidence.enable_auto_expiration', default=False)
            default_validity_days = get_setting('evidence.default_validity_days', default=365)

            if user_expiration_date_str:
                # Use user-provided date if valid
                if is_date_valid(user_expiration_date_str):
                     final_expiration_date_str = user_expiration_date_str
                else:
                    # Already flashed error earlier, just proceed without expiration
                    pass
            elif enable_auto_expiration:
                # Calculate default expiration if auto-expiration is enabled and user didn't provide one
                try:
                    # Convert to integer and validate it's positive
                    validity_days = int(default_validity_days)
                    if validity_days <= 0:
                        logger.warning(f"Invalid default_validity_days setting: {default_validity_days}. Value must be positive.")
                        flash('Warning: Could not apply automatic expiration date due to invalid settings. Contact your administrator.', 'warning')
                    else:
                        today = date.today()
                        calculated_expiration = today + timedelta(days=validity_days)
                        final_expiration_date_str = calculated_expiration.isoformat()
                except (ValueError, TypeError):
                    logger.error(f"Invalid default_validity_days setting: {default_validity_days}. Cannot calculate default expiration.")
                    flash('Warning: Could not apply automatic expiration date due to invalid settings. Contact your administrator.', 'warning')
                    # Proceed without expiration date if setting is invalid
            # --- End Expiration Date Calculation ---

            # Create evidence record using the final calculated/provided expiration date
            evidence = Evidence.create(
                control_id,
                title,
                description,
                file_path,
                saved_file_type,
                file_size,
                current_user.username,
                final_expiration_date_str # Use the processed date string
            )

            if evidence:
                # Log the action
                add_audit_log(
                    current_user.username,
                    'Create Evidence',
                    'Evidence',
                    evidence.evidence_id,
                    f"Added evidence '{title}' for control {control_id}"
                )

                flash('Evidence added successfully!', 'success')
                return redirect(url_for('evidence.list_evidence', control_id=control_id))
            else:
                flash('Failed to create evidence record.', 'danger')

        return render_template('add_evidence.html', control=control.to_dict())

    except Exception as e:
        logger.error(f"Error adding evidence for control {control_id}: {e}")
        flash('An error occurred while adding evidence.', 'danger')
        return redirect(url_for('evidence.list_evidence', control_id=control_id))

@evidence_bp.route('/evidence/<evidence_id>/download')
@login_required
@limiter.limit("30 per hour")
def download_evidence(evidence_id):
    """Download evidence file."""
    try:
        evidence = Evidence.get_by_id(evidence_id)
        if not evidence:
            flash('Evidence not found!', 'danger')
            return redirect(url_for('controls.index'))

        # Get the file path
        file_path = get_evidence_file_path(evidence.file_path)
        if not file_path:
            flash('Evidence file not found.', 'danger')
            return redirect(url_for('evidence.list_evidence', control_id=evidence.control_id))

        # Log the download
        add_audit_log(
            current_user.username,
            'Download Evidence',
            'Evidence',
            evidence_id,
            f"Downloaded evidence '{evidence.title}'"
        )

        # Determine the appropriate MIME type for the file
        mime_type = evidence.file_type

        # Return the file as an attachment
        return send_file(
            file_path,
            as_attachment=True,
            download_name=evidence.filename,
            mimetype=mime_type
        )

    except Exception as e:
        logger.error(f"Error downloading evidence {evidence_id}: {e}")
        flash('An error occurred while downloading the evidence file.', 'danger')
        return redirect(url_for('controls.index'))

@evidence_bp.route('/evidence/<evidence_id>/delete', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def delete_evidence(evidence_id):
    """Delete evidence."""
    try:
        evidence = Evidence.get_by_id(evidence_id)
        if not evidence:
            flash('Evidence not found!', 'danger')
            return redirect(url_for('controls.index'))

        control_id = evidence.control_id
        title = evidence.title

        # Delete the file from storage
        if evidence.file_path:
            delete_evidence_file(evidence.file_path)

        # Delete the database record
        if evidence.delete():
            # Log the action
            add_audit_log(
                current_user.username,
                'Delete Evidence',
                'Evidence',
                evidence_id,
                f"Deleted evidence '{title}' for control {control_id}"
            )

            flash('Evidence deleted successfully!', 'success')
        else:
            flash('Failed to delete evidence record.', 'danger')

        return redirect(url_for('evidence.list_evidence', control_id=control_id))

    except Exception as e:
        logger.error(f"Error deleting evidence {evidence_id}: {e}")
        flash('An error occurred while deleting evidence.', 'danger')
        return redirect(url_for('controls.index'))

@evidence_bp.route('/evidence/<evidence_id>/update', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def update_evidence(evidence_id):
    """Update evidence metadata."""
    try:
        evidence = Evidence.get_by_id(evidence_id)
        if not evidence:
            flash('Evidence not found!', 'danger')
            return redirect(url_for('controls.index'))

        control_id = evidence.control_id
        control = Control.get_by_id(control_id)

        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            expiration_date = request.form.get('expiration_date', '')
            status = request.form['status']

            # Validate inputs
            if not title:
                flash('Evidence title is required.', 'danger')
                return render_template('update_evidence.html', evidence=evidence.to_dict(), control=control.to_dict())

            # Validate expiration date if provided
            if expiration_date and not is_date_valid(expiration_date):
                flash('Invalid expiration date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('update_evidence.html', evidence=evidence.to_dict(), control=control.to_dict())

            # Update the evidence record
            evidence.title = title
            evidence.description = description
            evidence.expiration_date = format_date(expiration_date) if expiration_date else None
            evidence.status = status

            if evidence.update():
                # Log the action
                add_audit_log(
                    current_user.username,
                    'Update Evidence',
                    'Evidence',
                    evidence_id,
                    f"Updated evidence '{title}' for control {control_id}"
                )

                flash('Evidence updated successfully!', 'success')
                return redirect(url_for('evidence.list_evidence', control_id=control_id))
            else:
                flash('Failed to update evidence record.', 'danger')

        return render_template('update_evidence.html', evidence=evidence.to_dict(), control=control.to_dict())

    except Exception as e:
        logger.error(f"Error updating evidence {evidence_id}: {e}")
        flash('An error occurred while updating evidence.', 'danger')
        if evidence:
            return redirect(url_for('evidence.list_evidence', control_id=evidence.control_id))
        return redirect(url_for('controls.index'))
