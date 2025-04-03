import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from limits.storage import RedisStorage, MemoryStorage
from cmmc_tracker.config import config

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()
csrf = CSRFProtect()

# Initialize limiter with None storage - will be configured in create_app
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=None  # Will be set in create_app
)

def create_app(config_name=None):
    """Application factory function."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure Limiter with Redis storage
    redis_uri = app.config.get('REDIS_URL')
    
    # Initialize extensions with app
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Initialize database service with connection pool
    from app.services.database import init_app as init_db
    init_db(app)
    
    # Configure Limiter with appropriate storage
    if redis_uri:
        app.config['RATELIMIT_STORAGE_URI'] = redis_uri
    limiter.init_app(app)
    
    # Configure and Initialize Talisman (CSP & other headers)
    # Define the Content Security Policy
    csp = {
        'default-src': [
            "'self'"
            ], 
        'script-src': [
            "'self'", 
            'https://cdnjs.cloudflare.com', # Allow jQuery, Bootstrap JS
            "'unsafe-hashes'", # Reinstate unsafe-hashes (correctly quoted)
            "'sha256-U+tHSwYpCxaYh39elIShq5VNWTHsDCM263NYsqVDPTo='", 
            "'sha256-WKH3DN0mpznMXa6fDS+33+w7+vnfV9Rb+a1q1SasDFs='", 
            "'sha256-ehPVrgdV2GwJCE7DAMSg8aCgaSH3TZmA66nZZv8XrTg='", 
            "'sha256-nGcvoycun3J6WC44OPlTRh4BiXSlaDZj7YlCQ7h2N3o='"
            # Nonce will be added automatically by Talisman for blocks
            ], 
        'style-src': [
            "'self'", 
            'https://cdnjs.cloudflare.com', # Allow Bootstrap CSS
            'https://cdn.jsdelivr.net',    # Allow Bootstrap Icons CSS
            "'unsafe-hashes'", # Reinstate unsafe-hashes (correctly quoted)
            "'sha256-Et55ArTi+JMSbDReKb8DWpwdUtWcCoOGZibzhzGZSoU='", 
            "'sha256-NjYDAvf3Yswi9GqXn8q5mE3okYa3Q4PuzJ0DkAhe4yQ='", 
            "'sha256-R4pTFj1Hb1VrJAU4UoeiL+dbxZFpZ9IpcB5jA6lEfrQ='", 
            "'sha256-NjYDAvf3Yswi9GqXn8q5mE3okYa3Q4PuzJ0DkAhe4yQ='", # Added from dashboard errors
            "'sha256-ZVKgq1hdIBoPQgzFyefUpPwkQ0ClJDqnWKId/EgjQlY='"  # Added from calendar JS style
            # Nonce will be added automatically by Talisman for blocks
            ], 
        'img-src': [
            "'self'", 
            'data:' # Allow data: URIs (for QR codes)
            ], 
        'font-src': [
            "'self'", 
            'https://cdn.jsdelivr.net'    # Allow Bootstrap Icons fonts
            ], 
        'object-src': ["'none'"], 
        'base-uri': ["'self'"], 
        'frame-ancestors': ["'self'"]
    }
    # Initialize Talisman
    # force_https=False for development/testing if not behind TLS proxy
    Talisman(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src', 'style-src'], # Apply nonces
        force_https=False # Set to True in production if app is directly exposed or behind non-TLS proxy
    )
    
    # Set up logging
    configure_logging(app)
    
    # Register CSRF error handler
    register_error_handlers(app)
    
    # Add context processor for application settings
    @app.context_processor
    def inject_settings():
        """Add application settings to template context."""
        from app.services.settings import get_setting
        
        def get_app_setting(key, default=None):
            return get_setting(key, default)
        
        return dict(
            get_app_setting=get_app_setting,
            app_name=get_setting('app.name', 'CMMC Compliance Tracker')
        )
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize scheduler for email notifications
    if not app.config.get('TESTING', False):
        from app.services.scheduler import init_scheduler
        with app.app_context():
            init_scheduler(app)
    
    return app

def configure_logging(app):
    """Configure logging for the application."""
    if not app.debug and not app.testing:
        # Set log level
        log_level = logging.INFO
        
        # Create handlers
        file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        file_handler.setLevel(log_level)
        
        # Add handlers to app and logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        
        # Log application startup
        app.logger.info('CMMC Tracker startup')

def register_error_handlers(app):
    """Register error handlers with the app."""
    from flask import flash, redirect, url_for
    from flask_wtf.csrf import CSRFError
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.error(f"CSRF error: {e}")
        flash('The form you submitted is invalid or has expired. Please try again.', 'danger')
        return redirect(url_for('controls.index'))

def register_blueprints(app):
    """Register blueprints with the app."""
    # Import blueprints
    from app.routes.auth import auth_bp
    from app.routes.controls import controls_bp
    from app.routes.tasks import tasks_bp
    from app.routes.admin import admin_bp
    from app.routes.reports import reports_bp
    from app.routes.evidence import evidence_bp
    from app.routes.profile import profile_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(controls_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reports_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(profile_bp)

# Create a logger instance
logger = logging.getLogger(__name__)