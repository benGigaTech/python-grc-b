"""User model for the CMMC Tracker application."""

import logging
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.services.database import get_by_id, insert, update, execute_query
from app.utils.security import generate_reset_token

import logging
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.services.database import get_by_id, insert, update, execute_query
from app.utils.security import generate_reset_token

logger = logging.getLogger(__name__)

class User(UserMixin):
    """User model class."""
    
    def __init__(self, id, username, password_hash, is_admin=0, email=None, reset_token=None, token_expiration=None):
        self.id = id
        self.username = username
        self.password = password_hash
        self.is_admin = is_admin
        self.email = email
        self.reset_token = reset_token
        self.token_expiration = token_expiration
        
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password, password)
    
    def set_password(self, password):
        """Set a new password for the user."""
        password_hash = generate_password_hash(password)
        update('users', 'userid', self.id, {'password': password_hash})
        self.password = password_hash
        return True
        
    def generate_password_reset_token(self):
        """Generate a password reset token for the user."""
        token = generate_reset_token(self.email)
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store token and expiration in database
        update('users', 'userid', self.id, {
            'resettoken': token,
            'tokenexpiration': expiration.isoformat()
        })
        
        self.reset_token = token
        self.token_expiration = expiration.isoformat()
        return token
        
    def clear_reset_token(self):
        """Clear the password reset token."""
        update('users', 'userid', self.id, {
            'resettoken': None,
            'tokenexpiration': None
        })
        
        self.reset_token = None
        self.token_expiration = None

    @classmethod
    def get_by_id(cls, user_id):
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            User: A User object or None if not found
        """
        user_data = get_by_id('users', 'userid', user_id)
        if user_data:
            return cls(
                user_data['userid'],
                user_data['username'],
                user_data['password'],
                user_data['isadmin'],
                user_data['email'],
                user_data['resettoken'],
                user_data['tokenexpiration']
            )
        return None

    @classmethod
    def get_by_username(cls, username):
        """
        Get a user by username.
        
        Args:
            username: The username
            
        Returns:
            User: A User object or None if not found
        """
        query = "SELECT * FROM users WHERE username = %s"
        user_data = execute_query(query, (username,), fetch_one=True)
        if user_data:
            return cls(
                user_data['userid'],
                user_data['username'],
                user_data['password'],
                user_data['isadmin'],
                user_data['email'],
                user_data['resettoken'],
                user_data['tokenexpiration']
            )
        return None

    @classmethod
    def get_by_email(cls, email):
        """
        Get a user by email.
        
        Args:
            email: The email address
            
        Returns:
            User: A User object or None if not found
        """
        query = "SELECT * FROM users WHERE email = %s"
        user_data = execute_query(query, (email,), fetch_one=True)
        if user_data:
            return cls(
                user_data['userid'],
                user_data['username'],
                user_data['password'],
                user_data['isadmin'],
                user_data['email'],
                user_data['resettoken'],
                user_data['tokenexpiration']
            )
        return None

    @staticmethod
    def create(username, password, email, is_admin=False):
        """
        Create a new user.
        
        Args:
            username: The username
            password: The plaintext password
            email: The email address
            is_admin: Whether the user is an admin
            
        Returns:
            User: The created User object or None if creation failed
        """
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Insert the user
        try:
            user_data = insert('users', {
                'username': username,
                'password': password_hash,
                'isadmin': 1 if is_admin else 0,
                'email': email
            })
            
            return User(
                user_data['userid'],
                user_data['username'],
                user_data['password'],
                user_data['isadmin'],
                user_data['email'],
                user_data['resettoken'],
                user_data['tokenexpiration']
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None