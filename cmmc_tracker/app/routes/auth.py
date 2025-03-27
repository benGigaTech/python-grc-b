"""Authentication routes for the CMMC Tracker application."""

import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager, limiter
from app.models.user import User
from app.services.audit import add_audit_log
from app.services.email import send_password_reset
from app.services.mfa import verify_totp, generate_totp_secret, get_totp_uri, generate_qr_code
from app.utils.security import sanitize_string, verify_reset_token, generate_reset_token, is_password_strong

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.get_by_username(username)
        
        # Check if user exists
        if not user:
            # Don't reveal if username doesn't exist for security reasons
            logger.warning(f"Login attempt with non-existent username: {username} from IP: {request.remote_addr}")
            add_audit_log(username, 'Failed Login', 'User', '0', f"Failed login with non-existent username from IP: {request.remote_addr}")
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
        
        # Check if account is locked
        is_locked, lockout_message = user.is_account_locked()
        if is_locked:
            logger.warning(f"Login attempt on locked account: {username} from IP: {request.remote_addr}")
            add_audit_log(username, 'Failed Login - Locked Account', 'User', user.id, f"Login attempt on locked account from IP: {request.remote_addr}")
            flash(f'This account is temporarily locked due to too many failed login attempts. {lockout_message}', 'danger')
            return render_template('login.html')
        
        # Validate password
        if user.check_password(password):
            # Reset failed login attempts on successful login
            user.reset_failed_attempts()
            
            # Check if MFA is enabled
            if user.mfa_enabled:
                # Store user ID in session for MFA verification
                session['mfa_user_id'] = user.id
                add_audit_log(username, 'Login MFA Required', 'User', user.id)
                return redirect(url_for('auth.verify_mfa'))
            
            # No MFA required, log the user in
            login_user(user)
            flash('Logged in successfully!', 'success')
            # Log the login
            add_audit_log(username, 'Login', 'User', user.id)
            return redirect(url_for('controls.index'))
        else:
            # Increment failed login attempts
            was_locked = user.increment_failed_attempts()
            
            # Log failed login attempt
            logger.warning(f"Failed login attempt for username: {username} from IP: {request.remote_addr}")
            
            if was_locked:
                add_audit_log(username, 'Account Locked', 'User', user.id, f"Account locked after multiple failed login attempts from IP: {request.remote_addr}")
                flash('This account has been temporarily locked due to too many failed login attempts.', 'danger')
            else:
                add_audit_log(username, 'Failed Login', 'User', user.id, f"Failed login from IP: {request.remote_addr}")
                # Don't reveal that the password was wrong specifically
                flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/verify-mfa', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def verify_mfa():
    """Handle MFA verification."""
    # Check if user ID is in session
    if 'mfa_user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.get_by_id(session['mfa_user_id'])
    if not user:
        session.pop('mfa_user_id', None)
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Check if account is locked (could have been locked by admin during MFA verification)
    is_locked, lockout_message = user.is_account_locked()
    if is_locked:
        session.pop('mfa_user_id', None)
        logger.warning(f"MFA verification attempt on locked account: {user.username}")
        add_audit_log(user.username, 'Failed MFA - Locked Account', 'User', user.id)
        flash(f'This account is temporarily locked. {lockout_message}', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Check if the user is using a backup code
        if 'backup_code' in request.form and request.form['backup_code']:
            backup_code = request.form['backup_code'].strip().upper()
            if user.verify_backup_code(backup_code):
                # Reset failed login attempts
                user.reset_failed_attempts()
                
                # Log the user in
                login_user(user)
                session.pop('mfa_user_id', None)
                flash('Logged in successfully with backup code!', 'success')
                add_audit_log(user.username, 'Login with Backup Code', 'User', user.id)
                return redirect(url_for('controls.index'))
            else:
                # Don't increment failed attempts for backup code failures
                # But do log the attempt
                flash('Invalid backup code.', 'danger')
                add_audit_log(user.username, 'Failed Backup Code', 'User', user.id)
                return render_template('verify_mfa.html')
        
        # Otherwise, verify TOTP
        totp_code = request.form.get('totp_code', '').strip()
        if verify_totp(user.mfa_secret, totp_code):
            # Reset failed login attempts
            user.reset_failed_attempts()
            
            # Log the user in
            login_user(user)
            session.pop('mfa_user_id', None)
            flash('Logged in successfully!', 'success')
            add_audit_log(user.username, 'Login with MFA', 'User', user.id)
            return redirect(url_for('controls.index'))
        else:
            # Increment failed login attempts
            was_locked = user.increment_failed_attempts()
            
            if was_locked:
                session.pop('mfa_user_id', None)
                add_audit_log(user.username, 'Account Locked', 'User', user.id, "Account locked after multiple failed MFA attempts")
                flash('This account has been temporarily locked due to too many failed authentication attempts.', 'danger')
                return redirect(url_for('auth.login'))
            else:
                flash('Invalid authentication code. Please try again.', 'danger')
                add_audit_log(user.username, 'Failed MFA Verification', 'User', user.id)
            
    return render_template('verify_mfa.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    username = current_user.username
    user_id = current_user.id
    logout_user()
    flash('You have been logged out.', 'success')
    add_audit_log(username, 'Logout', 'User', user_id)
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        # Validate password strength
        if not is_password_strong(password):
            flash('Password is not strong enough. It must be at least 8 characters and include uppercase, lowercase, numbers, and special characters.', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        existing_user = User.get_by_username(username)
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('register.html')
        
        # Create the new user
        user = User.create(username, password, email)
        
        if user:
            # Log the registration
            add_audit_log('SYSTEM', 'Register User', 'User', user.id, f'New user registered: {username}')
            flash('User registered successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred during registration. Please try again.', 'danger')
            
    return render_template('register.html')

@auth_bp.route('/request_reset', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def request_reset():
    """Handle password reset request."""
    if request.method == 'POST':
        email = sanitize_string(request.form['email'], max_length=255)
        
        # Check if user exists
        user = User.get_by_email(email)
        
        if user:
            # Generate token
            token = user.generate_password_reset_token()
            
            # Generate reset URL
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Send password reset email
            if send_password_reset(email, reset_url):
                logger.info(f"Password reset email sent to {email}")
                flash('A password reset link has been sent to your email address.', 'success')
            else:
                logger.error(f"Failed to send password reset email to {email}")
                flash('An error occurred while sending the reset email. Please try again later.', 'danger')
        else:
            # Don't reveal whether the email exists for security
            flash('If an account with that email exists, a password reset link has been sent.', 'success')
            logger.warning(f"Password reset requested for non-existent email: {email}")
        
        return redirect(url_for('auth.login'))
            
    return render_template('request_reset.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset."""
    # Verify token
    email = verify_reset_token(token)
    if not email:
        flash('That password reset token is invalid or expired.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.get_by_email(email)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        # Validate password strength
        if not is_password_strong(password):
            flash('Password is not strong enough. It must be at least 8 characters and include uppercase, lowercase, numbers, and special characters.', 'danger')
            return render_template('reset_password.html', token=token)
        
        # Update password
        if user.set_password(password):
            # Clear the reset token
            user.clear_reset_token()
            
            # Reset failed login attempts and unlock account
            user.unlock_account()
            
            # Log the password reset
            add_audit_log('SYSTEM', 'Reset Password', 'User', user.id)
            
            flash('Your password has been reset! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred while resetting your password.', 'danger')
    
    return render_template('reset_password.html', token=token)

@auth_bp.route('/test_email', methods=['GET'])
@login_required
def test_email():
    """Test email functionality (admin only)."""
    if not current_user.is_admin:
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('controls.index'))
    
    from app.services.email import send_test_email
    
    recipient = current_user.email
    
    if not recipient:
        flash('Your user account does not have an email address set.', 'danger')
        return redirect(url_for('controls.index'))
    
    if send_test_email(recipient):
        flash(f'Test email sent to {recipient}. Please check your inbox.', 'success')
    else:
        flash('Failed to send test email. Check server logs for details.', 'danger')
    
    return redirect(url_for('controls.index'))