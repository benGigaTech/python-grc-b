"""Email service for sending notifications."""

import logging
from flask import current_app, render_template
from flask_mail import Message
from app import mail
from app.models.task import Task
from app.services.database import execute_query
from app.utils.date import parse_date

logger = logging.getLogger(__name__)

def send_email(to, subject, template, **kwargs):
    """
    Send an email using a template.
    
    Args:
        to (str or list): Recipient email address or list of addresses
        subject (str): Email subject
        template (str): HTML template to render
        **kwargs: Variables to pass to the template
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        msg = Message(subject, recipients=[to] if isinstance(to, str) else to)
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False

def send_task_notification(task_id, notification_type):
    """
    Send a notification for a task.
    
    Args:
        task_id (int): ID of the task
        notification_type (str): Type of notification (assigned, due_soon, overdue, completed, confirmed)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get task information
        task = Task.get_by_id(task_id)
        if not task:
            logger.error(f"Task not found for notification: {task_id}")
            return False
        
        # Get assignee and reviewer email addresses
        assignee_email = get_user_email(task.assigned_to)
        reviewer_email = get_user_email(task.reviewer)
        
        if not assignee_email and not reviewer_email:
            logger.error(f"No email addresses found for task {task_id}")
            return False
        
        # Convert to dictionary for the email template
        task_dict = task.to_dict()
        
        # Different notification types
        if notification_type == 'assigned':
            subject = f"New Task Assigned: {task.task_description}"
            template = 'emails/task_assigned.html'
            recipient = assignee_email
            
        elif notification_type == 'due_soon':
            subject = f"Task Due Soon: {task.task_description}"
            template = 'emails/task_due_soon.html'
            recipient = assignee_email
            
        elif notification_type == 'overdue':
            subject = f"Overdue Task: {task.task_description}"
            template = 'emails/task_overdue.html'
            recipients = [assignee_email]
            
            # Also notify reviewer for overdue tasks
            if reviewer_email and reviewer_email != assignee_email:
                recipients.append(reviewer_email)
                
            recipient = recipients
            
        elif notification_type == 'completed':
            subject = f"Task Completed: {task.task_description}"
            template = 'emails/task_completed.html'
            recipient = reviewer_email
            
        elif notification_type == 'confirmed':
            subject = f"Task Confirmed: {task.task_description}"
            template = 'emails/task_confirmed.html'
            recipient = assignee_email
            
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False
        
        # Send the email
        return send_email(recipient, subject, template, task=task_dict)
        
    except Exception as e:
        logger.error(f"Failed to send task notification: {e}")
        return False

def send_password_reset(email, reset_url):
    """
    Send a password reset email.
    
    Args:
        email (str): The user's email address
        reset_url (str): The password reset URL
        
    Returns:
        bool: True if successful, False otherwise
    """
    subject = "Password Reset Request"
    template = 'emails/password_reset.html'
    
    return send_email(email, subject, template, reset_url=reset_url)

def send_test_email(email):
    """
    Send a test email to verify email configuration.
    
    Args:
        email (str): The email address to send to
        
    Returns:
        bool: True if successful, False otherwise
    """
    subject = "CMMC Tracker Email Test"
    html = """
    <h1>Email Test</h1>
    <p>This is a test email from your CMMC Compliance Tracker.</p>
    <p>If you received this email, your email configuration is working correctly.</p>
    """
    
    try:
        msg = Message(subject, recipients=[email])
        msg.html = html
        mail.send(msg)
        logger.info(f"Test email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        return False

def check_and_notify_task_deadlines():
    """
    Check for tasks that are due soon or overdue and send email notifications.
    This function should be run as a scheduled job.
    
    Returns:
        int: Number of notifications sent
    """
    from datetime import date, timedelta
    
    today = date.today()
    notifications_sent = 0
    
    try:
        # Tasks due in 3 days
        due_soon_tasks = Task.get_due_soon(days=3)
        
        # Send 'due soon' notifications
        for task in due_soon_tasks:
            if send_task_notification(task.task_id, 'due_soon'):
                notifications_sent += 1
                logger.info(f"Sent 'due soon' notification for task {task.task_id}")
        
        # Find overdue tasks
        overdue_tasks = Task.get_overdue()
        
        # Send 'overdue' notifications
        for task in overdue_tasks:
            if send_task_notification(task.task_id, 'overdue'):
                notifications_sent += 1
                logger.info(f"Sent 'overdue' notification for task {task.task_id}")
        
        return notifications_sent
        
    except Exception as e:
        logger.error(f"Error in check_and_notify_task_deadlines: {e}")
        return 0

def get_user_email(username):
    """
    Get a user's email address.
    
    Args:
        username (str): The username
        
    Returns:
        str: The email address or None if not found
    """
    if not username:
        return None
        
    query = "SELECT email FROM users WHERE username = %s"
    result = execute_query(query, (username,), fetch_one=True)
    
    return result['email'] if result else None