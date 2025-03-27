# System Patterns: CMMC Compliance Tracker

## Architecture Overview

The CMMC Compliance Tracker follows a modular web application architecture based on Flask:

```
cmmc_tracker/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Route handlers 
│   ├── services/        # Business logic
│   ├── templates/       # Jinja2 templates
│   ├── utils/           # Helper functions
│   └── __init__.py      # Application factory
├── uploads/             # Evidence file storage
├── config.py            # Configuration
└── run.py               # Application entry point
```

The application uses a layered architecture:
- **Presentation Layer**: Flask routes and Jinja2 templates
- **Business Logic Layer**: Models and Services
- **Data Access Layer**: Database service abstraction
- **Infrastructure**: Docker containers for web, PostgreSQL, and Redis

## Design Patterns

### Model-View-Controller (MVC)
- **Models**: SQLAlchemy models in `app/models/` define the data structure
- **Views**: Jinja2 templates in `app/templates/` render the UI
- **Controllers**: Route handlers in `app/routes/` process requests

### Application Factory
- Centralized application initialization in `app/__init__.py`
- Supports multiple configurations (development, testing, production)
- Modular extension registration
- Security headers added via `@app.after_request` decorator

### Blueprint Pattern
- Routes organized into logical blueprints (auth, admin, controls, evidence, etc.)
- Each blueprint handles a specific functional area
- Improves code organization and maintainability
- Blueprints registered in `app/__init__.py` through `register_blueprints()` function

### Service Layer
- Business logic isolated in service modules
- Separates application logic from route handlers
- Improves testability and code reuse
- Key services include:
  - `database.py`: Database connection and operations
  - `email.py`: Email notification handling
  - `audit.py`: Audit logging
  - `mfa.py`: Multi-factor authentication
  - `storage.py`: File storage operations
  - `scheduler.py`: Background task scheduling

### Repository Pattern
- Data access logic encapsulated in model classes
- Standard methods for CRUD operations
- Abstracts database interactions from business logic
- Uses utility functions from `database.py` for SQL operations

### Database Connection Pool
- Connection management through `get_db_connection()` function
- Connection created for each request and closed after use
- PostgreSQL connection with psycopg2
- SQL execution with parameterized queries for security
- Error handling with try/except blocks and transaction management

## Key Components

### Authentication System
- Flask-Login for session management
- Password hashing with Werkzeug
- TOTP-based multi-factor authentication
- Backup codes for MFA recovery
- Admin MFA reset capability
- Rate limiting for security
- Redis-backed rate limiting persistence
- Password strength validation
- Account lockout after multiple failed login attempts
- Automatic account unlock after timeout period
- Admin capability to manually unlock accounts

### Database Schema
- Relational schema with SQLite (dev) and PostgreSQL (prod)
- Foreign key relationships for data integrity
- Indexes for performance optimization
- Migration support for schema evolution
- Main tables include:
  - `users`: User accounts and authentication
  - `controls`: CMMC compliance controls
  - `tasks`: Compliance tasks and assignments
  - `evidence`: Evidence files and metadata
  - `auditlogs`: System activity tracking

### File Storage
- Local file system storage for evidence files
- Secure file naming and organization
- File metadata tracked in database
- Status tracking (Current, Pending Review, Expired)
- File type validation and size limits
- Secure file download through Flask's `send_file`

### Task Scheduling
- Flask-APScheduler for periodic tasks
- Notification sending and status updates
- Automatic report generation
- Daily task deadline notifications configured

### Rate Limiting
- Flask-Limiter for request throttling
- Redis backend for persistent storage
- Configurable limits for different endpoints
- Protection against brute force attacks
- Specific limits defined per route

### MFA System
- PyOTP library for TOTP implementation
- QR code generation for easy setup
- Backup codes for recovery
- Admin reset capability
- TOTP verification during login
- Session-based MFA verification flow

### Account Lockout System
- Tracks failed login attempts in database
- Automatic lockout after configurable number of failed attempts (default: 5)
- Configurable lockout duration (default: 15 minutes)
- Failed attempts count reset on successful login
- Admin interface for viewing locked accounts
- Admin capability to manually unlock accounts
- Automatic unlock after lockout period expires
- Comprehensive audit logging of lockout events

## Data Flow Patterns

### User Authentication Flow
1. User submits credentials 
2. System validates credentials 
3. If invalid, increment failed login attempts counter
4. If failed attempts exceed threshold, lock account temporarily
5. If credentials valid but MFA enabled, redirect to MFA verification
6. User submits TOTP code or backup code
7. System validates MFA code
8. If MFA fails, increment failed attempts (may trigger lockout)
9. If MFA succeeds, reset failed attempts counter
10. Session cookie issued for authenticated requests
11. User redirected to dashboard

### Control Management Flow
1. Controls loaded from database
2. User performs CRUD operations
3. Changes logged in audit system
4. Notifications triggered for relevant users
5. Associated tasks and evidence updated accordingly

### Evidence Upload Flow
1. User selects file and provides metadata
2. System validates file type and size
3. File saved to secure storage location
4. Database updated with file reference and metadata
5. Status assigned based on expiration date
6. Audit log entry created for the upload

### Reporting Flow
1. User requests specific report type
2. System aggregates data from multiple tables
3. Report formatted according to template
4. Delivered as web view or downloadable file
5. Metrics calculated for dashboard displays

### Calendar View Flow
1. System retrieves control reviews and tasks with due dates
2. Dates organized into calendar format
3. Color-coding applied based on status
4. User can navigate between months
5. Paginated tables display detailed information

## Security Patterns

1. **Defense in Depth**: Multiple security layers including authentication, authorization, and input validation
2. **Principle of Least Privilege**: Role-based access control limits user permissions
3. **Secure by Default**: Sensible security defaults with explicit opt-out where needed
4. **Complete Mediation**: All requests pass through authentication and authorization checks
5. **Audit Trail**: Comprehensive logging of security-relevant events
6. **Rate Limiting**: Protection against brute force and DoS attacks
7. **Content Security Policy**: Protection against XSS and other injection attacks
8. **Multi-Factor Authentication**: Additional verification beyond passwords
9. **Password Strength Enforcement**: Prevention of weak passwords
10. **One-Time Token Pattern**: Secure password reset process
11. **Parameterized Queries**: Protection against SQL injection
12. **Input Sanitization**: Cleaning user input to prevent injection attacks
13. **Account Lockout**: Temporary account lockout after multiple failed authentication attempts
14. **Progressive Timeouts**: Increasing lockout durations for repeated authentication failures
15. **Administrative Override**: Admin capability to unlock accounts in legitimate cases

## Database Migration Pattern

1. **SQL-Based Migrations**: Versioned SQL scripts for schema changes
2. **Version Tracking**: Migration tracking table in database
3. **Idempotent Operations**: Safe to run multiple times
4. **Migration Application Script**: Centralized script for applying migrations

## UI Design Patterns

1. **Responsive Design**: Works across device sizes
2. **Dashboard Pattern**: Quick overview of key metrics
3. **Card-Based Layout**: Information organized in intuitive cards
4. **Color Status Indicators**: Visual feedback about status
5. **Paginated Tables**: Handling large datasets efficiently
6. **Interactive Calendar**: Visual representation of scheduled events
7. **Progress Bars**: Visual representation of metrics
8. **Badges**: Compact status indicators
9. **Flash Messages**: Immediate user feedback for actions
10. **Status Indicators**: Visual cues for account lockout status 