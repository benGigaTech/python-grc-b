"""Scheduler service for running background tasks."""

import logging
from flask import current_app
from flask_apscheduler import APScheduler
from app.services.email import check_and_notify_task_deadlines

logger = logging.getLogger(__name__)
scheduler = APScheduler()

def init_scheduler(app):
    """
    Initialize the scheduler with the Flask app and configure jobs.
    
    Args:
        app: Flask application instance
    """
    try:
        # Initialize the scheduler with the app
        scheduler.init_app(app)
        
        # Add jobs
        add_task_notification_job(app)
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Error initializing scheduler: {e}")

def add_task_notification_job(app):
    """
    Add a job to check and send task deadline notifications.
    
    Args:
        app: Flask application instance
    """
    try:
        # Get email notification configuration from app config
        notification_hour = app.config.get('NOTIFICATION_HOUR', 8)  # Default to 8 AM
        
        # Define the job to run daily at the configured hour
        scheduler.add_job(
            id='task_deadline_notifications',
            func=check_and_notify_task_deadlines,
            trigger='cron',
            hour=notification_hour,
            minute=0,
            replace_existing=True
        )
        
        logger.info(f"Task deadline notification job scheduled to run daily at {notification_hour}:00")
    except Exception as e:
        logger.error(f"Error setting up task notification job: {e}")

def add_one_time_job(func, args=None, kwargs=None, run_date=None, seconds=None):
    """
    Add a one-time job to the scheduler.
    
    Args:
        func: Function to execute
        args: Positional arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
        run_date: Date/time to run the job (alternative to seconds)
        seconds: Number of seconds from now to run the job (alternative to run_date)
        
    Returns:
        str: ID of the scheduled job or None if failed
    """
    try:
        job_id = f"one_time_{id(func)}_{id(run_date or seconds)}"
        
        if seconds is not None:
            from datetime import datetime, timedelta
            run_date = datetime.now() + timedelta(seconds=seconds)
            
        scheduler.add_job(
            id=job_id,
            func=func,
            args=args or (),
            kwargs=kwargs or {},
            trigger='date',
            run_date=run_date,
            replace_existing=True
        )
            
        logger.info(f"One-time job scheduled: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"Error scheduling one-time job: {e}")
        return None 