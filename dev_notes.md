# CMMC Compliance Tracker: Developer Documentation

This document provides comprehensive technical documentation of the CMMC Compliance Tracker application's architecture, code organization, and implementation details. It is intended for developers working on maintaining or extending the application.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Application Structure](#application-structure)
3. [Database Schema](#database-schema)
4. [Core Components](#core-components)
   - [Models](#models)
   - [Services](#services)
   - [Routes](#routes)
   - [Utilities](#utilities)
5. [Authentication System](#authentication-system)
6. [Dashboard and Visualization](#dashboard-and-visualization)
7. [Import/Export System](#import-export-system)
8. [Task Notifications](#task-notifications)
9. [Security Considerations](#security-considerations)
10. [Development Workflow](#development-workflow)
11. [Docker Configuration](#docker-configuration)
12. [Database Initialization](#database-initialization)
13. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
14. [Testing](#testing)

## Architecture Overview

The CMMC Tracker is a Flask-based web application following a layered architecture pattern:

- **Presentation Layer**: Flask routes and Jinja2 templates with Chart.js visualizations
- **Business Logic Layer**: Models and Services
- **Data Access Layer**: Database service abstraction over PostgreSQL
- **Infrastructure**: Docker containers for the web app and PostgreSQL database
- **Background Processing**: Flask-APScheduler for automated email notifications

The application uses the Blueprint pattern to organize routes and follows a factory pattern for application creation, allowing different configurations based on the environment. It implements a responsive dashboard with real-time metrics and automated task notification system.

## Application Structure

```
cmmc_tracker/
├── app/                      # Main application package
│   ├── models/               # Data models
│   ├── routes/               # Route definitions (blueprints)
│   ├── services/             # Business services
│   ├── templates/            # Jinja2 HTML templates
│   ├── utils/                # Utility functions
│   └── __init__.py           # Application factory
├── config.py                 # Configuration classes
└── run.py                    # Application entry point

db/                           # Database initialization scripts
├── init.sql                  # SQL schema setup

# Supporting scripts
seed_db.py                    # Database seeding script
update_templates.py           # Template updater utility
structure_check_script.py     # Code structure validation
```

## Database Schema

The application uses PostgreSQL with the following tables:

1. **users**
   - `userid`: Serial primary key
   - `username`: Unique username (TEXT)
   - `password`: Password hash (TEXT)
   - `isadmin`: Admin flag (INTEGER)
   - `email`: Email address (TEXT)
   - `resettoken`: Password reset token (TEXT)
   - `tokenexpiration`: Token expiration timestamp (TEXT)

2. **controls**
   - `controlid`: Primary key (TEXT)
   - `controlname`: Control name (TEXT)
   - `controldescription`: Description (TEXT)
   - `nist_sp_800_171_mapping`: Related NIST controls (TEXT)
   - `policyreviewfrequency`: Review frequency (TEXT)
   - `lastreviewdate`: Last review date (TEXT)
   - `nextreviewdate`: Next review date (TEXT)

3. **tasks**
   - `taskid`: Serial primary key
   - `controlid`: Foreign key to controls (TEXT)
   - `taskdescription`: Task description (TEXT)
   - `assignedto`: Assigned user (TEXT)
   - `duedate`: Due date (TEXT)
   - `status`: Task status (TEXT)
   - `confirmed`: Confirmation flag (INTEGER)
   - `reviewer`: Reviewer username (TEXT)

4. **auditlogs**
   - `logid`: Serial primary key
   - `timestamp`: Action timestamp (TEXT)
   - `username`: Acting user (TEXT)
   - `action`: Action performed (TEXT)
   - `objecttype`: Object type (TEXT)
   - `objectid`: Object ID (TEXT)
   - `details`: Additional details (TEXT)

## Core Components

### Models

The application uses the following model classes to represent data entities:

#### User Model (`models/user.py`)
- Represents system users with authentication capabilities
- Implements UserMixin for Flask-Login integration
- Methods for password management and user lookup

#### Control Model (`models/control.py`)
- Represents CMMC controls
- Includes methods for CRUD operations and related task management
- Handles control review scheduling

#### Task Model (`models/task.py`)
- Represents compliance tasks assigned to users
- Manages task status, assignment, and completion workflow
- Includes methods for tracking overdue tasks

#### AuditLog Model (`models/audit.py`)
- Records all significant actions in the system
- Provides audit trail for compliance purposes
- Implements methods for querying audit history

### Services

Service components provide reusable business logic and integrations:

#### Database Service (`services/database.py`)
- Provides a data access layer with CRUD operations
- Handles database connections and query execution
- Implements error handling and connection pooling

#### Email Service (`services/email.py`)
- Manages email notifications
- Handles password reset emails
- Provides task notification capabilities

#### Audit Service (`services/audit.py`)
- Records system actions to the audit log
- Ensures consistent audit trail creation

### Routes

The application uses Flask Blueprints to organize routes:

#### Authentication Routes (`routes/auth.py`)
- User login, logout, and registration
- Password reset functionality

#### Control Routes (`routes/controls.py`)
- CRUD operations for compliance controls
- Control review management

#### Task Routes (`routes/tasks.py`)
- Task assignment and management
- Task completion and review workflow

#### Admin Routes (`routes/admin.py`)
- User management for administrators (`/admin/users` and `/admin/users/create` endpoints)
- Admin dashboard for system monitoring

#### Reports Routes (`routes/reports.py`)
- Compliance reporting and dashboards

### Utilities

Utility modules provide reusable helper functions:

- **Date utilities**: Date parsing, formatting, and calculation functions
- **Security utilities**: Token generation, validation, and input sanitization
- **Form utilities**: Form validation and processing helpers

## Authentication System

The application uses Flask-Login for authentication with the following workflow:

1. Users log in with username/password
2. Passwords are verified against stored hashes
3. Successful login creates a user session
4. Role-based access control restricts admin functions
5. Password reset uses time-limited tokens sent via email

Security features include:
- Password hashing with Werkzeug's security functions
- CSRF protection on all forms
- Session management with Flask-Login
- Audit logging of authentication events

## Dashboard and Visualization

The application implements a responsive dashboard that provides real-time metrics and visualizations for compliance status.

### Dashboard Components

1. **Summary Cards**:
   - Total Controls
   - Overdue Tasks
   - Pending Tasks
   - Controls Due for Review

2. **Charts and Visualizations**:
   - Compliance Status Doughnut Chart (Compliant, In Progress, Non-Compliant, Not Assessed)
   - Task Status Pie Chart (Open, In Progress, Completed, Overdue)
   - Recent Activities Table
   - My Tasks Table

### Implementation Details

1. **Routes**:
   - The dashboard endpoint is defined in `app/routes/controls.py` under the `/dashboard` route
   - It aggregates data from multiple models and database queries

2. **Template**:
   - Dashboard template: `app/templates/dashboard.html`
   - Uses Chart.js for rendering charts
   - Responsive layout using CSS Grid and Flexbox

3. **Data Flow**:
   - Control metrics collected via SQL aggregation
   - Task metrics filtered by status and due dates
   - Recently completed activities pulled from audit logs
   - User-specific tasks filtered from the tasks table

4. **Entry Point**:
   - Primary application navigation starts at the dashboard
   - Navigation bar updated to highlight dashboard as main entry point

## Import/Export System

The application supports bulk operations for compliance controls through CSV import and export functionality.

### Export System

1. **Implementation**:
   - Export functionality is implemented in `app/routes/controls.py` under the `/export-csv` route
   - Uses Python's CSV module and Flask's Response class

2. **Features**:
   - Generates a CSV file containing all control information
   - Includes headers for user-friendly parsing
   - Names the file with a timestamp for version tracking

3. **Usage**:
   - Export button added to the controls list page
   - Direct URL access: `/export-csv`

### Import System

1. **Implementation**:
   - Import functionality is implemented in `app/routes/controls.py` under the `/import-csv` route
   - Uses the `Control.save()` method to handle both new and existing controls

2. **Features**:
   - Validates uploaded CSV files
   - Parses CSV header to map to database fields
   - Handles both creation and updating of controls
   - Reports success/error counts
   - Admin permission required

3. **Template**:
   - Import form: `app/templates/import_controls.html`
   - Includes documentation for CSV format

4. **Security Considerations**:
   - File type validation (CSV only)
   - Admin-only access
   - Input sanitization for CSV contents

## Task Notifications

The application implements automated email notifications for task deadlines to improve user awareness and compliance task completion rates.

### Notification System Components

1. **Email Service**:
   - Located in `app/services/email.py`
   - Provides functions for sending various types of notifications
   - Uses Flask-Mail for SMTP operations
   - Templates stored in `app/templates/emails/`

2. **Scheduler Service**:
   - Located in `app/services/scheduler.py`
   - Uses Flask-APScheduler for background tasks
   - Initializes with the Flask application

3. **Configuration**:
   - Email notification settings in config.py
   - NOTIFICATION_ENABLED controls whether notifications are active
   - NOTIFICATION_HOUR sets the daily time for notification sending

### Notification Types

1. **Task Assignment**: When a task is assigned to a user
2. **Due Soon**: For tasks approaching their deadline (within 3 days)
3. **Overdue**: For tasks that have passed their deadline
4. **Task Completed**: When a task is marked as completed
5. **Task Confirmation**: When a reviewer confirms a completed task

### Testing Notifications

1. **Manual Testing**:
   - Admin interface includes a button to manually trigger notifications
   - Available at admin users page
   - Useful for verifying email configuration

2. **Scheduled Execution**:
   - Default: Runs daily at 8 AM (configurable)
   - Checks for tasks due soon or overdue
   - Logs notification activity

### Implementation Note

The notification system is designed to be non-blocking, with email operations occurring in background threads to prevent impact on the main application performance.

## Security Considerations

The application implements several security measures:

1. **Input Validation**: All user inputs are validated before processing
2. **CSRF Protection**: All forms use CSRF tokens
3. **Password Security**: Passwords are hashed using secure algorithms
4. **Audit Logging**: All significant actions are logged
5. **Parameterized Queries**: SQL injection protection

Areas for enhancement:
- Consider implementing rate limiting for login attempts
- Add Multi-Factor Authentication support
- Implement more granular role-based access control

## Development Workflow

### Setting Up Development Environment

1. Clone the repository
2. Use Docker Compose for local development:
   ```
   docker compose up -d
   ```
3. Initialize the database:
   ```
   docker compose exec web python seed_db.py
   ```

### Making Changes

1. Create a feature branch
2. Implement changes following the existing patterns
3. Run structure_check_script.py to validate code structure
4. Test changes locally
5. Submit pull request

## Docker Configuration

The application is containerized using Docker with the following components:

1. **Web Application Container**:
   - Base image: Python 3.13 slim
   - Dependencies installed from requirements.txt
   - Uses gunicorn as the WSGI server
   - Contains the entrypoint script for automatic database initialization

2. **Database Container**:
   - PostgreSQL 15 database
   - Persistent volume for data storage
   - Port 5432 exposed for external connections

The `docker-compose.yml` file coordinates these containers and provides the networking setup.

Notable Docker configurations:

1. The `PYTHONPATH` environment variable in the Dockerfile ensures proper Python module resolution:
   ```Dockerfile
   ENV PYTHONPATH=/app:/app/cmmc_tracker
   ```

2. The Docker entrypoint script (`docker-entrypoint.sh`) handles:
   - Waiting for the database to be ready before starting the application
   - Checking if the database needs initialization
   - Running the seed script if needed
   - Starting the web application

3. Data persistence is managed through a named volume:
   ```yaml
   volumes:
     postgres_data:
   ```

## Database Initialization

The database initialization is automated through the `docker-entrypoint.sh` script and `seed_db.py`:

1. **Automatic Seeding**:
   - When the application starts, `docker-entrypoint.sh` checks if the database is empty
   - If empty or if tables don't exist, it runs the seed script
   - If data exists, it skips initialization

2. **Seed Script (`seed_db.py`)**:
   - Creates database tables if they don't exist
   - Imports CMMC controls from cmmc_controls.json
   - Creates default admin and regular user accounts
   - Generates sample tasks for demonstration

3. **Reset Process**:
   To completely reset the database and start fresh:
   ```
   docker compose down -v  # The -v flag removes volumes
   docker compose up -d    # Database will be automatically initialized
   ```

4. **Database Schema Evolution**:
   Currently, the application doesn't include formal migrations. Schema changes should be managed by:
   - Updating the table creation logic in `seed_db.py`
   - Documenting the changes for manual application to existing databases
   - Future enhancement: Implement proper database migrations

## Common Issues and Troubleshooting

### Circular Import Dependencies

The application has potential circular dependencies between modules that need to be carefully managed:

1. **Email and Utils**: There's a circular dependency risk between `app/services/email.py` and `app/utils/__init__.py`. The utils module should not directly import from the email service.

2. **Models and Services**: Models often need to use services, while services need to use models. To avoid circular imports:
   - Break out shared functionality into separate utility modules
   - Use function-level imports rather than module-level imports where appropriate
   - Ensure proper layering of dependencies

3. **Scheduler and Email Service**: The scheduler service imports the email service's notification function. Ensure the email service doesn't directly import the scheduler to avoid circular dependencies.

### URL Routing Issues

Common URL routing problems and solutions:

1. **Missing Routes**: Ensure all URLs referenced in templates correspond to defined routes in the blueprint files.

2. **Blueprint Naming**: Each blueprint has a unique name and URL prefix. Make sure they are consistent throughout the application.

3. **CSRF Error Handling**: The CSRF error handler should redirect to a valid endpoint:
   ```python
   @app.errorhandler(CSRFError)
   def handle_csrf_error(e):
       app.logger.error(f"CSRF error: {e}")
       flash('The form you submitted is invalid or has expired. Please try again.', 'danger')
       return redirect(url_for('controls.index'))
   ```

### Database Connection Issues

If you encounter database connection problems:

1. Verify the database container is running: `docker compose ps`
2. Check database logs: `docker compose logs db`
3. Ensure the database credentials in `docker-compose.yml` match the ones expected by the application
4. Check that database initialization completed successfully in the logs: `docker compose logs web`

### Template Rendering Errors

Common template issues include:

1. **Undefined variables**: Always provide all required variables to `render_template()`
2. **URL building errors**: Verify all `url_for()` calls reference valid endpoints
3. **CSRF token issues**: Ensure all forms include the CSRF token: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
4. **Chart.js rendering**: If charts aren't displaying, check the console for JavaScript errors and ensure data is properly formatted

### Notification System Issues

If email notifications aren't working:

1. **Configuration**: Verify MAIL_* settings in config.py match your mail server
2. **Scheduler**: Check if the scheduler initialized correctly in the logs
3. **Manual Test**: Use the admin interface to manually trigger notifications
4. **Flask-APScheduler**: Ensure the package is installed and properly configured

### Import/Export Issues

Common problems with the import/export functionality:

1. **CSV Format**: Exported CSV files should be compatible with the import functionality
2. **Headers**: Ensure CSV headers match the expected column names
3. **Date Formats**: Dates should be in YYYY-MM-DD format for proper parsing
4. **File Size**: Large imports might require adjusting the maximum file size in the Flask configuration

## Testing

The application currently lacks formal tests, which is an area for improvement.

Recommended testing strategy:
1. Add unit tests for models and services
2. Implement integration tests for routes and user flows
3. Set up CI/CD pipeline with automated testing
4. Add end-to-end tests for critical user journeys

### Priority Testing Areas

For the new features, prioritize testing of:
1. Dashboard data aggregation accuracy
2. CSV import validation and error handling
3. Email notification scheduling and delivery
4. Automatic database initialization

---

This documentation is intended to be a living document. As the application evolves, please keep it updated to reflect the current state of the codebase. 