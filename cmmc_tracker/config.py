"""Configuration settings for the CMMC Tracker application."""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    
    # Database
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'cmmc_db')
    DB_USER = os.environ.get('DB_USER', 'cmmc_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    
    # Database URI for SQLAlchemy (if you decide to use it)
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'sandbox.smtp.mailtrap.io')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 2525))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'yes', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'yes', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'bc366ad3b451bc')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '8d801eecf49e5a')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'cmmc-tracker@gigatech.net')
    
    # Password reset
    PASSWORD_SALT = os.environ.get('PASSWORD_SALT', 'sk123')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    
    # Task status constants
    TASK_STATUS = {
        'OPEN': 'Open',
        'PENDING': 'Pending Confirmation',
        'COMPLETED': 'Completed'
    }
    
    # Email notification settings
    NOTIFICATION_ENABLED = os.environ.get('NOTIFICATION_ENABLED', 'true').lower() in ['true', 'yes', '1']
    NOTIFICATION_HOUR = int(os.environ.get('NOTIFICATION_HOUR', 8))  # Default to 8 AM
    
    # Flask-APScheduler settings
    SCHEDULER_API_ENABLED = False
    SCHEDULER_TIMEZONE = "UTC"
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'}
    EVIDENCE_STATUS = {
        'CURRENT': 'Current',
        'EXPIRED': 'Expired',
        'PENDING_REVIEW': 'Pending Review'
    }

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    # Use a separate database for testing
    DB_NAME = os.environ.get('TEST_DB_NAME', 'cmmc_test_db')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"
    # Disable CSRF protection during tests
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, all sensitive config should come from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    # More secure session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}