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
from app.services.audit import add_audit_log, get_recent_audit_logs
from app.utils.security import is_password_strong

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
        
        # Get site activity logs
        site_activity = get_recent_audit_logs(limit=15)
            
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
        
        # Convert to dictionaries and add days overdue
        past_due_controls = []
        for control in past_due_controls_db:
            next_review = parse_date(control['nextreviewdate'])
            days_overdue = (today - next_review).days if next_review else None
            
            past_due_controls.append({
                'id': control['controlid'],
                'name': control['controlname'],
                'next_review': format_date(control['nextreviewdate']),
                'days_overdue': days_overdue
            })
        
        return render_template(
            'admin_dashboard.html',
            overdue_tasks=overdue_tasks_data,
            tasks_by_user_detailed=tasks_by_user_detailed,
            site_activity=site_activity,
            past_due_controls=past_due_controls,
            date_range=date_range
        )
    except Exception as e:
        logger.error(f"Error generating admin dashboard: {e}")
        flash('An error occurred while generating the dashboard.', 'danger')
        return redirect(url_for('controls.dashboard'))

@admin_bp.route('/users')
@login_required
def users():
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
def create_user():
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
        
        # Validate password strength
        if not is_password_strong(password):
            flash('Password is not strong enough. It must be at least 8 characters and include uppercase, lowercase, numbers, and special characters.', 'danger')
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
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            flash('An error occurred while creating the user.', 'danger')
            return render_template('admin_create_user.html')
    
    return render_template('admin_create_user.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    """Edit an existing user."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('controls.index'))
    
    try:
        # Get user details
        user_query = 'SELECT userid, username, isadmin, email FROM users WHERE userid = %s'
        user = execute_query(user_query, (user_id,), fetch_one=True)
        
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('admin.users'))
        
        if request.method == 'POST':
            # Get form data
            email = request.form.get('email')
            is_admin = 1 if request.form.get('is_admin') else 0
            new_password = request.form.get('password')
            
            # Validate password strength if a new password is provided
            if new_password and not is_password_strong(new_password):
                flash('Password is not strong enough. It must be at least 8 characters and include uppercase, lowercase, numbers, and special characters.', 'danger')
                return render_template('admin_edit_user.html', user=user)
            
            # Update user
            if new_password:
                # Update with new password
                password_hash = generate_password_hash(new_password)
                update_query = '''
                    UPDATE users
                    SET email = %s, isadmin = %s, password = %s
                    WHERE userid = %s
                '''
                execute_query(
                    update_query,
                    (email, is_admin, password_hash, user_id),
                    commit=True
                )
                
                log_message = f"User {user['username']} updated (including password)"
            else:
                # Update without changing password
                update_query = '''
                    UPDATE users
                    SET email = %s, isadmin = %s
                    WHERE userid = %s
                '''
                execute_query(
                    update_query,
                    (email, is_admin, user_id),
                    commit=True
                )
                
                log_message = f"User {user['username']} updated (no password change)"
            
            # Add audit log
            now = date.today().isoformat()
            add_audit_log(
                current_user.username,
                'Update User',
                'User',
                str(user_id),
                log_message
            )
            
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        
        return render_template('admin_edit_user.html', user=user)
            
    except Exception as e:
        logger.error(f"Error editing user: {e}")
        flash('An error occurred while editing the user.', 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete a user."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('controls.index'))
    
    try:
        # Get user details for audit log
        user_query = 'SELECT username FROM users WHERE userid = %s'
        user = execute_query(user_query, (user_id,), fetch_one=True)
        
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('admin.users'))
        
        # Prevent deletion of the currently logged-in user
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin.users'))
        
        # Delete user
        delete_query = 'DELETE FROM users WHERE userid = %s'
        execute_query(delete_query, (user_id,), commit=True)
        
        # Add audit log
        now = date.today().isoformat()
        add_audit_log(
            current_user.username,
            'Delete User',
            'User',
            str(user_id),
            f"User {user['username']} deleted"
        )
        
        flash('User deleted successfully.', 'success')
        return redirect(url_for('admin.users'))
            
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        flash('An error occurred while deleting the user.', 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/notifications/send-test', methods=['POST'])
@login_required
@admin_required
def send_test_notifications():
    """Send test task deadline notifications."""
    try:
        # Call the notification function
        sent_count = check_and_notify_task_deadlines(force=True)
        
        flash(f'Test notifications sent successfully! ({sent_count} notifications)', 'success')
    except Exception as e:
        logger.error(f"Error sending test notifications: {e}")
        flash('An error occurred while sending test notifications.', 'danger')
    
    return redirect(url_for('admin.users'))