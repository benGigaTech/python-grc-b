"""Control management routes for the CMMC Tracker application."""

import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.control import Control
from app.models.user import User
from app.services.audit import add_audit_log
from app.utils.date import is_date_valid, format_date, parse_date, is_past_date
from app.services.database import execute_query

logger = logging.getLogger(__name__)

# Create blueprint
controls_bp = Blueprint('controls', __name__)

@controls_bp.route('/')
@login_required
def index():
    """Display the list of controls."""
    # Get query parameters
    sort_by = request.args.get('sort_by', 'controlid')
    sort_order = request.args.get('sort_order', 'asc')
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('q', '')
    
    # Validate sort parameters
    valid_sort_columns = ['controlid', 'controlname', 'nextreviewdate']
    if sort_by not in valid_sort_columns:
        sort_by = 'controlid'
    
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'
    
    # Pagination parameters
    items_per_page = 10
    offset = (page - 1) * items_per_page
    
    # Get controls
    if search_term:
        # Search for controls
        controls_data = execute_query(
            """
            SELECT * FROM controls
            WHERE controlid LIKE %s OR controlname LIKE %s OR controldescription LIKE %s
            ORDER BY {} {}
            LIMIT %s OFFSET %s
            """.format(sort_by, sort_order.upper()),
            (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', items_per_page, offset),
            fetch_all=True
        )
        
        # Get total count for pagination
        total_count = execute_query(
            """
            SELECT COUNT(*) FROM controls
            WHERE controlid LIKE %s OR controlname LIKE %s OR controldescription LIKE %s
            """,
            (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'),
            fetch_one=True
        )[0]
    else:
        # Get all controls
        controls_data = execute_query(
            f"SELECT * FROM controls ORDER BY {sort_by} {sort_order.upper()} LIMIT %s OFFSET %s",
            (items_per_page, offset),
            fetch_all=True
        )
        
        # Get total count for pagination
        total_count = execute_query(
            "SELECT COUNT(*) FROM controls",
            fetch_one=True
        )[0]
    
    # Calculate total pages
    total_pages = (total_count + items_per_page - 1) // items_per_page
    
    return render_template(
        'index.html',
        controls=controls_data,
        search_term=search_term,
        page=page,
        total_pages=total_pages,
        sort_by=sort_by,
        sort_order=sort_order
    )

@controls_bp.route('/control/<control_id>')
@login_required
def control_detail(control_id):
    """Display details for a specific control."""
    logger.debug(f"Entering control_detail route with control_id: {control_id}")
    
    try:
        # Fetch control data
        control = Control.get_by_id(control_id)
        
        if control is None:
            logger.warning(f"No control found for control_id: {control_id}")
            flash('Control not found.', 'danger')
            return redirect(url_for('controls.index'))
        
        # Pagination parameters
        items_per_page = 5  # Number of tasks per page
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * items_per_page
        
        # Sorting parameters
        sort_by = request.args.get('sort_by', 'duedate')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Validate sort parameters
        valid_sort_columns = ['duedate', 'assignedto', 'status']
        if sort_by not in valid_sort_columns:
            sort_by = 'duedate'
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'asc'
        
        # Get tasks for this control
        tasks = control.get_tasks(
            sort_by=sort_by,
            sort_order=sort_order,
            limit=items_per_page,
            offset=offset
        )
        
        # Get total count of tasks for pagination
        total_count = control.count_tasks()
        
        # Get all users for task assignment
        users = execute_query(
            'SELECT username FROM users',
            fetch_all=True
        )
        
        # Calculate total pages
        total_pages = (total_count + items_per_page - 1) // items_per_page
        
        return render_template(
            'control_detail.html',
            control=control.to_dict(),
            tasks=tasks,
            users=users,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            total_pages=total_pages
        )
    
    except Exception as e:
        logger.error(f"Error in control_detail: {e}")
        flash('An error occurred while retrieving control details.', 'danger')
        return redirect(url_for('controls.index'))

@controls_bp.route('/create_control', methods=['GET', 'POST'])
@login_required
def create_control():
    """Create a new control."""
    if request.method == 'POST':
        control_id = request.form['control_id']
        control_name = request.form['control_name']
        control_description = request.form['control_description']
        nist_mapping = request.form['nist_mapping']
        review_frequency = request.form['review_frequency']
        
        # Check if control ID already exists
        existing_control = Control.get_by_id(control_id)
        if existing_control:
            flash('Control ID already exists. Please choose a different ID.', 'danger')
            return render_template('create_control.html')
        
        # Create the control
        control = Control.create(
            control_id,
            control_name,
            control_description,
            nist_mapping,
            review_frequency
        )
        
        if control:
            # Log the action
            add_audit_log(current_user.username, 'Create Control', 'Control', control_id)
            flash('Control created successfully!', 'success')
            return redirect(url_for('controls.index'))
        else:
            flash('An error occurred while creating the control.', 'danger')
    
    return render_template('create_control.html')

@controls_bp.route('/edit_control/<control_id>', methods=['GET', 'POST'])
@login_required
def edit_control(control_id):
    """Edit an existing control."""
    control = Control.get_by_id(control_id)
    
    if control is None:
        flash('Control not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    if request.method == 'POST':
        control.control_name = request.form['control_name']
        control.control_description = request.form['control_description']
        control.nist_mapping = request.form['nist_mapping']
        control.review_frequency = request.form['review_frequency']
        
        if control.update():
            # Log the action
            add_audit_log(current_user.username, 'Edit Control', 'Control', control_id)
            flash('Control updated successfully!', 'success')
            return redirect(url_for('controls.control_detail', control_id=control_id))
        else:
            flash('An error occurred while updating the control.', 'danger')
    
    return render_template('edit_control.html', control=control.to_dict())

@controls_bp.route('/delete_control/<control_id>', methods=['POST'])
@login_required
def delete_control(control_id):
    """Delete a control."""
    # Only admins can delete controls
    if not current_user.is_admin:
        flash('You do not have permission to delete controls.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=control_id))
    
    control = Control.get_by_id(control_id)
    
    if control is None:
        flash('Control not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Check for associated tasks
    tasks = control.get_tasks()
    
    if tasks:
        flash('Cannot delete control because it has associated tasks.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=control_id))
    
    # Delete the control
    if control.delete():
        # Log the action
        add_audit_log(current_user.username, 'Delete Control', 'Control', control_id)
        flash('Control deleted successfully!', 'success')
        return redirect(url_for('controls.index'))
    else:
        flash('An error occurred while deleting the control.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=control_id))

@controls_bp.route('/update_review_dates/<control_id>', methods=['POST'])
@login_required
def update_review_dates(control_id):
    """Update review dates for a control."""
    control = Control.get_by_id(control_id)
    
    if control is None:
        flash('Control not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    last_review_date_str = request.form['last_review_date']
    next_review_date_str = request.form['next_review_date']
    
    # Validate dates
    if last_review_date_str and not is_date_valid(last_review_date_str):
        flash('Invalid last review date format. Please use YYYY-MM-DD.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=control_id))
        
    if next_review_date_str and not is_date_valid(next_review_date_str):
        flash('Invalid next review date format. Please use YYYY-MM-DD.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=control_id))
    
    # Warn if next review date is in the past
    if next_review_date_str and is_past_date(next_review_date_str):
        flash('Warning: Next review date is in the past.', 'warning')
    
    # Update review dates
    if control.update_review_dates(last_review_date_str, next_review_date_str):
        # Log the action
        add_audit_log(current_user.username, 'Update Review Dates', 'Control', control_id)
        flash('Review dates updated successfully!', 'success')
    else:
        flash('An error occurred while updating review dates.', 'danger')
    
    return redirect(url_for('controls.control_detail', control_id=control_id))