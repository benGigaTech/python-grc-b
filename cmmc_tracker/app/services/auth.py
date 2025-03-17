"""Authentication service for the CMMC Tracker application."""

import logging
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

logger = logging.getLogger(__name__)

def admin_required(f):
    """
    Decorator to restrict access to admin users only.
    
    Args:
        f: The function to wrap
        
    Returns:
        The wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Administrator privileges required to access this page.', 'danger')
            return redirect(url_for('controls.index'))
        return f(*args, **kwargs)
    return decorated_function 