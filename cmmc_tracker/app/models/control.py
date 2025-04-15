"""Control model for the CMMC Tracker application."""

import logging
from app.services.database import get_by_id, insert, update, delete, execute_query
from app.utils.date import parse_date, format_date

logger = logging.getLogger(__name__)

class Control:
    """Control model class."""

    def __init__(self, control_id, control_name, control_description=None, nist_mapping=None,
                 review_frequency=None, last_review_date=None, next_review_date=None):
        self.control_id = control_id
        self.control_name = control_name
        self.control_description = control_description
        self.nist_mapping = nist_mapping
        self.review_frequency = review_frequency
        self.last_review_date = last_review_date
        self.next_review_date = next_review_date

    @classmethod
    def get_by_id(cls, control_id):
        """
        Get a control by ID.

        Args:
            control_id: The control ID

        Returns:
            Control: A Control object or None if not found
        """
        control_data = get_by_id('controls', 'controlid', control_id)
        if control_data:
            return cls(
                control_data['controlid'],
                control_data['controlname'],
                control_data['controldescription'],
                control_data['nist_sp_800_171_mapping'],
                control_data['policyreviewfrequency'],
                control_data['lastreviewdate'],
                control_data['nextreviewdate']
            )
        return None

    @classmethod
    def get_all(cls, sort_by='controlid', sort_order='asc', limit=None, offset=None):
        """
        Get all controls.

        Args:
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            list: A list of Control objects
        """
        query = f"""
            SELECT * FROM controls
            ORDER BY {sort_by} {sort_order.upper()}
            {"LIMIT %s" if limit else ""}
            {"OFFSET %s" if offset else ""}
        """

        params = []
        if limit:
            params.append(limit)
        if offset:
            params.append(offset)

        control_data_list = execute_query(query, tuple(params) if params else None, fetch_all=True)

        return [
            cls(
                data['controlid'],
                data['controlname'],
                data['controldescription'],
                data['nist_sp_800_171_mapping'],
                data['policyreviewfrequency'],
                data['lastreviewdate'],
                data['nextreviewdate']
            ) for data in control_data_list
        ]

    @classmethod
    def search(cls, search_term, limit=None, offset=None):
        """
        Search for controls.

        Args:
            search_term: The search term
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            list: A list of matching Control objects
        """
        query = """
            SELECT * FROM controls
            WHERE controlid LIKE %s OR controlname LIKE %s OR controldescription LIKE %s
            ORDER BY controlid
            {"LIMIT %s" if limit else ""}
            {"OFFSET %s" if offset else ""}
        """

        params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
        if limit:
            params.append(limit)
        if offset:
            params.append(offset)

        control_data_list = execute_query(query, params, fetch_all=True)

        return [
            cls(
                data['controlid'],
                data['controlname'],
                data['controldescription'],
                data['nist_sp_800_171_mapping'],
                data['policyreviewfrequency'],
                data['lastreviewdate'],
                data['nextreviewdate']
            ) for data in control_data_list
        ]

    @classmethod
    def count(cls, search_term=None):
        """
        Count the number of controls.

        Args:
            search_term: Optional search term to filter by

        Returns:
            int: The number of controls
        """
        if search_term:
            query = """
                SELECT COUNT(*) FROM controls
                WHERE controlid LIKE %s OR controlname LIKE %s OR controldescription LIKE %s
            """
            params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
            result = execute_query(query, params, fetch_one=True)
        else:
            query = "SELECT COUNT(*) FROM controls"
            result = execute_query(query, fetch_one=True)

        return result[0]

    @classmethod
    def create(cls, control_id, control_name, control_description=None, nist_mapping=None, review_frequency=None):
        """
        Create a new control.

        Args:
            control_id: The control ID
            control_name: The control name
            control_description: The control description
            nist_mapping: The NIST SP 800-171 mapping
            review_frequency: The policy review frequency

        Returns:
            Control: The created Control object or None if creation failed
        """
        try:
            control_data = insert('controls', {
                'controlid': control_id,
                'controlname': control_name,
                'controldescription': control_description,
                'nist_sp_800_171_mapping': nist_mapping,
                'policyreviewfrequency': review_frequency
            })

            return cls(
                control_data['controlid'],
                control_data['controlname'],
                control_data['controldescription'],
                control_data['nist_sp_800_171_mapping'],
                control_data['policyreviewfrequency'],
                control_data['lastreviewdate'],
                control_data['nextreviewdate']
            )
        except Exception as e:
            logger.error(f"Error creating control: {e}")
            return None

    def update(self):
        """
        Update the control in the database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update('controls', 'controlid', self.control_id, {
                'controlname': self.control_name,
                'controldescription': self.control_description,
                'nist_sp_800_171_mapping': self.nist_mapping,
                'policyreviewfrequency': self.review_frequency,
                'lastreviewdate': self.last_review_date,
                'nextreviewdate': self.next_review_date
            })
            return True
        except Exception as e:
            logger.error(f"Error updating control: {e}")
            return False

    def delete(self):
        """
        Delete the control from the database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            delete('controls', 'controlid', self.control_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting control: {e}")
            return False

    def save(self):
        """
        Save the control to the database.
        If the control exists, it will be updated. Otherwise, it will be created.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if control exists
            existing_control = Control.get_by_id(self.control_id)

            if existing_control:
                # Update existing control
                return self.update()
            else:
                # Create new control
                control_data = insert('controls', {
                    'controlid': self.control_id,
                    'controlname': self.control_name,
                    'controldescription': self.control_description,
                    'nist_sp_800_171_mapping': self.nist_mapping,
                    'policyreviewfrequency': self.review_frequency,
                    'lastreviewdate': self.last_review_date,
                    'nextreviewdate': self.next_review_date
                })
                return bool(control_data)
        except Exception as e:
            logger.error(f"Error saving control: {e}")
            return False

    def update_review_dates(self, last_review_date, next_review_date):
        """
        Update the review dates for the control.

        Args:
            last_review_date: The last review date
            next_review_date: The next review date

        Returns:
            bool: True if successful, False otherwise
        """
        # Format dates consistently
        self.last_review_date = format_date(parse_date(last_review_date)) if last_review_date else None
        self.next_review_date = format_date(parse_date(next_review_date)) if next_review_date else None

        try:
            update('controls', 'controlid', self.control_id, {
                'lastreviewdate': self.last_review_date,
                'nextreviewdate': self.next_review_date
            })
            return True
        except Exception as e:
            logger.error(f"Error updating review dates: {e}")
            return False

    def get_tasks(self, sort_by='duedate', sort_order='asc', limit=None, offset=None):
        """
        Get tasks associated with this control.

        Args:
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            list: A list of Task objects
        """
        from app.models.task import Task
        return Task.get_by_control(
            self.control_id,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

    def count_tasks(self):
        """
        Count the number of tasks for this control.

        Returns:
            int: The number of tasks
        """
        query = "SELECT COUNT(*) FROM tasks WHERE controlid = %s"
        result = execute_query(query, (self.control_id,), fetch_one=True)
        return result[0]

    def get_review_period_months(self):
        """
        Get the review period in months based on the review frequency.

        Returns:
            int or None: The number of months between reviews, or None if not applicable
        """
        if not self.review_frequency or self.review_frequency == 'None':
            return None

        frequency_map = {
            'Monthly': 1,
            'Quarterly': 3,
            'Semi-Annual': 6,
            'Annual': 12,
            'Biennial': 24
        }

        return frequency_map.get(self.review_frequency)

    def calculate_next_review_date(self):
        """
        Calculate the next review date based on the last review date and review frequency.

        Returns:
            str or None: The next review date in ISO format, or None if not applicable
        """
        if not self.last_review_date or not self.review_frequency:
            return None

        months = self.get_review_period_months()
        if not months:
            return None

        try:
            from datetime import date, timedelta
            from dateutil.relativedelta import relativedelta

            last_review = date.fromisoformat(self.last_review_date)
            next_review = last_review + relativedelta(months=months)

            return next_review.isoformat()
        except (ValueError, ImportError) as e:
            logger.error(f"Error calculating next review date: {e}")
            return None

    def is_review_due(self):
        """
        Check if the control is due for review.

        Returns:
            bool: True if the control is due for review, False otherwise
        """
        if not self.next_review_date:
            return False

        try:
            from datetime import date
            next_review = date.fromisoformat(self.next_review_date)
            today = date.today()

            return next_review <= today
        except ValueError as e:
            logger.error(f"Error checking if review is due: {e}")
            return False

    def to_dict(self):
        """
        Convert the control to a dictionary.

        Returns:
            dict: A dictionary representation of the control
        """
        return {
            'controlid': self.control_id,
            'controlname': self.control_name,
            'controldescription': self.control_description,
            'nist_sp_800_171_mapping': self.nist_mapping,
            'policyreviewfrequency': self.review_frequency,
            'lastreviewdate': self.last_review_date,
            'nextreviewdate': self.next_review_date,
            # Add these fields for test compatibility
            'control_id': self.control_id,
            'control_name': self.control_name,
            'control_description': self.control_description,
            'nist_mapping': self.nist_mapping,
            'review_frequency': self.review_frequency,
            'last_review_date': self.last_review_date,
            'next_review_date': self.next_review_date
        }