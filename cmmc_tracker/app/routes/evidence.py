"""Evidence management routes for the CMMC Tracker application."""

import os
import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.evidence import Evidence
from app.models.control import Control
from app.services.audit import add_audit_log
from app.services.storage import save_evidence_file, get_evidence_file_path, delete_evidence_file
from app.utils.date import is_date_valid, format_date
import math

logger = logging.getLogger(__name__)

# Create blueprint
evidence_bp = Blueprint('evidence', __name__)

def allowed_file(filename):
    """Check if a filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

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
            
            # Validate inputs
            if not title:
                flash('Evidence title is required.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())
                
            # Validate expiration date if provided
            if expiration_date and not is_date_valid(expiration_date):
                flash('Invalid expiration date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())
            
            # Check if file was uploaded
            if 'evidence_file' not in request.files:
                flash('No file selected.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())
                
            file = request.files['evidence_file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())
                
            if not allowed_file(file.filename):
                flash(f'File type not allowed. Allowed types: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())
            
            # Save the file
            file_path, file_type, file_size = save_evidence_file(file, control_id)
            if not file_path:
                flash('Failed to save evidence file.', 'danger')
                return render_template('add_evidence.html', control=control.to_dict())
            
            # Create evidence record
            evidence = Evidence.create(
                control_id,
                title,
                description,
                file_path,
                file_type,
                file_size,
                current_user.username,
                expiration_date
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