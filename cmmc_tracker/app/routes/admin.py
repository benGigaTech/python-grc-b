"""Admin routes for the CMMC Tracker application."""

import logging
from datetime import date, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.task import Task
from app.services.database import execute_query
from app.utils.date import parse_date, format_date
from werkzeug.security import generate_password_hash
from app.services.email import check_and_notify_task_deadlines
from app.services.auth import admin_required

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def reports():
    """Generate compliance reports."""
    # Get filter parameters
    date_range = request.args.get('date_range', '30')
    
    # Calculate date ranges
    today = date.today()
    if date_range != 'all':
        future_date = today + timedelta(days=int(date_range))
    else:
        future_date = today + timedelta(days=365)
    
    try:
        # Overdue Tasks
        overdue_tasks = Task.get_overdue()
        
        # Convert to dictionaries and add days overdue
        overdue_tasks_data = []
        for task in overdue_tasks:
            task_dict = task.to_dict()
            days_until_due = task_dict['days_until_due']
            task_dict['days_overdue'] = abs(days_until_due) if days_until_due else 'N/A'
            overdue_tasks_data.append(task_dict)
        
        # Tasks by User with detailed breakdown
        users_query = 'SELECT username FROM users'
        users = execute_query(users_query, fetch_all=True)
        
        tasks_by_user_detailed = []
        for user in users:
            username = user['username']
            
            # Get task counts by status
            open_tasks = execute_query(
                'SELECT COUNT(*) FROM tasks WHERE assignedto = %s AND status = %s',
                (username, 'Open'),
                fetch_one=True
            )[0]
            
            pending_tasks = execute_query(
                'SELECT COUNT(*) FROM tasks WHERE assignedto = %s AND status = %s',
                (username, 'Pending Confirmation'),
                fetch_one=True
            )[0]
            
            completed_tasks = execute_query(
                'SELECT COUNT(*) FROM tasks WHERE assignedto = %s AND status = %s',
                (username, 'Completed'),
                fetch_one=True
            )[0]
            
            total_tasks = open_tasks + pending_tasks + completed_tasks
            
            if total_tasks > 0:  # Only include users with tasks
                tasks_by_user_detailed.append({
                    'username': username,
                    'open_tasks': open_tasks,
                    'pending_tasks': pending_tasks,
                    'completed_tasks': completed_tasks,
                    'total_tasks': total_tasks
                })
        
        # Sort by total tasks (descending)
        tasks_by_user_detailed.sort(key=lambda x: x['total_tasks'], reverse=True)
        
        # Upcoming Controls
        upcoming_controls_query = """
            SELECT * FROM controls
            WHERE nextreviewdate IS NOT NULL AND nextreviewdate != ''
            AND nextreviewdate > %s AND nextreviewdate <= %s
            ORDER BY nextreviewdate
        """
        upcoming_controls_db = execute_query(
            upcoming_controls_query,
            (today.isoformat(), future_date.isoformat()),
            fetch_all=True
        )
        
        # Convert to dictionaries and add days until
        upcoming_controls = []
        for control in upcoming_controls_db:
            control_dict = dict(control)
            
            review_date = parse_date(control_dict['nextreviewdate'])
            if review_date:
                control_dict['days_until'] = (review_date - today).days
            else:
                control_dict['days_until'] = 'N/A'
                
            upcoming_controls.append(control_dict)
        
        # Past Due Controls
        past_due_controls_query = """
            SELECT * FROM controls
            WHERE nextreviewdate IS NOT NULL AND nextreviewdate != ''
            AND nextreviewdate < %s
            ORDER BY nextreviewdate
        """
        past_due_controls_db = execute_query(
            past_due_controls_query,
            (today.isoformat(),),
            fetch_all=True
        )
        
        # Convert to dictionaries and add days since
        past_due_controls = []
        for control in past_due_controls_db:
            control_dict = dict(control)
            
            review_date = parse_date(control_dict['nextreviewdate'])
            if review_date:
                control_dict['days_since'] = (today - review_date).days
            else:
                control_dict['days_since'] = 'N/A'
                
            past_due_controls.append(control_dict)
        
        return render_template(
            'reports.html',
            overdue_tasks=overdue_tasks_data,
            tasks_by_user_detailed=tasks_by_user_detailed,
            upcoming_controls=upcoming_controls,
            past_due_controls=past_due_controls,
            date_range=date_range
        )
    
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        flash('An error occurred while generating reports.', 'danger')
        return redirect(url_for('controls.index'))

@admin_bp.route('/users')
@login_required
def admin_users():
    """Display list of users for administration."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('controls.index'))
    
    try:
        # Get all users
        users_query = 'SELECT userid, username, isadmin, email FROM users ORDER BY username'
        users = execute_query(users_query, fetch_all=True)
        
        return render_template('admin_users.html', users=users)
    
    except Exception as e:
        logger.error(f"Error accessing user list: {e}")
        flash('An error occurred while accessing the user list.', 'danger')
        return redirect(url_for('controls.index'))

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    """Create a new user."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('controls.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        is_admin = 1 if request.form.get('is_admin') else 0
        
        # Basic validation
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('admin_create_user.html')
        
        try:
            # Check if username already exists
            check_query = 'SELECT COUNT(*) FROM users WHERE username = %s'
            count = execute_query(check_query, (username,), fetch_one=True)[0]
            
            if count > 0:
                flash('Username already exists.', 'danger')
                return render_template('admin_create_user.html')
            
            # Create new user
            password_hash = generate_password_hash(password)
            insert_query = '''
                INSERT INTO users (username, password, isadmin, email)
                VALUES (%s, %s, %s, %s)
                RETURNING userid
            '''
            user_id = execute_query(
                insert_query, 
                (username, password_hash, is_admin, email),
                fetch_one=True,
                commit=True
            )[0]
            
            # Add audit log
            now = date.today().isoformat()
            audit_query = '''
                INSERT INTO auditlogs (timestamp, username, action, objecttype, objectid, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            execute_query(
                audit_query,
                (now, current_user.username, 'Create User', 'User', str(user_id), f'User {username} created'),
                commit=True
            )
            
            flash(f'User {username} created successfully.', 'success')
            return redirect(url_for('admin.admin_users'))
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            flash('An error occurred while creating the user.', 'danger')
            return render_template('admin_create_user.html')
    
    return render_template('admin_create_user.html')

@admin_bp.route('/notifications/send-test', methods=['POST'])
@login_required
@admin_required
def send_test_notifications():
    """
    Manually trigger task deadline email notifications.
    This is for testing purposes.
    """
    try:
        # Call the notification function
        notification_count = check_and_notify_task_deadlines()
        
        if notification_count > 0:
            flash(f'Successfully sent {notification_count} notifications', 'success')
        else:
            flash('No notifications were sent - there may be no tasks due soon or overdue', 'info')
        
        return redirect(url_for('admin.admin_users'))
    except Exception as e:
        logger.error(f"Error sending test notifications: {e}")
        flash('Error sending test notifications', 'error')
        return redirect(url_for('admin.admin_users'))