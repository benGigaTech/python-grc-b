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
16. [Redis-Backed Rate Limiting](#redis-backed-rate-limiting)
17. [Multi-Factor Authentication (MFA)](#multi-factor-authentication-mfa)

## Architecture Overview

The CMMC Tracker is a Flask-based web application following a layered architecture pattern:

- **Presentation Layer**: Flask routes and Jinja2 templates with responsive progress bars and table-based visualizations
- **Business Logic Layer**: Models and Services
- **Data Access Layer**: Database service abstraction over PostgreSQL
- **Infrastructure**: Docker containers for the web app, PostgreSQL database, and Redis
- **Background Processing**: Flask-APScheduler for automated email notifications
- **Rate Limiting**: Redis-backed rate limiting via Flask-Limiter

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
   - Configured Redis as persistent storage backend for rate limiting keys

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
6. **Redis-backed Rate Limiting**: Distributed and persistent rate limiting for authentication endpoints

Areas for enhancement:
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

3. **Redis Container**:
   - Redis 7-alpine image for rate limiting storage
   - Persistent volume for data storage
   - Configured to save data every 60 seconds
   - Port 6379 exposed for external connections

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

3. Data persistence is managed through named volumes:
   ```yaml
   volumes:
     postgres_data:
     redis_data:
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

6. **Rate Limiting Issues**:
   - Check Redis connection: `docker compose exec redis redis-cli ping`
   - View rate limiting keys: `docker compose exec redis redis-cli keys "*LIMITS*"`
   - Check rate limit value: `docker compose exec redis redis-cli get "LIMITS:LIMITER/[IP_ADDRESS]/auth.login/10/1/minute"`
   - Reset rate limits: `docker compose exec redis redis-cli flushall`

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

## Evidence Management System

The CMMC Tracker now includes a comprehensive evidence management system that allows users to upload, track, and manage compliance evidence files associated with specific controls.

### System Components

1. **Database Schema**:
   - The evidence table stores metadata about uploaded files
   - Created by the `03_evidence_migration.sql` migration
   - Includes fields for file metadata, upload dates, and status tracking
   - Indexed for efficient querying by control ID, upload date, expiration date, and status

2. **Model Layer**:
   - `Evidence` class in `app/models/evidence.py` provides the data model and business logic
   - Handles CRUD operations for evidence records
   - Includes validation and relationship management with controls
   - Provides status logic (Current, Pending Review, Expired)

3. **Routes and Controllers**:
   - Implemented in `app/routes/evidence.py`
   - Provides endpoints for listing, adding, updating, downloading, and deleting evidence
   - Includes access control and validation logic
   - Manages file uploads and secure file serving

4. **Storage Service**:
   - `app/services/storage.py` handles file storage operations
   - Manages directory creation and file saving
   - Handles secure filename generation
   - Enforces file type restrictions

5. **Templates**:
   - `evidence_list.html`: List view of evidence for a control with sorting and pagination
   - `add_evidence.html`: Form for uploading new evidence
   - `update_evidence.html`: Form for updating evidence metadata

### Status Indicators

Evidence status is visualized using color-coded badges:
- **Current** (Green): Valid and up-to-date evidence
- **Pending Review** (Yellow): Evidence that needs review or validation
- **Expired** (Red): Evidence past its expiration date

The status is determined automatically based on the expiration date or can be manually set during updates.

### File Handling

1. **File Upload Process**:
   - Files are validated for allowed types (`ALLOWED_EXTENSIONS` in config)
   - Secure filenames are generated to prevent path traversal
   - Files are stored in a structured directory hierarchy by control ID
   - File metadata (size, type, path) is stored in the database

2. **File Download Process**:
   - Files are served securely with proper MIME types
   - Downloads are logged in the audit system
   - Access control ensures only authorized users can download files

3. **File Storage Structure**:
   - Base directory: `/app/uploads/evidence/`
   - Files organized by control ID: `/app/uploads/evidence/{control_id}/`
   - Filenames include timestamps to prevent collisions

### Sample Data

For testing purposes, the system includes a script to generate sample evidence records:
- `add_sample_evidence.py` creates test evidence records for controls
- Sample data includes various file types and statuses
- To add sample evidence: `docker compose exec web python /app/add_sample_evidence.py`

### Implementation Notes

1. **Evidence Model Design**:
   - Implements a lazy-loaded relationship to the Control model
   - Provides helper properties like `is_expired` and `filename`
   - Uses the database service layer for operations

2. **Access Control**:
   - All evidence operations require authentication
   - Only admin users can delete evidence
   - All users can view and download evidence

3. **Future Enhancements**:
   - Consider implementing file versioning
   - Add support for evidence approval workflows
   - Implement file content indexing for search
   - Add direct file previews for common formats

### Troubleshooting Evidence Issues

Common issues with the evidence management system:

1. **Upload Directory Permissions**:
   - If file uploads fail, check that the web container has write permissions to the uploads directory
   - Verify the directory exists and is created if missing

2. **File Size Limitations**:
   - Default maximum file size is 16MB
   - To change, modify `MAX_CONTENT_LENGTH` in the Flask configuration

3. **Missing Evidence Table**:
   - If the evidence feature is not working, verify the evidence migration was applied
   - Run `python check_evidence_table.py` to verify the table exists
   - If missing, apply the migration: `python apply_migration.py db/03_evidence_migration.sql`

4. **File Download Issues**:
   - Ensure the file exists at the stored path
   - Verify the MIME type is correctly set in the database
   - Check that send_file is configured correctly for the deployment environment

### Redis Implementation Issues

If you encounter issues with the Redis-backed rate limiting:

1. **Connection issues**:
   - Verify the Redis container is running: `docker compose ps`
   - Check Redis logs: `docker compose logs redis`
   - Ensure the Redis URL in the configuration matches what's expected by Flask-Limiter

2. **Rate limiting not working**:
   - Check that Redis keys are being created using: `docker compose exec redis redis-cli keys "*LIMITS*"`
   - Verify rate limits are correctly specified in the route decorators
   - Ensure the Flask-Limiter extension is properly initialized in `app/__init__.py`

3. **Redis data persistence**:
   - Redis is configured to save snapshots every 60 seconds
   - If Redis data is unexpectedly lost, check if the redis_data volume exists: `docker volume ls`
   - Verify the Redis save configuration with: `docker compose exec redis redis-cli config get save`

## Redis-Backed Rate Limiting

The application now uses Redis as a persistent storage backend for rate limiting through Flask-Limiter. This implementation provides several advantages over the default in-memory storage:

1. **Persistence**: Rate limiting data persists across application restarts, ensuring consistent protection against abuse
2. **Scalability**: Redis allows for distributed rate limiting when running multiple application instances
3. **Configurability**: Time-to-Live (TTL) for rate limit windows is automatically managed
4. **Monitoring**: Rate limiting statistics can be easily monitored through Redis commands

### Implementation Details

1. **Configuration**:
   - Redis settings are defined in `config.py`:
     ```python
     # Redis settings for Flask-Limiter
     REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
     REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
     REDIS_DB = int(os.environ.get('REDIS_DB', 0))
     REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
     REDIS_URL = os.environ.get('REDIS_URL', f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
     ```
   - Redis container in `docker-compose.yml` is configured with persistence:
     ```yaml
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       command: redis-server --save 60 1 --loglevel warning
     ```

2. **Flask-Limiter Integration**:
   - Initialization in `app/__init__.py`:
     ```python
     # Initialize limiter with None storage - will be configured in create_app
     limiter = Limiter(
         key_func=get_remote_address,
         default_limits=["200 per day", "50 per hour"],
         storage_uri=None  # Will be set in create_app
     )

     def create_app(config_name=None):
         # ...
         redis_uri = app.config.get('REDIS_URL')
         # ...
         # Configure Limiter with appropriate storage
         if redis_uri:
             app.config['RATELIMIT_STORAGE_URI'] = redis_uri
         limiter.init_app(app)
     ```

3. **Rate Limits Applied**:
   - Authentication routes (`auth.py`):
     - Login: `@limiter.limit("10 per minute")`
     - Registration: `@limiter.limit("5 per hour")`
     - Password reset request: `@limiter.limit("5 per hour")`
   - Admin routes (`admin.py`):
     - Create user: `@limiter.limit("5 per hour")`
     - Edit user: `@limiter.limit("10 per hour")`
     - Delete user: `@limiter.limit("5 per hour")`
     - Send test notifications: `@limiter.limit("3 per hour")`
   - Evidence routes (`evidence.py`):
     - Add evidence: `@limiter.limit("20 per hour")`
     - Download evidence: `@limiter.limit("30 per hour")`
     - Delete evidence: `@limiter.limit("10 per hour")`
     - Update evidence: `@limiter.limit("20 per hour")`

### Verifying Redis Rate Limiting

You can verify that the Redis-backed rate limiting is working correctly using the following commands:

1. **Check active rate limits**:
   ```
   docker compose exec redis redis-cli keys "*LIMITS*"
   ```

2. **Check specific endpoint rate limit**:
   ```
   docker compose exec redis redis-cli keys "*auth.login*"
   ```

3. **Check current count for a specific limit**:
   ```
   docker compose exec redis redis-cli get "LIMITS:LIMITER/[IP_ADDRESS]/auth.login/10/1/minute"
   ```

4. **Check TTL for a rate limit key**:
   ```
   docker compose exec redis redis-cli ttl "LIMITS:LIMITER/[IP_ADDRESS]/auth.login/10/1/minute"
   ```

Rate limit keys in Redis follow the format:
```
LIMITS:LIMITER/[IP_ADDRESS]/[ROUTE]/[LIMIT_COUNT]/[LIMIT_PERIOD]/[LIMIT_UNIT]
```

Example: `LIMITS:LIMITER/172.20.0.1/auth.login/10/1/minute` indicates a limit of 10 requests per minute for the auth.login endpoint from IP 172.20.0.1.

### Troubleshooting

1. **Rate limits not being enforced**:
   - Ensure Redis is running: `docker compose ps`
   - Verify the Redis connection in the application logs
   - Check that the Redis URI is correctly configured and used
   - Confirm that the rate limit decorator is correctly applied to routes

2. **TTL issues**:
   - Redis keys should have appropriate TTLs matching the rate limit window
   - If keys are expiring too quickly or not at all, check Redis configuration
   - Verify Redis persistence configuration with `docker compose exec redis redis-cli config get save`

3. **Resetting rate limits**:
   - For testing purposes, you can flush all rate limits with:
     ```
     docker compose exec redis redis-cli flushall
     ```
   - Or delete specific keys with:
     ```
     docker compose exec redis redis-cli del "LIMITS:LIMITER/[IP_ADDRESS]/[ROUTE]/[LIMIT_COUNT]/[LIMIT_PERIOD]/[LIMIT_UNIT]"
     ```

4. **Redis persistence issues**:
   - Check that the Redis volume is properly mounted
   - Verify that Redis is configured to save data: `docker compose exec redis redis-cli config get save`
   - The current configuration saves after 60 seconds if at least 1 key has changed

This Redis implementation ensures that rate limiting remains effective and persistent in production environments, protecting sensitive endpoints from abuse while maintaining application performance.

## Multi-Factor Authentication (MFA)

The application now supports Time-based One-Time Password (TOTP) multi-factor authentication to enhance security, particularly for administrator accounts.

### MFA Implementation Details

1. **Database Schema**:
   - MFA-related columns have been added to the `users` table via the `04_mfa_migration.sql` migration:
     - `mfa_enabled` (BOOLEAN): Indicates whether MFA is enabled for the user
     - `mfa_secret` (TEXT): Stores the TOTP secret key
     - `mfa_backup_codes` (TEXT): Stores backup codes as a JSON array for use when the authenticator app is unavailable

2. **User Model**:
   - The `User` class in `app/models/user.py` has been extended with MFA-related methods:
     - `enable_mfa()`: Enables MFA and generates backup codes
     - `disable_mfa()`: Disables MFA for the user
     - `verify_backup_code()`: Verifies and consumes a backup code
     - `get_backup_codes()`: Retrieves the user's backup codes

3. **MFA Service**:
   - MFA functionality is encapsulated in `app/services/mfa.py`:
     - `generate_totp_secret()`: Generates a new TOTP secret key
     - `get_totp_uri()`: Creates a URI for QR code generation
     - `generate_qr_code()`: Generates a QR code as a base64-encoded image
     - `verify_totp()`: Verifies a TOTP token

4. **Authentication Flow**:
   - Enhanced login process in `app/routes/auth.py`:
     - If MFA is enabled, the user is redirected to the MFA verification page after password authentication
     - The user must provide a valid TOTP code or backup code to complete login

5. **User Profile Management**:
   - New profile management routes in `app/routes/profile.py`:
     - View profile information
     - Change password with strength validation
     - Set up MFA with QR code for authenticator apps
     - Manage MFA settings (view backup codes, regenerate backup codes, disable MFA)

6. **Admin MFA Management**:
   - Added functionality for administrators to manage user MFA in `app/routes/admin.py`:
     - View MFA status for all users in the user list
     - Reset MFA for any user from the edit user page
     - Audit logging of all MFA reset actions
   - The MFA reset process:
     - Disables MFA for the target user
     - Clears the user's MFA secret and backup codes
     - Records the action in the audit log
     - Administrator is required to confirm the action

### How to Use MFA

1. **Enabling MFA**:
   - Navigate to your profile page
   - Click "Enable Two-Factor Authentication"
   - Scan the QR code with an authenticator app (Google Authenticator, Authy, etc.)
   - Enter the verification code from your app
   - Save your backup codes in a secure location

2. **Logging in with MFA**:
   - Enter your username and password
   - When prompted, enter the TOTP code from your authenticator app
   - Alternatively, use a backup code if you don't have access to your authenticator app

3. **Managing MFA**:
   - View and print backup codes
   - Regenerate backup codes (invalidates previous codes)
   - Disable MFA if necessary (requires password confirmation)

4. **Admin MFA Reset**:
   - Administrators can reset MFA for any user:
     - Navigate to Admin → Users
     - Click "Edit" for the target user
     - In the MFA Status Section, click "Reset MFA" if MFA is enabled
     - The reset is immediate and does not require confirmation from the user
     - The user will need to set up MFA again if required

### Security Considerations

1. **Backup Codes**:
   - Each backup code can only be used once
   - New backup codes can be generated, which invalidates all existing codes
   - Backup codes are stored as a JSON array in the database

2. **TOTP Implementation**:
   - Uses the industry-standard TOTP algorithm (RFC 6238)
   - 30-second time step for code generation
   - 6-digit codes for compatibility with most authenticator apps

3. **Protection Measures**:
   - Rate limiting on MFA verification (10 attempts per minute)
   - Rate limiting on MFA management operations (3 operations per hour)
   - Rate limiting on admin MFA reset (5 resets per hour)
   - Password confirmation required for sensitive operations like disabling MFA

4. **Recovery Options**:
   - Backup codes provide a fallback when the authenticator app is unavailable
   - Administrators can disable MFA for users when needed via the admin interface
   - The admin MFA reset feature provides a simple user support workflow

### Troubleshooting MFA Issues

1. **Synchronization Problems**:
   - If TOTP codes are consistently rejected, check that your device's time is correctly synchronized
   - Time drift on the authenticator device can cause validation failures

2. **Lost Access**:
   - If a user loses access to both their authenticator app and backup codes, an administrator can:
     - Navigate to Admin → Users
     - Click "Edit" for the user in question
     - Use the "Reset MFA" button to disable MFA for the user
     - Alternatively, connect to the database directly and update the user's record:
       ```sql
       UPDATE users SET mfa_enabled = false, mfa_secret = NULL, mfa_backup_codes = NULL WHERE username = 'username';
       ```

3. **QR Code Issues**:
   - If the QR code doesn't scan properly, users can manually enter the secret key into their authenticator app
   - The secret key is displayed on the setup page along with a copy button for convenience

4. **Admin Reset Issues**:
   - If the admin MFA reset fails:
     - Check server logs for detailed error messages
     - Verify that the administrator has proper permissions
     - Make sure the rate limit for MFA resets hasn't been exceeded
     - For persistent issues, use direct database access as a fallback

### Implementation Details for Admin MFA Reset

The admin MFA reset functionality is implemented in `app/routes/admin.py` with the following key components:

1. **Route Definition**:
   ```python
   @admin_bp.route('/users/reset-mfa/<int:user_id>', methods=['POST'])
   @login_required
   @admin_required
   @limiter.limit("5 per hour")
   def admin_reset_mfa(user_id):
       # Implementation details...
   ```

2. **Template Integration**:
   - The MFA status and reset button are displayed in `admin_edit_user.html`
   - The reset button appears only when MFA is enabled for the user

3. **Database Update**:
   - The reset process sets `mfa_enabled` to `false` and clears MFA-related fields
   - SQL query:
     ```sql
     UPDATE users
     SET mfa_enabled = FALSE, mfa_secret = NULL, mfa_backup_codes = NULL
     WHERE userid = %s
     ```

4. **Security Measures**:
   - Rate limiting restricts the reset function to 5 uses per hour
   - Admin permission check ensures only authorized users can perform resets
   - Comprehensive audit logging records all reset actions

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

6. **Account Lockout System**
   - Implemented automatic account lockout after multiple failed login attempts
   - Configurable failed attempt threshold (default: 5 attempts)
   - Configurable lockout duration (default: 15 minutes)
   - Tracks failed attempts for both password and MFA verification
   - Administrative interface for viewing and managing locked accounts
   - Automatic unlocking after lockout period expires
   - Comprehensive audit logging of all lockout events
   - Reset of failed attempt counters upon successful authentication
   - Database schema support with migration script for failure tracking

## Account Lockout Implementation

The account lockout system provides protection against brute force attacks by temporarily locking user accounts after multiple failed authentication attempts.

### Key Components

1. **Database Schema**:
   - `failed_login_attempts`: Integer column in the users table tracking the number of failed attempts
   - `account_locked_until`: Timestamp column indicating when the lockout period expires

2. **Model Implementation** (`app/models/user.py`):
   - `increment_failed_attempts()`: Increments the counter and locks account if threshold reached
   - `is_account_locked()`: Checks if an account is currently locked
   - `reset_failed_attempts()`: Resets counter after successful login
   - `unlock_account()`: Manually unlocks an account (admin function)

3. **Authentication Flow Integration** (`app/routes/auth.py`):
   - Check for account lockout before password validation
   - Increment failed attempts on invalid password
   - Increment failed attempts on invalid MFA code
   - Reset failed attempts on successful authentication
   - Clear lockout status during password reset

4. **Admin Interface** (`app/routes/admin.py` and templates):
   - Display locked accounts in user list with visual indicators
   - Show failed attempts count for all users
   - Provide unlock button for manually unlocking accounts
   - Enhanced user edit page with account status information
   - Audit logging of all unlock actions

### Configuration Constants

The account lockout behavior is controlled by two constants in `app/models/user.py`:
```python
MAX_FAILED_ATTEMPTS = 5  # Number of failed attempts before lockout
LOCKOUT_DURATION = 15    # Lockout duration in minutes
```

These can be adjusted based on security requirements and user experience considerations.

### Database Migration

The account lockout functionality requires two new columns in the users table, added via `05_account_lockout_migration.sql`:
```sql
-- Add column for tracking failed login attempts
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;

-- Add column for tracking when account will be unlocked
ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMPTZ DEFAULT NULL;
```

This migration is designed to be idempotent and can be safely reapplied.

### User Experience

From the user perspective:
1. After 5 consecutive failed login attempts, their account becomes locked
2. A clear message indicates the account is locked with approximate time remaining
3. After the lockout period (15 minutes), the account is automatically unlocked
4. Users can contact administrators for immediate unlocking if needed

From the administrator perspective:
1. The user list shows locked accounts with visual indicators
2. Failed login attempts are displayed for all users
3. The edit user page provides detailed account status
4. Admins can manually unlock accounts with a single click
5. All lockout and unlock events are recorded in the audit log

### Security Considerations

1. **Preventing Enumeration**: Login failure messages do not reveal whether the username exists
2. **Audit Logging**: All lockout and unlock events are thoroughly logged
3. **Admin Override**: Administrators can unlock accounts in case of legitimate lockouts
4. **MFA Integration**: Failed MFA attempts also count toward the lockout threshold
5. **Password Reset**: The password reset process will automatically unlock accounts

### Future Enhancements

Potential improvements to the account lockout system:
1. Progressive timeouts for repeat offenders
2. Email notifications when accounts are locked
3. Self-service unlock via email verification
4. IP-based tracking to detect distributed attacks
5. More granular configuration options for different user types

### Testing

The account lockout system can be tested by:
1. Attempting multiple incorrect logins for a user
2. Verifying the account becomes locked after the threshold
3. Testing that MFA failures contribute to the lockout threshold
4. Verifying an admin can unlock the account
5. Checking that the account automatically unlocks after the timeout period

### Troubleshooting

Common issues with the account lockout system:
1. **Permanent Lockouts**: If a user remains locked after the timeout period, check the timestamp format in `account_locked_until`
2. **Failed Unlock**: If admin unlock fails, check permissions and ensure the admin user has the admin flag set
3. **Missing Lockout Information**: Ensure the migration has been applied to add the required columns
4. **False Positives**: Consider adjusting the threshold if legitimate users are frequently locked

### Future Security Recommendations

For future security enhancements, consider implementing:

1. **Enhanced Input Validation**
   - Replace the basic sanitize_string function with a more comprehensive solution
   - Consider using a library like bleach for HTML sanitization

2. **Enhanced Logging and Monitoring**
   - Implement centralized logging with structured data
   - Add alerting for suspicious activity
   - Consider integrating with a SIEM solution

3. **Regular Security Scanning**
   - Implement automated security scanning in the CI/CD pipeline
   - Regular dependency vulnerability checks
   - Periodic penetration testing

4. **Server Hardening**
   - Implement more restrictive Content Security Policy
   - Add subnet restrictions for admin access
   - Consider implementing a Web Application Firewall (WAF)

These improvements have significantly enhanced the security of the CMMC Tracker application, reducing the risk of common vulnerabilities and providing better protection against unauthorized access. 