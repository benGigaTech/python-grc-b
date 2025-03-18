# CMMC Compliance Tracker

A Flask-based web application for tracking and managing Cybersecurity Maturity Model Certification (CMMC) compliance controls.

## Overview

The CMMC Compliance Tracker helps organizations manage their cybersecurity controls, track compliance tasks, and maintain audit logs for CMMC certification requirements. It provides a centralized platform for:

- Managing CMMC and NIST SP 800-171 controls
- Assigning and tracking compliance tasks
- Conducting control reviews
- Generating compliance reports
- Maintaining detailed audit logs

## Features

- **Interactive Dashboard**: Visual overview of compliance status with metrics and charts
- **Control Management**: Create, update, and track cybersecurity controls
- **Bulk Import/Export**: Easily import or export controls in CSV format
- **Task Assignment**: Assign tasks to team members with due dates and status tracking
- **User Management**: Role-based access control with admin capabilities
- **Audit Logging**: Comprehensive audit trail for compliance activities
- **Reporting**: Generate compliance status reports and dashboards
- **Email Notifications**: Automated alerts for task assignments and upcoming deadlines

## Technology Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap, Jinja2 templates, Chart.js
- **Task Scheduling**: Flask-APScheduler
- **Deployment**: Docker, Docker Compose

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

### Default Credentials

- **Admin User**:
  - Username: admin
  - Password: adminpassword

- **Regular User**:
  - Username: user
  - Password: userpassword

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

## Environment Variables

The application can be configured using the following environment variables:

- `FLASK_CONFIG`: Configuration mode (development, testing, production)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database connection settings
- `SECRET_KEY`: Flask secret key
- `MAIL_*`: Email server configuration settings
- `NOTIFICATION_ENABLED`: Enable/disable email notifications (true/false)
- `NOTIFICATION_HOUR`: Hour of the day to send daily notifications (0-23)

