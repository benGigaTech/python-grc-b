"""Routes package for the CMMC Tracker application."""

# Import route blueprints so they are available for registering with the app
from app.routes.auth import auth_bp
from app.routes.controls import controls_bp
from app.routes.tasks import tasks_bp
from app.routes.admin import admin_bp
from app.routes.reports import reports_bp
from app.routes.evidence import evidence_bp
from app.routes.profile import profile_bp