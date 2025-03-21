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
15. [Database Migrations](#database-migrations)

## Architecture Overview

The CMMC Tracker is a Flask-based web application following a layered architecture pattern:

- **Presentation Layer**: Flask routes and Jinja2 templates with responsive progress bars and table-based visualizations
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

The application features a comprehensive dashboard with visualizations to provide insights into compliance status and task management.

### Main Dashboard

The main dashboard displays:

1. **Summary Cards**: Present key metrics in a quickly scannable format
   - Total Controls Count
   - Overdue Tasks Count
   - Pending Tasks Count
   - Controls Due for Review Count

2. **Compliance Status Visualization**: 
   - Uses responsive progress bars to show compliance metrics
   - Color-coded indicators for different compliance statuses
   - Shows percentages for Compliant, In Progress, Non-Compliant, and Not Assessed controls
   - Implemented with HTML/CSS for maximum reliability

3. **Task Status Visualization**:
   - Displays distribution of tasks by status
   - Uses simple progress bars for reliable visualization
   - Color-coded indicators for different task statuses
   - JavaScript-enhanced but with progressive enhancement

4. **Recent Activities**: 
   - Table showing recent activity logs
   - Helps track changes in the system

5. **My Tasks**:
   - Personalized view of assigned tasks
   - Prioritized display with overdue tasks highlighted
   - Direct links to task details

### Admin Dashboard

The admin dashboard provides additional features for administrators:

1. **Tasks by User**:
   - Breakdown of tasks assigned to each user
   - Statistics on open, pending, and completed tasks

2. **Overdue Tasks**:
   - Comprehensive list of all overdue tasks
   - Days overdue calculation for prioritization

3. **Site Activity Logs**:
   - Recent system activity for auditing purposes
   - User actions tracking for compliance
   - Timestamp display of when activities occurred

4. **Past Due Control Reviews**:
   - Controls that have missed review dates
   - Days overdue calculation for prioritization

### Calendar View

The calendar view combines a visual calendar with tables for a comprehensive event tracking experience:

1. **Interactive Calendar Component**:
   - Visual month-based calendar showing control review dates
   - Color-coded indicators for different event types (past due, upcoming, scheduled)
   - Navigation controls for moving between months
   - Highlights the current day for easier reference
   - Completely JavaScript-based for dynamic interaction

2. **Summary Cards**:
   - Overview metrics showing total control reviews, past due items, and tasks
   - Quick visual indicators of system status
   - Numeric counters for at-a-glance information

3. **Upcoming Events Panel**:
   - Focused view of events due in the next 30 days
   - Card-based layout with clear date indicators
   - Direct links to relevant controls

4. **Control Reviews Table with Pagination**:
   - Lists control reviews in chronological order with page navigation
   - Status indicators for past due or upcoming reviews
   - Color-coded rows based on status for easier scanning
   - Direct links to control details
   - Pagination controls for navigating large datasets
   - Shows total count of controls in the header

5. **Tasks Table with Pagination**:
   - Shows tasks with due dates and pagination for large datasets
   - Includes status indicators with consistent color coding
   - Direct links to task editing
   - Pagination controls allow browsing through all tasks
   - Displays total task count in the header

This approach combines the benefits of visualization (calendar) with detailed, paginated data (tables) to provide a complete view of upcoming compliance activities. The design is responsive and works well on both desktop and mobile devices.

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

### Import/Export Issues

Common problems with the import/export functionality:

1. **CSV Format**: Exported CSV files should be compatible with the import functionality
2. **Headers**: Ensure CSV headers match the expected column names
3. **Date Formats**: Dates should be in YYYY-MM-DD format for proper parsing
4. **File Size**: Large imports might require adjusting the maximum file size in the Flask configuration

### Audit Log Issues

When working with the audit log system, be aware of these common issues:

1. **Timestamp Format**: Audit log timestamps are stored as ISO format strings, not datetime objects
   - Do not attempt to call `strftime()` on these values in templates
   - Example error: `'str object' has no attribute 'strftime'`
   - Use the timestamp string directly in templates: `{{ log.timestamp }}`

2. **Database Connection**: Ensure proper connection when querying large numbers of audit logs
   - Large result sets may cause timeout issues
   - Use appropriate LIMIT clauses for pagination

3. **Event Tracking**: When adding new features, remember to add corresponding audit log entries
   - All important user actions should be logged
   - Include object IDs where applicable for proper tracking

4. **Admin Dashboard**: The Site Activity Logs section requires audit logs to be available
   - If logs are missing, check the audit log service implementation
   - Verify that audit log entries are being created correctly

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

The CMMC Tracker implements several security best practices:

### Recent Security Improvements

As part of our continuous security enhancement efforts, the following improvements have been implemented:

1. **Password Strength Enforcement** ✅
   - Added required password complexity validation during registration and password changes
   - Ensures passwords meet minimum security requirements (length, character types)
   - Implemented in both user self-registration and admin user creation
   - Prevents users from creating weak passwords that could be easily compromised

2. **Security Headers Implementation** ✅
   - Added critical HTTP security headers to all responses:
     - X-Content-Type-Options: Prevents MIME type sniffing
     - X-XSS-Protection: Enables browser's XSS filtering
     - X-Frame-Options: Prevents clickjacking attacks
     - Strict-Transport-Security: Enforces HTTPS connections
     - Content-Security-Policy: Restricts resource loading sources
   - Implemented using Flask's @app.after_request decorator to apply headers to all responses

3. **Enhanced Password Reset Security** ✅
   - Improved password reset token security with one-time use enforcement
   - Added additional validation to verify tokens haven't been used already
   - Enhanced error logging for security events
   - Prevents token reuse attacks

4. **IDOR Protection Improvements** ✅
   - Added ownership validation for all resource access in task management
   - Implemented proper authorization checks on all endpoints
   - Added audit logging for unauthorized access attempts
   - Prevents unauthorized users from viewing, editing, or deleting resources they shouldn't access

5. **Rate Limiting for Authentication** ✅
   - Implemented rate limiting on authentication endpoints using Flask-Limiter
   - Added limit of 10 login attempts per minute to prevent brute force attacks
   - Added limit of 5 registration and password reset requests per hour to prevent abuse
   - Enhanced logging for failed login attempts to track potential attackers

6. **Other Security Enhancements** (Pending)
   - Improved input validation and sanitization
   - Enhanced error handling to avoid information disclosure
   - Added comprehensive security event logging

### Existing Security Features

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
   - Uses start.sh script for database initialization and application startup

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

2. The startup script (`start.sh`) handles:
   - Waiting for the database to be ready before starting the application
   - Checking if the database needs initialization
   - Running the seed script if needed
   - Starting the web application with gunicorn

3. Data persistence is managed through a named volume:
   ```yaml
   volumes:
     postgres_data:
   ```

4. Simplified Dockerfile structure:
   ```Dockerfile
   # Use an official Python runtime as a parent image
   FROM python:3.13-slim
   
   # Set up working directory
   WORKDIR /app
   
   # Copy requirements first for better caching
   COPY requirements.txt /app/
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy the rest of the application
   COPY . /app/
   
   # Make the start script executable
   RUN chmod +x /app/start.sh
   
   # Make port 80 available outside the container
   EXPOSE 80
   
   # Set Python path
   ENV PYTHONPATH=/app:/app/cmmc_tracker
   
   # Run the start script
   CMD ["/app/start.sh"]
   ```

## Database Initialization

The database initialization is automated through the `start.sh` script and `seed_db.py`:

1. **Automatic Database Connection Check**:
   - When the application starts, `start.sh` waits for the database to be ready
   - Retries connection up to 30 times with 2-second intervals
   - Provides clear logging of connection attempts

2. **Improved Seeding Process**:
   - `seed_db.py` has been enhanced with robust checks to determine if initialization is needed
   - Checks for existing tables and data before attempting to create or populate
   - Connection pooling and retry logic for better reliability
   - Comprehensive logging of the initialization process

3. **Smart Initialization Logic**:
   - Only creates tables if they don't exist
   - Only adds users, controls, and sample tasks if they don't already exist
   - Prevents duplicate data and errors when restarting the application

4. **Reset Process**:
   To completely reset the database and start fresh:
   ```
   docker compose down -v  # The -v flag removes volumes
   docker compose up --build -d  # Rebuild containers and restart with fresh database
   ```

5. **Validation and Testing**:
   - Includes a `test_auth.py` script to verify authentication is working properly
   - Tests can be run manually to validate database setup:
   ```
   docker compose exec web python /app/test_auth.py
   ```

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

### Docker Container Issues

Common Docker container issues and their solutions:

1. **Container won't start**:
   - Check Docker logs: `docker compose logs web`
   - Verify port availability: Make sure port 80 is not already in use
   - Check environment variables: Ensure all required variables are set

2. **Container starts but application is inaccessible**:
   - Check if gunicorn is running: `docker compose exec web ps aux | grep gunicorn`
   - Verify port mappings: Ensure port 80 is correctly mapped in docker-compose.yml
   - Check application logs for errors: `docker compose logs web`

3. **Database initialization issues**:
   - Check if the script ran: Look for "Database initialization complete" in logs
   - Verify database volume: Ensure it's created with `docker volume ls`
   - Try manual initialization: `docker compose exec web python /app/seed_db.py`

4. **Changes to code not reflected in container**:
   - You need to rebuild the container: `docker compose up --build -d`
   - Check bind mounts: For development, consider using bind mounts instead of copying files

5. **Authentication testing**:
   - Use the test_auth.py script: `docker compose exec web python /app/test_auth.py`
   - Check user table directly: `docker compose exec db psql -U cmmc_user -d cmmc_db -c "SELECT username, isadmin FROM users;"`

### Template Rendering Errors

Common template issues include:

1. **Undefined variables**: Always provide all required variables to `render_template()`
2. **URL building errors**: Verify all `url_for()` calls reference valid endpoints
3. **CSRF token issues**: Ensure all forms include the CSRF token: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
4. **Progress bar calculations**: If dashboard progress bars aren't displaying correctly, ensure the metrics data is properly calculated and division by zero is handled

### Notification System Issues

If email notifications aren't working:

1. **Configuration**: Verify MAIL_* settings in config.py match your mail server
2. **Scheduler**: Check if the scheduler initialized correctly in the logs
3. **Manual Test**: Use the admin interface to manually trigger notifications
4. **Flask-APScheduler**: Ensure the package is installed and properly configured

## Testing

The application currently lacks formal tests, which is an area for improvement.

Recommended testing strategy:
1. Add unit tests for models and services
2. Add integration tests for database operations 
3. Add end-to-end tests for critical user workflows

## UI Implementation Notes

The user interface has been simplified to avoid dependencies on complex JavaScript libraries:

1. **Dashboard UI**: The dashboard uses simple HTML progress bars instead of Chart.js to display metrics. This approach:
   - Reduces JavaScript dependencies
   - Improves compatibility across browsers
   - Simplifies maintenance
   - Is more reliable in containerized environments

2. **Calendar UI**: The calendar view has been implemented as a simple table-based display instead of using FullCalendar. This approach:
   - Eliminates JavaScript initialization issues
   - Improves loading time and performance
   - Provides better accessibility
   - Works more consistently across different environments

3. **General UI Principles**:
   - Prefer server-side rendering for complex data display
   - Minimize client-side JavaScript dependencies
   - Use simple, reliable UI components
   - Implement graceful fallbacks for all dynamic features

4. **Admin Dashboard Enhancements**:
   - Added Site Activity Logs to replace Upcoming Control Reviews
   - Improved visibility into user actions and system changes
   - Enhanced audit capabilities for administrators
   - Better tracking of changes for compliance purposes
   - Timestamp display optimized for readability
   - Table-based interface for better sorting and scanning of activities

These UI simplifications make the application more robust, especially in containerized environments where browser compatibility and JavaScript execution might be less predictable.

## Database Migrations

### Overview

The CMMC Compliance Tracker application now supports database migrations for schema evolution. This allows for adding new tables, columns, and other database objects in a controlled manner.

### Migration System

The migration system consists of:

1. **SQL Migration Files** - Located in the `/db` directory with descriptive names (e.g., `evidence_migration.sql`)
2. **Migration Tracking Table** - A table in the database that tracks which migrations have been applied
3. **Migration Application Script** - The `apply_migration.py` script that handles applying migrations

### How to Apply Migrations

For local development:
```
python apply_migration.py
```

In Docker environment:
```
docker compose exec web python apply_migration.py
```

### How to Create New Migrations

1. Create a new SQL file in the `/db` directory with a descriptive name
2. Use the numbered file format to ensure correct execution order (e.g., `04_add_custom_field.sql`)
3. Use the template pattern for idempotent operations:

```sql
-- Check if the feature exists before creating it
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'table_name') THEN
        -- Create the table/column/etc.
        CREATE TABLE table_name (...);
        
        RAISE NOTICE 'Created table_name';
    ELSE
        RAISE NOTICE 'table_name already exists';
    END IF;
END $$;
```

4. Add proper error handling and logging in the SQL script
5. Test the migration thoroughly before committing

### Docker Initialization

When running in Docker, the PostgreSQL container executes SQL files in the `docker-entrypoint-initdb.d` directory in alphabetical order. This is why we use a numbered prefix format (`01_`, `02_`, etc.) for migration files to ensure they run in the correct sequence.

The sequence is important because:
1. Base tables must be created first
2. The migration tracking table should be created next
3. Feature-specific migrations can then be applied

If migrations fail during Docker initialization, check the database logs with `docker compose logs db`.

### Verification

After applying migrations, you can verify that they were applied correctly:

```
python check_evidence_table.py
```

This will check if the evidence table exists and output its structure and indexes.

### Best Practices

1. Migrations should be forward-only (no rollbacks)
2. Make migrations idempotent so they can be safely re-run
3. Add proper documentation in the SQL file header about what the migration does
4. Keep migrations focused on a single concern (e.g., adding one table or feature)
5. Use transactions where appropriate
6. Avoid direct data manipulation in migrations when possible

---

This documentation is intended to be a living document. As the application evolves, please keep it updated to reflect the current state of the codebase. 

## Security Improvements Summary

In our recent security overhaul, we've implemented several critical improvements to enhance the application's security posture:

1. **Password Strength Enforcement**
   - Implemented in both user self-registration and admin user management
   - Enforces minimum length and character requirements
   - Prevents common password vulnerabilities

2. **HTTP Security Headers**
   - Added comprehensive security headers to all responses
   - Prevents common web vulnerabilities like XSS, clickjacking, and MIME sniffing
   - Enforces HTTPS through HSTS headers

3. **Rate Limiting**
   - Protected authentication endpoints from brute force attacks
   - Implemented tiered limits for different sensitive operations
   - Enhanced logging for failed attempts

4. **One-time Password Reset Tokens**
   - Improved token validation to prevent reuse
   - Enhanced security of the password reset flow
   - Added detailed logging of token usage

5. **IDOR Protection**
   - Improved authorization checks throughout the application
   - Added comprehensive audit logging for unauthorized access attempts
   - Enforced proper access control on all resource endpoints

### Future Security Recommendations

For future security enhancements, consider implementing:

1. **Multi-Factor Authentication (MFA)**
   - Add support for TOTP-based 2FA for admin accounts
   - Implement email verification as a second factor

2. **Advanced Input Validation**
   - Replace the basic sanitize_string function with a more comprehensive solution
   - Consider using a library like bleach for HTML sanitization

3. **Enhanced Logging and Monitoring**
   - Implement centralized logging with structured data
   - Add alerting for suspicious activity
   - Consider integrating with a SIEM solution

4. **Regular Security Scanning**
   - Implement automated security scanning in the CI/CD pipeline
   - Regular dependency vulnerability checks
   - Periodic penetration testing

5. **Server Hardening**
   - Implement more restrictive Content Security Policy
   - Add subnet restrictions for admin access
   - Consider implementing a Web Application Firewall (WAF)

These improvements have significantly enhanced the security of the CMMC Tracker application, reducing the risk of common vulnerabilities and providing better protection against unauthorized access. 