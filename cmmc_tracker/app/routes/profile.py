"""User profile management routes for the CMMC Tracker application."""

import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app import limiter
from app.models.user import User
from app.services.audit import add_audit_log
from app.services.mfa import generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp
from app.utils.security import is_password_strong

logger = logging.getLogger(__name__)

# Create blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET'])
@login_required
def view_profile():
    """View user profile."""
    return render_template('profile.html', user=current_user)

@profile_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """Handle password change."""
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')
        
        # Check that passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('change_password.html')
        
        # Validate password strength
        if not is_password_strong(new_password):
            flash('Password is not strong enough. It must be at least 8 characters and include uppercase, lowercase, numbers, and special characters.', 'danger')
            return render_template('change_password.html')
        
        # Update password
        if current_user.set_password(new_password):
            flash('Your password has been updated.', 'success')
            add_audit_log(current_user.username, 'Changed Password', 'User', current_user.id)
            return redirect(url_for('profile.view_profile'))
        else:
            flash('An error occurred while updating your password.', 'danger')
    
    return render_template('change_password.html')

@profile_bp.route('/profile/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    """Set up MFA for the user."""
    # If MFA is already enabled, redirect to manage MFA page
    if current_user.mfa_enabled:
        flash('MFA is already enabled for your account.', 'info')
        return redirect(url_for('profile.manage_mfa'))
    
    # Generate a new secret on first visit
    if 'mfa_secret' not in request.form:
        secret = generate_totp_secret()
        totp_uri = get_totp_uri(current_user.username, secret)
        qr_code = generate_qr_code(totp_uri)
        
        return render_template('setup_mfa.html', 
                               secret=secret, 
                               qr_code=qr_code)
    
    # Handle form submission
    secret = request.form['mfa_secret']
    code = request.form['code']
    
    # Verify the code before enabling MFA
    if verify_totp(secret, code):
        if current_user.enable_mfa(secret):
            flash('MFA has been enabled for your account. Make sure to save your backup codes!', 'success')
            add_audit_log(current_user.username, 'Enabled MFA', 'User', current_user.id)
            return redirect(url_for('profile.manage_mfa'))
        else:
            flash('An error occurred while enabling MFA.', 'danger')
    else:
        flash('Invalid verification code. Please try again.', 'danger')
        totp_uri = get_totp_uri(current_user.username, secret)
        qr_code = generate_qr_code(totp_uri)
        return render_template('setup_mfa.html', 
                               secret=secret, 
                               qr_code=qr_code)
    
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/profile/manage-mfa', methods=['GET'])
@login_required
def manage_mfa():
    """Manage MFA settings."""
    if not current_user.mfa_enabled:
        flash('MFA is not enabled for your account.', 'info')
        return redirect(url_for('profile.setup_mfa'))
    
    backup_codes = current_user.get_backup_codes()
    backup_codes_count = len(backup_codes)
    return render_template('manage_mfa.html', backup_codes=backup_codes, backup_codes_count=backup_codes_count)

@profile_bp.route('/profile/disable-mfa', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def disable_mfa():
    """Disable MFA for the user."""
    # Require password confirmation for security
    password = request.form['password']
    
    if not current_user.check_password(password):
        flash('Incorrect password.', 'danger')
        return redirect(url_for('profile.manage_mfa'))
    
    if current_user.disable_mfa():
        flash('MFA has been disabled for your account.', 'success')
        add_audit_log(current_user.username, 'Disabled MFA', 'User', current_user.id)
    else:
        flash('An error occurred while disabling MFA.', 'danger')
    
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/profile/regenerate-backup-codes', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def regenerate_backup_codes():
    """Regenerate backup codes for MFA."""
    # Require password confirmation for security
    password = request.form['password']
    
    if not current_user.check_password(password):
        flash('Incorrect password.', 'danger')
        return redirect(url_for('profile.manage_mfa'))
    
    # Re-enable MFA with the same secret to regenerate backup codes
    if current_user.enable_mfa(current_user.mfa_secret):
        flash('Your backup codes have been regenerated.', 'success')
        add_audit_log(current_user.username, 'Regenerated MFA Backup Codes', 'User', current_user.id)
    else:
        flash('An error occurred while regenerating backup codes.', 'danger')
    
    return redirect(url_for('profile.manage_mfa')) 