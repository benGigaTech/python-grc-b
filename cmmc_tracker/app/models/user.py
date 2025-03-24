"""User model for the CMMC Tracker application."""

import logging
import json
import random
import string
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.services.database import get_by_id, insert, update, execute_query
from app.utils.security import generate_reset_token

logger = logging.getLogger(__name__)

class User(UserMixin):
    """User model class."""
    
    def __init__(self, id, username, password_hash, is_admin=0, email=None, reset_token=None, 
                 token_expiration=None, mfa_enabled=False, mfa_secret=None, mfa_backup_codes=None):
        self.id = id
        self.username = username
        self.password = password_hash
        self.is_admin = is_admin
        self.email = email
        self.reset_token = reset_token
        self.token_expiration = token_expiration
        self.mfa_enabled = mfa_enabled
        self.mfa_secret = mfa_secret
        self.mfa_backup_codes = mfa_backup_codes
        
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
        
    def enable_mfa(self, secret_key):
        """
        Enable MFA for the user and store the secret key.
        
        Args:
            secret_key: The TOTP secret key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate backup codes
            backup_codes = self._generate_backup_codes()
            backup_codes_json = json.dumps(backup_codes)
            
            # Update database
            update('users', 'userid', self.id, {
                'mfa_enabled': True,
                'mfa_secret': secret_key,
                'mfa_backup_codes': backup_codes_json
            })
            
            # Update object properties
            self.mfa_enabled = True
            self.mfa_secret = secret_key
            self.mfa_backup_codes = backup_codes_json
            
            logger.info(f"MFA enabled for user {self.username}")
            return True
        except Exception as e:
            logger.error(f"Error enabling MFA for user {self.username}: {e}")
            return False
    
    def disable_mfa(self):
        """
        Disable MFA for the user.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update database
            update('users', 'userid', self.id, {
                'mfa_enabled': False,
                'mfa_secret': None,
                'mfa_backup_codes': None
            })
            
            # Update object properties
            self.mfa_enabled = False
            self.mfa_secret = None
            self.mfa_backup_codes = None
            
            logger.info(f"MFA disabled for user {self.username}")
            return True
        except Exception as e:
            logger.error(f"Error disabling MFA for user {self.username}: {e}")
            return False
    
    def verify_backup_code(self, code):
        """
        Verify and consume a backup code.
        
        Args:
            code: The backup code to verify
            
        Returns:
            bool: True if code is valid, False otherwise
        """
        if not self.mfa_backup_codes:
            return False
        
        try:
            backup_codes = json.loads(self.mfa_backup_codes)
            
            if code in backup_codes:
                # Remove the used code
                backup_codes.remove(code)
                
                # Update database
                backup_codes_json = json.dumps(backup_codes)
                update('users', 'userid', self.id, {
                    'mfa_backup_codes': backup_codes_json
                })
                
                # Update object property
                self.mfa_backup_codes = backup_codes_json
                
                logger.info(f"Backup code used for user {self.username}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error verifying backup code for user {self.username}: {e}")
            return False
    
    def _generate_backup_codes(self, count=10, length=8):
        """
        Generate backup codes for MFA.
        
        Args:
            count: Number of codes to generate
            length: Length of each code
            
        Returns:
            list: List of backup codes
        """
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            codes.append(code)
        return codes
    
    def get_backup_codes(self):
        """
        Get the user's backup codes.
        
        Returns:
            list: List of backup codes or empty list if none
        """
        if not self.mfa_backup_codes:
            return []
        
        try:
            return json.loads(self.mfa_backup_codes)
        except Exception as e:
            logger.error(f"Error parsing backup codes for user {self.username}: {e}")
            return []
    
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
                user_data['tokenexpiration'],
                user_data.get('mfa_enabled', False),
                user_data.get('mfa_secret'),
                user_data.get('mfa_backup_codes')
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
                user_data['tokenexpiration'],
                user_data.get('mfa_enabled', False),
                user_data.get('mfa_secret'),
                user_data.get('mfa_backup_codes')
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
                user_data['tokenexpiration'],
                user_data.get('mfa_enabled', False),
                user_data.get('mfa_secret'),
                user_data.get('mfa_backup_codes')
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
                user_data['tokenexpiration'],
                user_data.get('mfa_enabled', False),
                user_data.get('mfa_secret'),
                user_data.get('mfa_backup_codes')
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None