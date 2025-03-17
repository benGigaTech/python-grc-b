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
    
    # Store control_id before deleting
    control_id = task.control_id
    
    if task.delete():
        # Log the action
        add_audit_log(current_user.username, 'Delete Task', 'Task', task_id)
        flash('Task deleted successfully!', 'success')
    else:
        flash('An error occurred while deleting the task.', 'danger')
    
    return redirect(url_for('controls.control_detail', control_id=control_id))

@tasks_bp.route('/calendar')
@login_required
def calendar():
    """Display a calendar view of controls and tasks."""
    try:
        # Get controls with review dates
        controls_query = 'SELECT * FROM controls WHERE nextreviewdate IS NOT NULL AND nextreviewdate != \'\''
        controls_data = execute_query(controls_query, fetch_all=True)
        
        # Get all tasks
        tasks_query = 'SELECT * FROM tasks'
        tasks_data = execute_query(tasks_query, fetch_all=True)
        
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
        
        return render_template('calendar.html', controls=controls_with_status, tasks=tasks_data)
    
    except Exception as e:
        logger.error(f"Error loading calendar view: {e}")
        flash('An error occurred while loading the calendar.', 'danger')
        return redirect(url_for('controls.index'))