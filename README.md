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

- **Interactive Dashboard**: Visual overview of compliance status with metrics and charts
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

The database will be automatically initialized with sample data on first startup. No manual initialization is required.

### Database Migrations

When schema changes are required, SQL migration files are provided in the `db` directory. To apply migrations:

1. **Using the migration script**:
   ```
   # Apply all migrations
   python apply_migration.py
   
   # Apply a specific migration
   python apply_migration.py db/evidence_migration.sql
   ```

2. **Within Docker**:
   ```
   docker compose exec web python apply_migration.py
   ```

Migration files are named descriptively (e.g., `evidence_migration.sql`) to indicate their purpose.

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
- Track metadata including upload date, expiration date, and status
- View evidence status with color-coded indicators (Current, Pending Review, Expired)
- Download evidence files securely
- Add, update, and delete evidence with proper access controls
- Organize evidence by control for easy compliance verification

### File Support

- Supported file types include PDF, Word documents, Excel spreadsheets, images, and text files
- Each evidence item tracks file size, type, and original filename
- Optional expiration dates to manage evidence lifecycle

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

## Environment Variables

The application can be configured using the following environment variables:

- `FLASK_CONFIG`: Configuration mode (development, testing, production)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database connection settings
- `SECRET_KEY`: Flask secret key
- `MAIL_*`: Email server configuration settings
- `NOTIFICATION_ENABLED`: Enable/disable email notifications (true/false)
- `NOTIFICATION_HOUR`: Hour of the day to send daily notifications (0-23)

