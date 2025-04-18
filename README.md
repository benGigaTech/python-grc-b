# CMMC Compliance Tracker

A Flask-based web application for tracking and managing Cybersecurity Maturity Model Certification (CMMC) compliance controls.

## Overview

The CMMC Compliance Tracker helps organizations manage their cybersecurity controls, track compliance tasks, and maintain audit logs for CMMC certification requirements. It provides a centralized platform for:

- Managing CMMC and NIST SP 800-171 controls
- Assigning and tracking compliance tasks
- Conducting control reviews
- Managing evidence for compliance controls
- Generating compliance reports
- Maintaining detailed audit logs

## Features

- **Interactive Dashboard**: Visual overview of compliance status with metrics and charts, optimized with caching and performance monitoring
- **Control Management**: Create, update, and track cybersecurity controls
- **Bulk Import/Export**: Easily import or export controls in CSV format
- **Task Assignment**: Assign tasks to team members with due dates and status tracking
- **Interactive Calendar**: Visual calendar with paginated tables for control reviews and tasks
- **Evidence Management**: Upload, track, and manage compliance evidence files with metadata
- **User Management**: Role-based access control with admin capabilities
- **Multi-Factor Authentication**: Time-based One-Time Password (TOTP) support with backup codes
- **Account Security**: Account lockout after multiple failed login attempts with admin unlock capability
- **Audit Logging**: Comprehensive audit trail for compliance activities
- **Reporting**: Generate compliance status reports and dashboards
- **Email Notifications**: Automated alerts for task assignments and upcoming deadlines
- **Responsive Design**: Optimized for both desktop and mobile devices

## Technology Stack

- **Backend**: Python, Flask, SQLite
- **Frontend**: Bootstrap, Jinja2 templates, Progress Bars and Responsive Tables
- **Authentication**: Flask-Login with password hashing
- **Database**: SQLite for development, PostgreSQL for production
- **Docker**: Containerized for easy deployment
- **Task Scheduling**: Flask-APScheduler

## Getting Started

### Prerequisites

- Docker and Docker Compose installed

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/benGigaTech/python-grc-b
   cd python-grc-b
   ```

2. Start the application using Docker Compose:
   ```
   docker compose up -d
   ```

3. Access the application at http://localhost:80

The database schema is automatically migrated on startup. Initial sample data (users, controls) is seeded if the `RUN_FULL_SEED` environment variable is set to `true` (default is `true` in `docker-compose.yml`).

### Running Tests

The application includes a testing framework with unit, integration, and functional tests. To run the tests:

1. Start the test environment:
   ```
   docker compose -f docker-compose.test.yml up -d
   ```

2. Run the tests:
   ```
   docker compose -f docker-compose.test.yml exec web pytest -v tests/
   ```

3. Run specific test categories:
   ```
   # Run only unit tests
   docker compose -f docker-compose.test.yml exec web pytest -v tests/unit/

   # Run only tests for models
   docker compose -f docker-compose.test.yml exec web pytest -v -m models

   # Run only tests for utilities
   docker compose -f docker-compose.test.yml exec web pytest -v -m utils
   ```

### Database Migrations

Database schema migrations are handled automatically when the `web` container starts. The `docker-entrypoint.sh` script performs the following steps:

1.  Waits for the PostgreSQL database (`db` service) to become available.
2.  Ensures the `migration_history` table exists (by running `db/02_migration_tracking.sql`).
3.  Iterates through all `db/0*.sql` files in numerical order.
4.  For each script, it checks the `migration_history` table.
5.  If the script has not been applied previously, it executes the script using `psql`.
6.  On successful execution, it records the script filename in the `migration_history` table.

This ensures that the database schema is always up-to-date with the SQL scripts present in the `db/` directory. Manual migration application is generally not required when using Docker Compose.

### Default Credentials

- **Admin User**:
  - Username: admin
  - Password: adminpassword

- **Regular User**:
  - Username: user
  - Password: userpassword

## Evidence Management

The application includes a comprehensive evidence management system for tracking compliance documentation:

### Features

- Upload and store compliance evidence files for specific controls
- Chunked upload support for large files with progress tracking
- Automatic expiration date calculation based on configurable settings
- Track metadata including upload date, expiration date, and status
- View evidence status with color-coded indicators (Current, Pending Review, Expired)
- Download evidence files securely
- Add, update, and delete evidence with proper access controls
- Organize evidence by control for easy compliance verification

### File Support

- Supported file types include PDF, Word documents, Excel spreadsheets, images, and text files
- Each evidence item tracks file size, type, and original filename
- Support for files up to 50MB with chunked upload mechanism
- Automatic file type validation using both extension and content inspection
- Optional expiration dates to manage evidence lifecycle
- Configurable default validity period for evidence files

### Access

Evidence management is accessible from each control's detail page via the "Manage Evidence" button.

## Security Features

### Account Lockout Protection

The application includes account lockout protection to mitigate brute force attacks:

- Accounts are automatically locked after 5 consecutive failed login attempts
- Lockout duration is configurable (default: 15 minutes)
- Failed attempts are tracked for both password and MFA verification
- Administrators can view locked accounts in the admin interface
- Admins can manually unlock accounts when needed
- Account lockout status appears clearly in the user management pages
- Failed login attempts are reset after successful authentication
- All lockout events are thoroughly logged in the audit trail

### Multi-Factor Authentication

The application supports industry-standard TOTP-based multi-factor authentication:

- Time-based One-Time Password (TOTP) compatible with Google Authenticator, Authy, etc.
- QR code generation for easy setup
- Backup codes for emergency access
- Administrator capability to reset MFA for users

## Performance Features

The application includes several performance optimizations to ensure fast response times and efficient resource usage:

### Dashboard Performance

1. **In-memory Caching**: Dashboard data is cached for 60 seconds (configurable) to reduce database load and improve response times for frequently accessed pages.
2. **Query Profiling**: A built-in profiling system measures and logs database query execution times, helping identify and optimize slow queries.
3. **Optimized SQL**: Complex dashboard queries use Common Table Expressions (CTEs) to improve database performance.
4. **Performance Monitoring**: Administrators can access a dedicated dashboard performance page showing query execution statistics.

### Database Efficiency

1. **Connection Pooling**: Database connections are managed through a connection pool to reduce overhead.
2. **Query Naming**: Queries are named for easier profiling and performance tracking.
3. **Parameterized Queries**: All database queries use parameterization to prevent SQL injection and improve query plan caching.

## Chunked Upload Feature

The application includes a chunked upload mechanism for handling large evidence files:

### How It Works

1. When a user selects a file larger than 5MB in the evidence upload form, the client-side JavaScript automatically switches to chunked upload mode.
2. The file is sliced into smaller chunks (2MB by default) on the client side.
3. Each chunk is uploaded separately to the server using the Fetch API.
4. A progress bar shows the upload progress in real-time.
5. Once all chunks are uploaded, they are assembled on the server into the complete file.
6. The assembled file is then processed like a regular upload (validation, storage, database entry).

### Benefits

- Prevents timeouts during large file uploads
- Provides visual feedback on upload progress
- Reduces memory usage on both client and server
- Allows for resumable uploads (future enhancement)
- Supports files up to 50MB (configurable)

### Technical Implementation

- Client-side: JavaScript with Fetch API and File API for slicing and uploading chunks
- Server-side: Dedicated service (`chunked_upload.py`) and routes (`chunked_upload_bp`) for handling chunks
- Temporary storage: Chunks are stored in a temporary directory until assembly
- Cleanup: Temporary files are automatically removed after successful upload or on error

## Troubleshooting

### Common Issues

1. **Web container exits after startup**:
   - Check logs with `docker compose logs web`
   - Common causes include Python import errors or missing dependencies
   - Solution: Ensure PYTHONPATH is correctly set in the Dockerfile

2. **Circular dependencies**:
   - Symptoms: Import errors related to circular imports
   - Solution: Refactor imports or move them into functions

3. **URL building errors**:
   - Symptoms: Errors like `Could not build url for endpoint 'X'`
   - Solution: Ensure routes are correctly named in both route definitions and templates

4. **CSRF errors when submitting forms**:
   - Symptoms: 400 Bad Request - The CSRF token is missing
   - Solution: Ensure forms include the csrf_token field

5. **Email notification issues**:
   - Symptoms: No emails being sent for task notifications
   - Solution: Check mail server configuration in config.py and ensure the scheduler is running

6. **Multi-Factor Authentication (MFA) issues**:
   - Symptoms: QR code not displaying, unable to verify codes, or locked out of account
   - Solutions:
     - Ensure the pyotp library is installed and available
     - Check that the Content Security Policy allows displaying the QR code image
     - For locked accounts, administrators can reset MFA from the user edit page
     - Verify that your authenticator app's time is synchronized correctly
     - Use backup codes if you can't access your authenticator app

7. **Account Lockout Issues**:
   - Symptoms: User account locked or login unsuccessful after multiple attempts
   - Solutions:
     - Wait for the automatic lockout period to expire (default 15 minutes)
     - Ask an administrator to manually unlock the account
     - Check if account is locked in the admin user management interface
     - Review audit logs for unauthorized login attempts

8. **Testing Issues**:
   - Symptoms: Tests failing with database connection errors
   - Solutions:
     - Ensure the test database container is running (`docker compose -f docker-compose.test.yml ps`)
     - Check that the database host in docker-entrypoint.sh matches the service name in docker-compose.test.yml
     - Verify that tests are using the app context when accessing the database
     - For database-dependent tests, use the `init_database` fixture
     - Skip tests that require complex database setup with `@pytest.mark.skip`
     - If you encounter hostname resolution issues, the database service now automatically tries to connect using the Docker container name format (e.g., `python-grc-b-db_test-1`) if the initial connection fails

9. **Chunked Upload Issues**:
   - Symptoms: Large file uploads fail, progress bar gets stuck, or assembled file is corrupted
   - Solutions:
     - Check browser console for JavaScript errors
     - Verify that the Content Security Policy allows fetch API calls to the application's own endpoints
     - Ensure the temporary directory for chunks exists and is writable
     - Check server logs for errors during chunk assembly
     - Verify that the `MAX_CONTENT_LENGTH` setting is large enough for individual chunks
     - If uploads consistently fail at the same percentage, the chunk size might be too large - try reducing it in the JavaScript code
     - For very large files, ensure the server has enough disk space for both chunks and the assembled file

10. **Performance Issues**:
    - Symptoms: Slow dashboard loading, high database CPU usage, or timeouts
    - Solutions:
      - Check the dashboard performance page (accessible to admins from the dashboard)
      - Review slow queries in the application logs (queries taking > 100ms are logged)
      - Ensure database indexes are properly created for frequently queried columns
      - Verify that the database connection pool is properly configured
      - For high-traffic instances, consider increasing the dashboard cache TTL
      - Monitor database connection usage to ensure the pool size is appropriate

## Environment Variables

The application can be configured using the following environment variables:

- `FLASK_CONFIG`: Configuration mode (development, testing, production)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database connection settings
- `SECRET_KEY`: Flask secret key
- `MAIL_*`: Email server configuration settings
- `NOTIFICATION_ENABLED`: Enable/disable email notifications (true/false)
- `NOTIFICATION_HOUR`: Hour of the day to send daily notifications (0-23)
- `RUN_FULL_SEED`: Whether to seed the database with initial data (true/false)
- `DB_MIN_CONNECTIONS`: Minimum number of database connections in the pool (default: 5)
- `DB_MAX_CONNECTIONS`: Maximum number of database connections in the pool (default: 25)
- `MAX_CONTENT_LENGTH`: Maximum allowed file size in bytes (default: 52428800, which is 50MB)
- `CHUNK_SIZE`: Size of each chunk in bytes for chunked uploads (default: 2097152, which is 2MB)
- `UPLOAD_FOLDER`: Directory where uploaded files are stored (default: 'uploads')
- `TEMP_UPLOAD_FOLDER`: Directory where temporary chunks are stored (default: 'uploads/temp')
- `DASHBOARD_CACHE_TTL`: Time-to-live for dashboard cache in seconds (default: 60)
- `PROFILE_SLOW_QUERIES`: Whether to log slow queries (default: true)
- `SLOW_QUERY_THRESHOLD`: Threshold in seconds for logging slow queries (default: 0.1)

### Test Environment Variables

The test environment can be configured using these additional variables in `docker-compose.test.yml`:

- `FLASK_CONFIG`: Set to 'testing' for test-specific configuration
- `DB_HOST`: Set to 'db_test' to use the test database container
- `PYTHONPATH`: Set to '/app' to ensure proper module imports during testing

## Project Structure

The application follows a modular structure to maintain clean separation of concerns:

```
/
├── cmmc_tracker/           # Main application package
│   ├── app/                # Core application code
│   │   ├── models/         # Data models
│   │   ├── routes/         # Route definitions (blueprints)
│   │   │   ├── auth.py     # Authentication routes
│   │   │   ├── controls.py # Control management routes
│   │   │   ├── evidence.py # Evidence management routes
│   │   │   ├── chunked_upload.py # Chunked file upload routes
│   │   │   └── ...         # Other route blueprints
│   │   ├── services/       # Business logic services
│   │   │   ├── database.py # Database connection service
│   │   │   ├── storage.py  # File storage service
│   │   │   ├── chunked_upload.py # Chunked upload service
│   │   │   └── ...         # Other services
│   │   ├── templates/      # Jinja2 HTML templates
│   │   ├── utils/          # Utility functions
│   │   │   ├── profiler.py # Performance monitoring utilities
│   │   └── __init__.py     # Application factory
│   ├── config.py           # Configuration classes
│   └── run.py              # Application entry point
├── db/                     # Database migration scripts
├── memory-bank/            # Project documentation
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── functional/         # Functional tests
│   └── conftest.py         # Test fixtures and configuration
├── docker-compose.yml      # Docker configuration
├── docker-compose.test.yml # Test environment configuration
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── seed_db.py              # Database seeding script
```

### Key Support Scripts

- **apply_migration.py**: Handles database schema migrations
- **docker-entrypoint.sh**: Container startup script that initializes the database
- **seed_db.py**: Populates the database with initial data
- **start.sh**: Starts the application within the container

## Maintenance

This repository has been cleaned to remove development artifacts and temporary files. The core application code, configuration files, and documentation have been preserved.

### Documentation

Detailed project documentation is available in the `memory-bank` directory:

- **productContext.md**: Overview of the problem space and solution
- **projectbrief.md**: Core requirements and project goals
- **techContext.md**: Technical architecture and technology stack
- **roadmap.md**: Future development plans
- **systemPatterns.md**: Design patterns and architectural decisions

