import os
import logging
import json
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, session
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

    # Configure CSRF protection
    app.config['WTF_CSRF_ENABLED'] = True  # Enable CSRF protection
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Disable by default, enable explicitly on forms
    csrf.init_app(app)

    # Initialize database service with connection pool
    from app.services.database import init_app as init_db
    init_db(app)

    # Initialize profiler
    from app.utils.profiler import init_app as init_profiler
    init_profiler(app)

    # Configure Limiter with appropriate storage
    if redis_uri:
        app.config['RATELIMIT_STORAGE_URI'] = redis_uri
    limiter.init_app(app)

    # Configure and Initialize Talisman (CSP & other headers)
    # Define the Content Security Policy
    csp = {
        # Defines valid sources for all resources not explicitly listed
        'default-src': [
            "'self'"
        ],

        # Sources for JavaScript
        'script-src': [
            "'self'",                       # Allow scripts from same origin
            'https://cdnjs.cloudflare.com', # Allow jQuery, Bootstrap JS
            # "'unsafe-hashes'",            # Temporarily removed to identify specific violations
            # Specific inline scripts that are allowed via hash
            "'sha256-U+tHSwYpCxaYh39elIShq5VNWTHsDCM263NYsqVDPTo='",
            "'sha256-WKH3DN0mpznMXa6fDS+33+w7+vnfV9Rb+a1q1SasDFs='",
            "'sha256-ehPVrgdV2GwJCE7DAMSg8aCgaSH3TZmA66nZZv8XrTg='",
            "'sha256-nGcvoycun3J6WC44OPlTRh4BiXSlaDZj7YlCQ7h2N3o='"
            # Nonce will be added automatically by Talisman for blocks
        ],

        # Sources for CSS
        'style-src': [
            "'self'",                       # Allow CSS from same origin
            'https://cdnjs.cloudflare.com', # Allow Bootstrap CSS
            'https://cdn.jsdelivr.net',     # Allow Bootstrap Icons CSS
            # Specific inline styles that are allowed via hash
            "'sha256-Et55ArTi+JMSbDReKb8DWpwdUtWcCoOGZibzhzGZSoU='",
            "'sha256-NjYDAvf3Yswi9GqXn8q5mE3okYa3Q4PuzJ0DkAhe4yQ='",
            "'sha256-R4pTFj1Hb1VrJAU4UoeiL+dbxZFpZ9IpcB5jA6lEfrQ='",
            "'sha256-NjYDAvf3Yswi9GqXn8q5mE3okYa3Q4PuzJ0DkAhe4yQ='",  # Dashboard styles
            "'sha256-ZVKgq1hdIBoPQgzFyefUpPwkQ0ClJDqnWKId/EgjQlY='"   # Calendar styles
            # Nonce will be added automatically by Talisman for blocks
        ],

        # Sources for images
        'img-src': [
            "'self'",  # Allow images from same origin
            'data:'    # Allow data: URIs (for QR codes)
        ],

        # Sources for fonts
        'font-src': [
            "'self'",             # Allow fonts from same origin
            'https://cdn.jsdelivr.net'  # Allow Bootstrap Icons fonts
        ],

        # Sources for AJAX, WebSockets, and other connections
        'connect-src': [
            "'self'",  # Allow connections to same origin
            "'self'"   # Explicitly allow fetch API calls to our own endpoints
        ],

        # Prohibit embedding this site in iframes
        'frame-ancestors': ["'self'"],

        # Block plugins like Flash and Java
        'object-src': ["'none'"],

        # Restricts use of the <base> tag
        'base-uri': ["'self'"],

        # Form submissions only to same origin
        'form-action': ["'self'"],

        # Allowed sources for media (audio/video)
        'media-src': [
            "'self'"
        ],

        # Control where manifests can be loaded from
        'manifest-src': ["'self'"],

        # Report CSP violations to this endpoint
        'report-uri': ["/csp-report"]
    }

    # Initialize Talisman
    Talisman(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src', 'style-src'],    # Apply nonces to scripts and styles
        force_https=False,    # Should be True in production
        strict_transport_security=True,     # Enable HSTS
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', False),  # Secure cookies when HTTPS is used
        session_cookie_http_only=True,      # Prevent JavaScript access to cookies
        feature_policy={      # Set permissions policy (formerly feature policy)
            'geolocation': "'none'",
            'microphone': "'none'",
            'camera': "'none'"
        },
        referrer_policy='strict-origin-when-cross-origin'  # Control referrer information
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

    # Ensure sessions are permanent to use the configured lifetime
    @app.before_request
    def make_session_permanent():
        session.permanent = True

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
    from flask import flash, redirect, url_for, render_template
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.route('/csp-report', methods=['POST'])
    def csp_report():
        """Handle CSP violation reports."""
        try:
            report_data = request.data.decode('utf-8')
            app.logger.info(f"Received CSP Report Data: {report_data}") # Log raw report data
            report = json.loads(report_data)
            report_details = report.get('csp-report', {})
            violated_directive = report_details.get('violated-directive', 'N/A')
            blocked_uri = report_details.get('blocked-uri', 'N/A')
            document_uri = report_details.get('document-uri', 'N/A')
            source_file = report_details.get('source-file', 'N/A')
            line_number = report_details.get('line-number', 'N/A')
            column_number = report_details.get('column-number', 'N/A')
            app.logger.warning(
                f"CSP Violation: Directive='{violated_directive}', "
                f"Blocked='{blocked_uri}', Document='{document_uri}', "
                f"Source='{source_file}:{line_number}:{column_number}', "
                f"Full Report='{json.dumps(report)}'"
            )
            return jsonify({'status': 'received'}), 204
        except Exception as e:
            app.logger.error(f"Error processing CSP report: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

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
    from app.routes.chunked_upload import chunked_upload_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(controls_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reports_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(chunked_upload_bp)

# Create a logger instance
logger = logging.getLogger(__name__)