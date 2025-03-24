import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
    
    # Configure Limiter with appropriate storage
    if redis_uri:
        app.config['RATELIMIT_STORAGE_URI'] = redis_uri
    limiter.init_app(app)
    
    # Set up logging
    configure_logging(app)
    
    # Register CSRF error handler
    register_error_handlers(app)
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to every response."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        return response
    
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
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(controls_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reports_bp)
    app.register_blueprint(evidence_bp)

# Create a logger instance
logger = logging.getLogger(__name__)