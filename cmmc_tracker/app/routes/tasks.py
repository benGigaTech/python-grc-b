"""Task management routes for the CMMC Tracker application."""

import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.task import Task
from app.models.control import Control
from app.services.audit import add_audit_log
from app.services.email import send_task_notification
from app.utils.date import is_date_valid, format_date
from app.services.database import execute_query
from app.services.database import get_db_connection

# Remove the builtins import and use the Python standard library
import math  # For ceil function

logger = logging.getLogger(__name__)

# Create blueprint
tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/add_task/<control_id>', methods=['GET', 'POST'])
@login_required
def add_task(control_id):
    """Add a new task for a control."""
    # Verify control exists
    control = Control.get_by_id(control_id)
    if not control:
        flash('Control not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Get all users for task assignment
    users = execute_query('SELECT username FROM users', fetch_all=True)
    
    if request.method == 'POST':
        try:
            task_description = request.form['task_description']
            assigned_to = request.form['assigned_to']
            due_date_str = request.form['due_date']
            reviewer = request.form['reviewer']
            
            # Validate due date
            if not is_date_valid(due_date_str):
                flash('Invalid due date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('add_task.html', control_id=control_id, users=users)
            
            # Create the task
            task = Task.create(
                control_id,
                task_description,
                assigned_to,
                due_date_str,
                reviewer
            )
            
            if task:
                # Log the action
                add_audit_log(current_user.username, 'Create Task', 'Task', task.task_id)
                
                # Send email notification to the assignee
                send_task_notification(task.task_id, 'assigned')
                
                flash('Task added successfully!', 'success')
                return redirect(url_for('controls.control_detail', control_id=control_id))
            else:
                flash('An error occurred while adding the task.', 'danger')
                
        except Exception as e:
            logger.error(f"Error adding task for control {control_id}: {e}")
            flash('An error occurred while adding the task.', 'danger')
    
    return render_template('add_task.html', control_id=control_id, users=users)

@tasks_bp.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        flash('Task not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Enhanced IDOR protection: Check if current user is authorized to edit this task
    if not current_user.is_admin and task.assigned_to != current_user.username and task.reviewer != current_user.username:
        # Log unauthorized access attempt
        add_audit_log(
            current_user.username, 
            'Unauthorized Access Attempt', 
            'Task', 
            task_id, 
            f"Attempted to edit task assigned to {task.assigned_to}"
        )
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('controls.index'))
    
    # Get all users for task assignment
    users = execute_query('SELECT username FROM users', fetch_all=True)
    
    if request.method == 'POST':
        task.task_description = request.form['task_description']
        task.assigned_to = request.form['assigned_to']
        due_date_str = request.form['due_date']
        task.reviewer = request.form['reviewer']
        
        # Validate due date
        if not is_date_valid(due_date_str):
            flash('Invalid due date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('edit_task.html', task=task.to_dict(), users=users)
        
        # Format due date consistently
        task.due_date = format_date(due_date_str)
        
        if task.update():
            # Log the action
            add_audit_log(current_user.username, 'Edit Task', 'Task', task_id)
            flash('Task updated successfully!', 'success')
            return redirect(url_for('controls.control_detail', control_id=task.control_id))
        else:
            flash('An error occurred while updating the task.', 'danger')
    
    return render_template('edit_task.html', task=task.to_dict(), users=users)

@tasks_bp.route('/complete_task/<task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as complete (pending confirmation)."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        flash('Task not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Check if the current user is assigned to the task
    if task.assigned_to != current_user.username and not current_user.is_admin:
        flash('You can only complete tasks assigned to you.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=task.control_id))
    
    if task.status == 'Completed':
        flash('This task is already completed.', 'info')
        return redirect(url_for('controls.control_detail', control_id=task.control_id))
    
    if task.complete():
        # Log the action
        add_audit_log(current_user.username, 'Complete Task', 'Task', task_id)
        
        # Send email notification to the reviewer
        send_task_notification(task_id, 'completed')
        
        flash('Task marked as complete! Awaiting confirmation.', 'success')
    else:
        flash('An error occurred while completing the task.', 'danger')
    
    return redirect(url_for('controls.control_detail', control_id=task.control_id))

@tasks_bp.route('/confirm_task/<task_id>', methods=['POST'])
@login_required
def confirm_task(task_id):
    """Confirm a completed task."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        flash('Task not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Check if the current user is the reviewer for the task
    if task.reviewer != current_user.username and not current_user.is_admin:
        flash('You can only confirm tasks where you are the reviewer.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=task.control_id))
    
    if task.status != 'Pending Confirmation':
        flash('This task is not awaiting confirmation.', 'info')
        return redirect(url_for('controls.control_detail', control_id=task.control_id))
    
    if task.confirm():
        # Log the action
        add_audit_log(current_user.username, 'Confirm Task', 'Task', task_id)
        
        # Send email notification to the assignee
        send_task_notification(task_id, 'confirmed')
        
        flash('Task confirmed!', 'success')
    else:
        flash('An error occurred while confirming the task.', 'danger')
    
    return redirect(url_for('controls.control_detail', control_id=task.control_id))

@tasks_bp.route('/delete_task/<task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        flash('Task not found!', 'danger')
        return redirect(url_for('controls.index'))
    
    # Enhanced IDOR protection: Only allow admins or the creator to delete tasks
    if not current_user.is_admin:
        # Log unauthorized access attempt and deny access
        add_audit_log(
            current_user.username, 
            'Unauthorized Access Attempt', 
            'Task', 
            task_id, 
            "Attempted to delete task without admin privileges"
        )
        flash('Only administrators can delete tasks.', 'danger')
        return redirect(url_for('controls.control_detail', control_id=task.control_id))
    
    # Store control_id before deleting
    control_id = task.control_id
    
    if task.delete():
        # Log the action
        add_audit_log(current_user.username, 'Delete Task', 'Task', task_id)
        flash('Task deleted successfully!', 'success')
    else:
        flash('An error occurred while deleting the task.', 'danger')
    
    return redirect(url_for('controls.control_detail', control_id=control_id))

@tasks_bp.route('/statistics')
def statistics():
    """Display task statistics."""
    task_counts_query = """
    SELECT status, COUNT(*) as count, SUM(CASE WHEN duedate < CURRENT_DATE THEN 1 ELSE 0 END) as overdue
    FROM tasks
    GROUP BY status
    ORDER BY status
    """
    
    task_stats = []
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(task_counts_query)
        task_stats = cursor.fetchall()
        cursor.close()
        connection.close()
    except Exception as e:
        app.logger.error(f"Error fetching task statistics: {e}")
        flash("Unable to fetch task statistics.", "error")
    
    return render_template('task_statistics.html', task_stats=task_stats)

@tasks_bp.route('/calendar')
@login_required
def calendar():
    """Display a calendar view of controls and tasks."""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        controls_page = request.args.get('controls_page', 1, type=int)
        tasks_page = request.args.get('tasks_page', 1, type=int)
        items_per_page = 10
        
        # Get controls with review dates
        controls_count_query = "SELECT COUNT(*) FROM controls WHERE nextreviewdate IS NOT NULL AND nextreviewdate != ''"
        controls_count = execute_query(controls_count_query, fetch_one=True)[0]
        
        controls_query = '''
            SELECT * FROM controls 
            WHERE nextreviewdate IS NOT NULL AND nextreviewdate != '' 
            ORDER BY nextreviewdate 
            LIMIT %s OFFSET %s
        '''
        controls_offset = (controls_page - 1) * items_per_page
        controls_data = execute_query(controls_query, (items_per_page, controls_offset), fetch_all=True)
        
        # Get all tasks with pagination
        tasks_count_query = "SELECT COUNT(*) FROM tasks"
        tasks_count = execute_query(tasks_count_query, fetch_one=True)[0]
        
        tasks_query = '''
            SELECT * FROM tasks 
            ORDER BY duedate 
            LIMIT %s OFFSET %s
        '''
        tasks_offset = (tasks_page - 1) * items_per_page
        tasks_data = execute_query(tasks_query, (items_per_page, tasks_offset), fetch_all=True)
        
        # Process controls to add status (past-due, upcoming)
        from datetime import date, timedelta
        today = date.today()
        next_month = today + timedelta(days=30)
        
        controls_with_status = []
        for control in controls_data:
            if control['nextreviewdate']:
                review_date = format_date(control['nextreviewdate'])
                if review_date:
                    from app.utils.date import parse_date
                    review_date_obj = parse_date(review_date)
                    status = ""
                    if review_date_obj < today:
                        status = "past-due"
                    elif review_date_obj <= next_month:
                        status = "upcoming"
                    
                    controls_with_status.append({
                        'controlid': control['controlid'],
                        'controlname': control['controlname'],
                        'nextreviewdate': review_date,
                        'status': status
                    })
        
        # Get all controls for the calendar view (no pagination for the calendar itself)
        all_controls_query = "SELECT * FROM controls WHERE nextreviewdate IS NOT NULL AND nextreviewdate != ''"
        all_controls_data = execute_query(all_controls_query, fetch_all=True)
        
        all_controls_with_status = []
        for control in all_controls_data:
            if control['nextreviewdate']:
                review_date = format_date(control['nextreviewdate'])
                if review_date:
                    from app.utils.date import parse_date
                    review_date_obj = parse_date(review_date)
                    status = ""
                    if review_date_obj < today:
                        status = "past-due"
                    elif review_date_obj <= next_month:
                        status = "upcoming"
                    
                    all_controls_with_status.append({
                        'controlid': control['controlid'],
                        'controlname': control['controlname'],
                        'nextreviewdate': review_date,
                        'status': status
                    })
        
        # Calculate pagination metadata
        controls_total_pages = (controls_count + items_per_page - 1) // items_per_page
        tasks_total_pages = (tasks_count + items_per_page - 1) // items_per_page
        
        pagination = {
            'controls_page': controls_page,
            'controls_total_pages': controls_total_pages,
            'controls_count': controls_count,
            'tasks_page': tasks_page,
            'tasks_total_pages': tasks_total_pages,
            'tasks_count': tasks_count,
            'items_per_page': items_per_page
        }
        
        # Define utility functions for the template
        def template_max(a, b):
            return max(a, b)
            
        def template_min(a, b):
            return min(a, b)
        
        return render_template(
            'calendar.html', 
            controls=controls_with_status, 
            all_controls=all_controls_with_status,
            tasks=tasks_data, 
            pagination=pagination,
            max=template_max,  # Pass max function to template
            min=template_min   # Pass min function to template
        )
    
    except Exception as e:
        logger.error(f"Error loading calendar view: {e}")
        flash('An error occurred while loading the calendar.', 'danger')
        return redirect(url_for('controls.index'))