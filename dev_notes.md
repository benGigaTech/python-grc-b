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
6. [Security Considerations](#security-considerations)
7. [Development Workflow](#development-workflow)
8. [Docker Configuration](#docker-configuration)
9. [Database Initialization](#database-initialization)
10. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
11. [Testing](#testing)

## Architecture Overview

The CMMC Tracker is a Flask-based web application following a layered architecture pattern:

- **Presentation Layer**: Flask routes and Jinja2 templates
- **Business Logic Layer**: Models and Services
- **Data Access Layer**: Database service abstraction over PostgreSQL
- **Infrastructure**: Docker containers for the web app and PostgreSQL database

The application uses the Blueprint pattern to organize routes and follows a factory pattern for application creation, allowing different configurations based on the environment.

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

The application uses Docker Compose with two services:

1. **Web Service**:
   - Built from the project's Dockerfile
   - Runs the Flask application with Gunicorn
   - Connects to the database service
   - Exposes port 80

2. **Database Service**:
   - Uses PostgreSQL 15
   - Persists data in a named volume
   - Initialized with scripts from db/ directory

Environment variables in docker-compose.yml allow configuration of:
- Database credentials
- Flask configuration mode
- Email settings
- Secret keys

### Python Path and Module Imports

The application uses Python's import system with some specific considerations:

1. The `run.py` script adds both the current directory and parent directory to Python's path:
   ```python
   # Add the parent directory to the Python path
   parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
   sys.path.insert(0, parent_dir)
   
   # Add the current directory to the Python path
   sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
   ```

2. The Dockerfile sets the `PYTHONPATH` environment variable:
   ```Dockerfile
   ENV PYTHONPATH=/app:/app/cmmc_tracker
   ```

This configuration allows imports both from within the `cmmc_tracker` package and from the project root.

## Database Initialization

The `seed_db.py` script handles database initialization:

1. Creates database tables if they don't exist
2. Imports CMMC controls from cmmc_controls.json
3. Creates default admin user
4. Generates sample tasks for demonstration

To reset the database:
```
docker compose down -v
docker compose up -d
docker compose exec web python seed_db.py
```

## Common Issues and Troubleshooting

### Circular Import Dependencies

The application has potential circular dependencies between modules that need to be carefully managed:

1. **Email and Utils**: There's a circular dependency risk between `app/services/email.py` and `app/utils/__init__.py`. The utils module should not directly import from the email service.

2. **Models and Services**: Models often need to use services, while services need to use models. To avoid circular imports:
   - Break out shared functionality into separate utility modules
   - Use function-level imports rather than module-level imports where appropriate
   - Ensure proper layering of dependencies

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

### Template Rendering Errors

Common template issues include:

1. **Undefined variables**: Always provide all required variables to `render_template()`
2. **URL building errors**: Verify all `url_for()` calls reference valid endpoints
3. **CSRF token issues**: Ensure all forms include the CSRF token: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`

## Testing

The application currently lacks formal tests, which is an area for improvement.

Recommended testing strategy:
1. Add unit tests for models and services
2. Implement integration tests for routes and user flows
3. Set up CI/CD pipeline with automated testing
4. Add end-to-end tests for critical user journeys

---

This documentation is intended to be a living document. As the application evolves, please keep it updated to reflect the current state of the codebase. 