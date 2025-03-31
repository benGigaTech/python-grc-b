"""Services package for the CMMC Tracker application."""

# Import services so they are available for use
from app.services.database import execute_query, get_db_connection
from app.services.email import send_email, send_task_notification, check_and_notify_task_deadlines
from app.services.audit import add_audit_log, get_audit_logs_for_object
from app.services.settings import get_setting, update_setting, get_all_settings, get_settings_by_prefix