"""Security utility functions for the CMMC Tracker application."""

import re
import logging
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app

logger = logging.getLogger(__name__)

def sanitize_string(value, max_length=None, allow_html=False):
    """
    Sanitize a string input by stripping whitespace, removing potentially harmful characters,
    and optionally limiting length.
    
    Args:
        value (str): The string to sanitize
        max_length (int, optional): Maximum allowed length
        allow_html (bool): Whether to allow HTML tags (default: False)
        
    Returns:
        str: The sanitized string
    """
    if value is None:
        return ""
        
    # Convert to string if not already
    result = str(value).strip()
    
    if not allow_html:
        # Remove HTML tags
        result = re.sub(r'<[^>]*>', '', result)
        
        # Remove potentially harmful characters
        result = re.sub(r'[^\w\s@.-]', '', result)
    
    # Limit length if specified
    if max_length and len(result) > max_length:
        return result[:max_length]
        
    return result

def generate_reset_token(email):
    """
    Generate a secure token for password reset.
    
    Args:
        email (str): The user's email address
        
    Returns:
        str: The reset token
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    salt = current_app.config['PASSWORD_SALT']
    return serializer.dumps(email, salt=salt)

def verify_reset_token(token, expiration=3600):
    """
    Verify a password reset token.
    
    Args:
        token (str): The reset token
        expiration (int): Token expiration time in seconds (default: 1 hour)
        
    Returns:
        str or None: The email address if token is valid, otherwise None
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    salt = current_app.config['PASSWORD_SALT']
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
        return email
    except SignatureExpired:
        logger.warning("Token expired")
        return None
    except BadSignature:
        logger.warning("Invalid token")
        return None

def is_password_strong(password):
    """
    Check if a password meets the strength requirements.
    
    Args:
        password (str): The password to check
        
    Returns:
        bool: True if the password is strong enough, False otherwise
    """
    # Password should be at least 8 characters long
    if len(password) < 8:
        return False
    
    # Password should contain at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
    
    # Password should contain at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False
    
    # Password should contain at least one digit
    if not re.search(r'\d', password):
        return False
    
    # Password should contain at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True