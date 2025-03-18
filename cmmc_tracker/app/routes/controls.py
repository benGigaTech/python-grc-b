"""Control management routes for the CMMC Tracker application."""

import logging
from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, Response, jsonify
from flask_login import login_required, current_user
from app.models.control import Control
from app.models.task import Task
from app.models.user import User
from app.services.audit import add_audit_log, get_audit_logs_for_object
from app.utils.date import is_date_valid, format_date, parse_date, is_past_date
from app.services.database import execute_query
from app.services.auth import admin_required
import csv
import io

logger = logging.getLogger(__name__)

# Create blueprint
controls_bp = Blueprint('controls', __name__)

@controls_bp.route('/dashboard')
@login_required
def dashboard():
    """Display the dashboard with compliance metrics and visualizations."""
    try:
        # Get system date
        today = date.today()
        
        # Calculate control metrics
        control_total_query = "SELECT COUNT(*) FROM controls"
        control_total = execute_query(control_total_query, fetch_one=True)[0]
        
        # Get counts for compliance status
        compliant_query = "SELECT COUNT(*) FROM controls WHERE controlid IN (SELECT DISTINCT controlid FROM tasks WHERE status = 'Completed' AND confirmed = 1)"
        compliant = execute_query(compliant_query, fetch_one=True)[0]
        
        in_progress_query = "SELECT COUNT(*) FROM controls WHERE controlid IN (SELECT DISTINCT controlid FROM tasks WHERE status IN ('Open', 'Pending Confirmation'))"
        in_progress = execute_query(in_progress_query, fetch_one=True)[0]
        
        # Assume controls with no tasks are not assessed
        not_assessed_query = "SELECT COUNT(*) FROM controls WHERE controlid NOT IN (SELECT DISTINCT controlid FROM tasks)"
        not_assessed = execute_query(not_assessed_query, fetch_one=True)[0]
        
        # Calculate non-compliant as remainder
        non_compliant = control_total - compliant - in_progress - not_assessed
        if non_compliant < 0:
            non_compliant = 0
        
        # Get upcoming reviews (next 30 days)
        thirty_days_later = (today + timedelta(days=30)).isoformat()
        upcoming_reviews_query = """
            SELECT COUNT(*) FROM controls 
            WHERE nextreviewdate IS NOT NULL AND nextreviewdate != '' 
            AND nextreviewdate BETWEEN %s AND %s
        """
        upcoming_reviews = execute_query(upcoming_reviews_query, (today.isoformat(), thirty_days_later), fetch_one=True)[0]
        
        # Calculate task metrics
        open_tasks_query = "SELECT COUNT(*) FROM tasks WHERE status = 'Open'"
        open_tasks = execute_query(open_tasks_query, fetch_one=True)[0]
        
        in_progress_tasks_query = "SELECT COUNT(*) FROM tasks WHERE status = 'Pending Confirmation'"
        in_progress_tasks = execute_query(in_progress_tasks_query, fetch_one=True)[0]
        
        completed_tasks_query = "SELECT COUNT(*) FROM tasks WHERE status = 'Completed'"
        completed_tasks = execute_query(completed_tasks_query, fetch_one=True)[0]
        
        overdue_tasks_query = """
            SELECT COUNT(*) FROM tasks 
            WHERE status != 'Completed' AND duedate IS NOT NULL AND duedate != '' 
            AND duedate < %s
        """
        overdue_tasks = execute_query(overdue_tasks_query, (today.isoformat(),), fetch_one=True)[0]
        
        # Get recent activities related to tasks and controls only (last 10)
        recent_activities_query = """
            SELECT * FROM auditlogs 
            WHERE objecttype IN ('control', 'task')
            AND action IN ('created', 'updated', 'deleted', 'completed', 'confirmed')
            ORDER BY logid DESC 
            LIMIT 10
        """
        recent_activities = execute_query(recent_activities_query, fetch_all=True)
        
        # Get user's tasks (max 10)
        my_tasks_query = """
            SELECT t.taskid as task_id, 
                   t.controlid as control_id, 
                   t.taskdescription as task_description, 
                   t.duedate as due_date, 
                   t.status, 
                   CASE WHEN t.duedate < %s AND t.status != 'Completed' THEN 1 ELSE 0 END as is_overdue
            FROM tasks t
            WHERE t.assignedto = %s AND t.status != 'Completed'
            ORDER BY t.duedate ASC NULLS LAST
            LIMIT 10
        """
        my_tasks = execute_query(my_tasks_query, (today.isoformat(), current_user.username), fetch_all=True)
        
        # Compile metrics
        control_metrics = {
            'total': control_total,
            'compliant': compliant,
            'in_progress': in_progress,
            'non_compliant': non_compliant,
            'not_assessed': not_assessed,
            'upcoming_reviews': upcoming_reviews
        }
        
        task_metrics = {
            'open': open_tasks,
            'in_progress': in_progress_tasks,
            'completed': completed_tasks,
            'overdue': overdue_tasks,
            'pending': open_tasks + in_progress_tasks
        }
        
        return render_template(
            'dashboard.html',
            control_metrics=control_metrics,
            task_metrics=task_metrics,
            recent_activities=recent_activities,
            my_tasks=my_tasks
        )
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        flash('An error occurred while generating the dashboard.', 'danger')
        return redirect(url_for('controls.index'))

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
        
        # Convert tasks to dictionaries for the template
        tasks_dicts = [task.to_dict() for task in tasks]
        
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
            tasks=tasks_dicts,
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

@controls_bp.route('/export-csv')
@login_required
def export_csv():
    """Export controls to CSV."""
    try:
        # Get all controls
        controls = Control.get_all()
        
        if not controls:
            flash('No controls to export', 'error')
            return redirect(url_for('controls.index'))
        
        # Create a CSV string
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Control ID', 'Control Name', 'Control Description', 'NIST Mapping', 
                         'Review Frequency', 'Last Review Date', 'Next Review Date'])
        
        # Write data
        for control in controls:
            writer.writerow([
                control.control_id,
                control.control_name,
                control.control_description,
                control.nist_mapping,
                control.review_frequency,
                format_date(control.last_review_date) if control.last_review_date else '',
                format_date(control.next_review_date) if control.next_review_date else ''
            ])
        
        # Create the response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename=cmmc_controls_export_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
        return response
    except Exception as e:
        logger.error(f"Error exporting controls: {e}")
        flash('Error exporting controls', 'error')
        return redirect(url_for('controls.index'))

@controls_bp.route('/import-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def import_csv():
    """Import controls from CSV."""
    if request.method == 'GET':
        return render_template('import_controls.html')
    
    try:
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if not file.filename.endswith('.csv'):
            flash('File must be a CSV', 'error')
            return redirect(request.url)
        
        # Process the CSV file
        csv_content = file.read().decode('utf-8')
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        imported_count = 0
        updated_count = 0
        error_count = 0
        
        for row in reader:
            try:
                # Check if control exists
                existing_control = Control.get_by_id(row['Control ID'])
                
                # Format dates correctly
                last_review_date = parse_date(row.get('Last Review Date', '')) if row.get('Last Review Date') else None
                next_review_date = parse_date(row.get('Next Review Date', '')) if row.get('Next Review Date') else None
                
                # Create control object
                control = Control(
                    control_id=row['Control ID'],
                    control_name=row['Control Name'],
                    control_description=row.get('Control Description', ''),
                    nist_mapping=row.get('NIST Mapping', ''),
                    review_frequency=row.get('Review Frequency', ''),
                    last_review_date=last_review_date,
                    next_review_date=next_review_date
                )
                
                if existing_control:
                    # Update existing control
                    control.save()
                    updated_count += 1
                else:
                    # Insert new control
                    control.save()
                    imported_count += 1
            except Exception as e:
                logger.error(f"Error importing row {row}: {e}")
                error_count += 1
        
        if error_count:
            flash(f'Imported {imported_count} new controls, updated {updated_count} existing controls with {error_count} errors', 'warning')
        else:
            flash(f'Successfully imported {imported_count} new controls and updated {updated_count} existing controls', 'success')
        
        return redirect(url_for('controls.index'))
    except Exception as e:
        logger.error(f"Error importing controls: {e}")
        flash('Error importing controls', 'error')
        return redirect(url_for('controls.index'))

@controls_bp.route('/edit_control_family/<family_id>', methods=['GET', 'POST'])
@login_required
def edit_control_family(family_id):
    """Edit a control family."""
    control_family = Control.get_by_id(family_id)
    
    if control_family is None:
        flash('Control family not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    if request.method == 'POST':
        control_family.family_name = request.form['family_name']
        control_family.description = request.form['description']
        
        if control_family.update():
            # Log the action
            add_audit_log(current_user.username, 'Edit Control Family', 'Control Family', family_id)
            flash('Control family updated successfully!', 'success')
            return redirect(url_for('controls.control_family_detail', family_id=family_id))
        else:
            flash('An error occurred while updating the control family.', 'danger')
    
    return render_template('edit_control_family.html', control_family=control_family.to_dict())

@controls_bp.route('/delete_control_family/<family_id>', methods=['POST'])
@login_required
def delete_control_family(family_id):
    """Delete a control family."""
    # Only admins can delete control families
    if not current_user.is_admin:
        flash('You do not have permission to delete control families.', 'danger')
        return redirect(url_for('controls.control_family_detail', family_id=family_id))
    
    control_family = Control.get_by_id(family_id)
    
    if control_family is None:
        flash('Control family not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Delete the control family
    if control_family.delete():
        # Log the action
        add_audit_log(current_user.username, 'Delete Control Family', 'Control Family', family_id)
        flash('Control family deleted successfully!', 'success')
        return redirect(url_for('controls.index'))
    else:
        flash('An error occurred while deleting the control family.', 'danger')
        return redirect(url_for('controls.control_family_detail', family_id=family_id))

@controls_bp.route('/update_control_family/<family_id>', methods=['POST'])
@login_required
def update_control_family(family_id):
    """Update control family."""
    control_family = Control.get_by_id(family_id)
    
    if control_family is None:
        flash('Control family not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    control_family.family_name = request.form['family_name']
    control_family.description = request.form['description']
    
    if control_family.update():
        # Log the action
        add_audit_log(current_user.username, 'Update Control Family', 'Control Family', family_id)
        flash('Control family updated successfully!', 'success')
        return redirect(url_for('controls.control_family_detail', family_id=family_id))
    else:
        flash('An error occurred while updating the control family.', 'danger')
        return redirect(url_for('controls.edit_control_family', family_id=family_id))