"""Task model for the CMMC Tracker application."""

import logging
from datetime import date
from app.services.database import get_by_id, insert, update, delete, execute_query
from app.utils.date import parse_date, format_date

logger = logging.getLogger(__name__)

class Task:
    """Task model class."""
    
    def __init__(self, task_id, control_id, task_description, assigned_to=None, 
                 due_date=None, status="Open", confirmed=0, reviewer=None):
        self.task_id = task_id
        self.control_id = control_id
        self.task_description = task_description
        self.assigned_to = assigned_to
        self.due_date = due_date
        self.status = status
        self.confirmed = confirmed
        self.reviewer = reviewer
        self._control_name = None  # Lazy-loaded

    @property
    def control_name(self):
        """Get the associated control name (lazy-loaded)."""
        if self._control_name is None:
            query = "SELECT controlname FROM controls WHERE controlid = %s"
            result = execute_query(query, (self.control_id,), fetch_one=True)
            self._control_name = result['controlname'] if result else None
        return self._control_name

    @classmethod
    def get_by_id(cls, task_id):
        """
        Get a task by ID.
        
        Args:
            task_id: The task ID
            
        Returns:
            Task: A Task object or None if not found
        """
        task_data = get_by_id('tasks', 'taskid', task_id)
        if task_data:
            return cls(
                task_data['taskid'],
                task_data['controlid'],
                task_data['taskdescription'],
                task_data['assignedto'],
                task_data['duedate'],
                task_data['status'],
                task_data['confirmed'],
                task_data['reviewer']
            )
        return None

    @classmethod
    def get_by_control(cls, control_id, sort_by='duedate', sort_order='asc', limit=None, offset=None):
        """
        Get tasks for a specific control.
        
        Args:
            control_id: The control ID
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            list: A list of Task objects
        """
        query = f"""
            SELECT * FROM tasks
            WHERE controlid = %s
            ORDER BY {sort_by} {sort_order.upper()}
            {"LIMIT %s" if limit else ""}
            {"OFFSET %s" if offset else ""}
        """
        
        params = [control_id]
        if limit:
            params.append(limit)
        if offset:
            params.append(offset)
            
        task_data_list = execute_query(query, tuple(params), fetch_all=True)
        
        return [
            cls(
                data['taskid'],
                data['controlid'],
                data['taskdescription'],
                data['assignedto'],
                data['duedate'],
                data['status'],
                data['confirmed'],
                data['reviewer']
            ) for data in task_data_list
        ]

    @classmethod
    def get_by_user(cls, username, status=None):
        """
        Get tasks assigned to a specific user.
        
        Args:
            username: The username
            status: Optional status to filter by
            
        Returns:
            list: A list of Task objects
        """
        if status:
            query = "SELECT * FROM tasks WHERE assignedto = %s AND status = %s ORDER BY duedate"
            params = (username, status)
        else:
            query = "SELECT * FROM tasks WHERE assignedto = %s ORDER BY duedate"
            params = (username,)
            
        task_data_list = execute_query(query, params, fetch_all=True)
        
        return [
            cls(
                data['taskid'],
                data['controlid'],
                data['taskdescription'],
                data['assignedto'],
                data['duedate'],
                data['status'],
                data['confirmed'],
                data['reviewer']
            ) for data in task_data_list
        ]

    @classmethod
    def get_for_review(cls, username):
        """
        Get tasks to be reviewed by a specific user.
        
        Args:
            username: The username
            
        Returns:
            list: A list of Task objects awaiting review
        """
        query = "SELECT * FROM tasks WHERE reviewer = %s AND status = 'Pending Confirmation' ORDER BY duedate"
        task_data_list = execute_query(query, (username,), fetch_all=True)
        
        return [
            cls(
                data['taskid'],
                data['controlid'],
                data['taskdescription'],
                data['assignedto'],
                data['duedate'],
                data['status'],
                data['confirmed'],
                data['reviewer']
            ) for data in task_data_list
        ]

    @classmethod
    def get_overdue(cls):
        """
        Get all overdue tasks.
        
        Returns:
            list: A list of overdue Task objects
        """
        today = date.today().isoformat()
        query = "SELECT * FROM tasks WHERE duedate < %s AND status != 'Completed' ORDER BY duedate"
        task_data_list = execute_query(query, (today,), fetch_all=True)
        
        return [
            cls(
                data['taskid'],
                data['controlid'],
                data['taskdescription'],
                data['assignedto'],
                data['duedate'],
                data['status'],
                data['confirmed'],
                data['reviewer']
            ) for data in task_data_list
        ]

    @classmethod
    def get_due_soon(cls, days=7):
        """
        Get tasks due within the specified number of days.
        
        Args:
            days: Number of days ahead to consider
            
        Returns:
            list: A list of Task objects due soon
        """
        today = date.today()
        end_date = today + date.timedelta(days=days)
        
        query = """
            SELECT * FROM tasks 
            WHERE duedate >= %s AND duedate <= %s AND status != 'Completed'
            ORDER BY duedate
        """
        task_data_list = execute_query(query, (today.isoformat(), end_date.isoformat()), fetch_all=True)
        
        return [
            cls(
                data['taskid'],
                data['controlid'],
                data['taskdescription'],
                data['assignedto'],
                data['duedate'],
                data['status'],
                data['confirmed'],
                data['reviewer']
            ) for data in task_data_list
        ]

    @classmethod
    def create(cls, control_id, task_description, assigned_to, due_date, reviewer):
        """
        Create a new task.
        
        Args:
            control_id: The control ID
            task_description: The task description
            assigned_to: The username of the person assigned
            due_date: The due date
            reviewer: The username of the reviewer
            
        Returns:
            Task: The created Task object or None if creation failed
        """
        # Format due date consistently
        formatted_due_date = format_date(parse_date(due_date)) if due_date else None
        
        try:
            task_data = insert('tasks', {
                'controlid': control_id,
                'taskdescription': task_description,
                'assignedto': assigned_to,
                'duedate': formatted_due_date,
                'status': 'Open',
                'confirmed': 0,
                'reviewer': reviewer
            })
            
            return cls(
                task_data['taskid'],
                task_data['controlid'],
                task_data['taskdescription'],
                task_data['assignedto'],
                task_data['duedate'],
                task_data['status'],
                task_data['confirmed'],
                task_data['reviewer']
            )
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    def update(self):
        """
        Update the task in the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update('tasks', 'taskid', self.task_id, {
                'controlid': self.control_id,
                'taskdescription': self.task_description,
                'assignedto': self.assigned_to,
                'duedate': self.due_date,
                'status': self.status,
                'confirmed': self.confirmed,
                'reviewer': self.reviewer
            })
            return True
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False

    def delete(self):
        """
        Delete the task from the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            delete('tasks', 'taskid', self.task_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False

    def complete(self):
        """
        Mark the task as completed (pending confirmation).
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.status = 'Pending Confirmation'
        self.confirmed = 0
        return self.update()

    def confirm(self):
        """
        Confirm the completion of the task.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.status = 'Completed'
        self.confirmed = 1
        return self.update()

    def days_until_due(self):
        """
        Calculate days until due date.
        
        Returns:
            int: Number of days until due date or None if no due date
        """
        if not self.due_date:
            return None
            
        due = parse_date(self.due_date)
        if due:
            return (due - date.today()).days
        return None

    def is_overdue(self):
        """
        Check if task is overdue.
        
        Returns:
            bool: True if overdue, False otherwise
        """
        days = self.days_until_due()
        return days is not None and days < 0

    def to_dict(self):
        """
        Convert the task to a dictionary.
        
        Returns:
            dict: A dictionary representation of the task
        """
        return {
            'taskid': self.task_id,
            'controlid': self.control_id,
            'controlname': self.control_name,
            'taskdescription': self.task_description,
            'assignedto': self.assigned_to,
            'duedate': self.due_date,
            'status': self.status,
            'confirmed': self.confirmed,
            'reviewer': self.reviewer,
            'days_until_due': self.days_until_due(),
            'is_overdue': self.is_overdue()
        }