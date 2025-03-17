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

- **Control Management**: Create, update, and track cybersecurity controls
- **Task Assignment**: Assign tasks to team members with due dates and status tracking
- **User Management**: Role-based access control with admin capabilities
- **Audit Logging**: Comprehensive audit trail for compliance activities
- **Reporting**: Generate compliance status reports and dashboards
- **Email Notifications**: Automated alerts for task assignments and due dates

## Technology Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap, Jinja2 templates
- **Deployment**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose installed

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/python-grc-b.git
   cd python-grc-b
   ```

2. Start the application using Docker Compose:
   ```
   docker-compose up -d
   ```

3. Initialize the database:
   ```
   docker-compose exec web python seed_db.py
   ```

4. Access the application at http://localhost:80

### Default Credentials

- **Username**: admin
- **Password**: admin123

## Environment Variables

The application can be configured using the following environment variables:

- `FLASK_CONFIG`: Configuration mode (development, testing, production)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database connection settings
- `SECRET_KEY`: Flask secret key
- `MAIL_*`: Email server configuration settings

## License

[Your License Information]

## Contact

[Your Contact Information]
