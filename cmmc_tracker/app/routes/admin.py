"""Admin routes for the CMMC Tracker application."""

import logging
from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.task import Task
from app.models.user import User
from app.services.database import execute_query
from app.utils.date import parse_date, format_date
from werkzeug.security import generate_password_hash
from app.services.email import check_and_notify_task_deadlines
from app.services.auth import admin_required
from app.services.audit import add_audit_log, get_recent_audit_logs
from app.services.settings import get_all_settings, update_setting
from app.utils.security import is_password_strong
from app import limiter

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
        # Get all users with MFA status and account lockout info
        users_query = '''
            SELECT userid, username, isadmin, email, mfa_enabled,
                   failed_login_attempts, account_locked_until
            FROM users
            ORDER BY username
        '''
        users_data = execute_query(users_query, fetch_all=True)

        # Process the data to add a "locked" status
        users = []
        now = datetime.now().astimezone()  # Current time with timezone

        for user in users_data:
            # Check if account is locked
            is_locked = False
            locked_until = user.get('account_locked_until')

            if locked_until and isinstance(locked_until, str):
                try:
                    locked_until_dt = datetime.fromisoformat(locked_until)
                    is_locked = locked_until_dt > now
                except (ValueError, TypeError):
                    is_locked = False
            elif locked_until:
                is_locked = locked_until > now

            users.append({
                'userid': user['userid'],
                'username': user['username'],
                'isadmin': user['isadmin'],
                'email': user['email'],
                'mfa_enabled': user['mfa_enabled'],
                'failed_login_attempts': user['failed_login_attempts'] or 0,
                'is_locked': is_locked,
                'account_locked_until': locked_until
            })

        return render_template('admin_users.html', users=users)

    except Exception as e:
        logger.error(f"Error accessing user list: {e}")
        flash('An error occurred while accessing the user list.', 'danger')
        return redirect(url_for('controls.index'))

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
@limiter.limit("5 per hour")
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
                INSERT INTO users (username, password, isadmin, email, failed_login_attempts, account_locked_until)
                VALUES (%s, %s, %s, %s, 0, NULL)
                RETURNING userid
            '''
            user_id = execute_query(
                insert_query,
                (username, password_hash, is_admin, email),
                fetch_one=True,
                commit=True
            )[0]

            # Add audit log
            add_audit_log(
                current_user.username,
                'Create User',
                'User',
                user_id,
                f'Created user {username}'
            )

            flash('User created successfully!', 'success')
            return redirect(url_for('admin.users'))

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            flash('An error occurred while creating the user.', 'danger')
            return render_template('admin_create_user.html')

    return render_template('admin_create_user.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def admin_edit_user(user_id):
    """Edit a user."""
    try:
        # Get user data
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('admin.users'))

        # Check if account is locked
        is_account_locked, lockout_message = user.is_account_locked()

        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            is_admin = 1 if request.form.get('is_admin') else 0

            # Prepare update data
            update_data = {
                'email': email,
                'isadmin': is_admin
            }

            # Update password if provided
            if password:
                # Validate password strength
                if not is_password_strong(password):
                    flash('Password is not strong enough. It must be at least 8 characters and include uppercase, lowercase, numbers, and special characters.', 'danger')
                    return render_template('admin_edit_user.html', user=user.to_dict(),
                                          is_account_locked=is_account_locked,
                                          lockout_message=lockout_message)

                update_data['password'] = generate_password_hash(password)

            # Update user
            execute_query(
                'UPDATE users SET email = %s, isadmin = %s' + (', password = %s' if password else '') + ' WHERE userid = %s',
                tuple(list(update_data.values()) + [user_id]),
                commit=True
            )

            # Add audit log
            add_audit_log(
                current_user.username,
                'Edit User',
                'User',
                user_id,
                f'Edited user {user.username}'
            )

            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.users'))

        return render_template('admin_edit_user.html',
                              user=user.to_dict(),
                              is_account_locked=is_account_locked,
                              lockout_message=lockout_message)

    except Exception as e:
        logger.error(f"Error editing user: {e}")
        flash('An error occurred while editing the user.', 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/users/reset-mfa/<int:user_id>', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per hour")
def admin_reset_mfa(user_id):
    """Reset MFA for a user."""
    # Log for debugging
    logger.info(f"Reset MFA requested for user ID: {user_id} by {current_user.username}")

    if not current_user.is_admin:
        logger.error(f"Non-admin user {current_user.username} attempted to reset MFA for user ID: {user_id}")
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('controls.index'))

    try:
        # Get user details for audit log
        user_query = 'SELECT username FROM users WHERE userid = %s'
        user = execute_query(user_query, (user_id,), fetch_one=True)
        logger.info(f"Found user: {user}")

        if not user:
            logger.error(f"User ID {user_id} not found during MFA reset attempt")
            flash('User not found.', 'danger')
            return redirect(url_for('admin.users'))

        # Reset MFA
        update_query = '''
            UPDATE users
            SET mfa_enabled = FALSE, mfa_secret = NULL, mfa_backup_codes = NULL
            WHERE userid = %s
        '''
        execute_query(update_query, (user_id,), commit=True)
        logger.info(f"MFA reset successful for user ID: {user_id}")

        # Add audit log
        add_audit_log(
            current_user.username,
            'Reset MFA',
            'User',
            str(user_id),
            f"MFA reset for user {user['username']}"
        )

        flash(f"MFA has been reset for user {user['username']}.", 'success')
        return redirect(url_for('admin.admin_edit_user', user_id=user_id))

    except Exception as e:
        logger.error(f"Error resetting MFA for user ID {user_id}: {e}")
        flash('An error occurred while resetting MFA.', 'danger')
        return redirect(url_for('admin.admin_edit_user', user_id=user_id))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
@limiter.limit("5 per hour")
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
@limiter.limit("3 per hour")
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

@admin_bp.route('/users/unlock/<int:user_id>', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def admin_unlock_account(user_id):
    """Unlock a user account."""
    try:
        # Get the user
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('admin.users'))

        # Unlock the account
        user.unlock_account()

        # Log the action
        add_audit_log(
            current_user.username,
            'Unlock Account',
            'User',
            user_id,
            f'Unlocked account for user {user.username}'
        )

        flash(f'Account for {user.username} has been unlocked.', 'success')

    except Exception as e:
        logger.error(f"Error unlocking account: {e}")
        flash('An error occurred while unlocking the account.', 'danger')

    return redirect(url_for('admin.users'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Admin settings page for application configuration."""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('controls.index'))

    # Process POST requests (settings updates)
    if request.method == 'POST':
        try:
            # Extract setting updates from form
            setting_keys = request.form.getlist('setting_key')
            setting_values = request.form.getlist('setting_value')

            # Validate settings before updating
            validation_errors = []

            # Get current settings to check types
            all_settings = get_all_settings()

            for key, value in zip(setting_keys, setting_values):
                # Extract category and name from key
                category, name = key.split('.', 1) if '.' in key else ('other', key)

                # Check if this is an integer setting that needs validation
                if key == 'evidence.default_validity_days':
                    try:
                        days = int(value)
                        if days <= 0:
                            validation_errors.append(f"'{name.replace('_', ' ').title()}' must be a positive number.")
                    except ValueError:
                        validation_errors.append(f"'{name.replace('_', ' ').title()}' must be a valid number.")

            # If there are validation errors, show them and return to the form
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return render_template('admin_settings.html', settings=all_settings)

            # Update settings if validation passed
            for key, value in zip(setting_keys, setting_values):
                update_setting(key, value, current_user.username)

            # Add audit log entry
            add_audit_log(
                current_user.username,
                'update',
                'settings',
                'app',
                'Updated application settings'
            )

            flash('Settings updated successfully.', 'success')
            return redirect(url_for('admin.settings'))

        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            flash('An error occurred while updating settings.', 'danger')

    # Get all settings grouped by category
    try:
        settings = get_all_settings()
        return render_template('admin_settings.html', settings=settings)
    except Exception as e:
        logger.error(f"Error retrieving settings: {e}")
        flash('An error occurred while retrieving settings.', 'danger')
        return redirect(url_for('controls.index'))