# Technology Context: CMMC Compliance Tracker

## Technology Stack

### Backend
- **Python 3.x**: Core programming language
- **Flask 2.3+**: Web framework
- **SQLAlchemy**: ORM for database interactions
- **Jinja2**: Template engine for rendering HTML

### Frontend
- **Bootstrap**: CSS framework for responsive design
- **JavaScript**: Client-side interactivity
- **jQuery**: Simplifies DOM manipulation and AJAX
- **Chart.js**: Data visualization for dashboards

### Database
- **SQLite**: Development and testing database
- **PostgreSQL**: Production database
- **SQL Migrations**: Version-controlled schema changes

### Authentication & Security
- **Flask-Login**: User session management
- **Werkzeug**: Password hashing
- **PyOTP**: Time-based One-Time Password (TOTP) for MFA
- **QRCode**: QR code generation for MFA setup
- **Flask-Limiter**: Rate limiting for security
- **Redis**: Storage backend for rate limiting

### Notifications & Scheduling
- **Flask-Mail**: Email notifications
- **Flask-APScheduler**: Task scheduling
- **Redis**: Queue backend for scheduled tasks

### Deployment & Infrastructure
- **Docker**: Containerization for consistent deployment
- **Docker Compose**: Multi-container orchestration
- **Gunicorn**: WSGI HTTP server for production

## Development Environment

### Prerequisites
- Docker and Docker Compose
- Python 3.x development environment (for local development)
- Git for version control

### Local Setup
1. Clone repository
2. Use Docker Compose for containerized development
3. Access application at http://localhost:80

### Docker Configuration
- Web application container based on Python image
- PostgreSQL container for database
- Redis container for rate limiting and task queue
- Persistent volumes for database and uploads
- Environment variables for configuration

## Technical Constraints

### Performance
- Optimized for organizations with up to 500 controls
- Up to 100 concurrent users
- Evidence file size limited to 10MB per upload

### Security
- HTTPS required for production deployment
- Secure cookie settings for session management
- Content-Security-Policy implementation
- HTTP security headers (X-XSS-Protection, X-Frame-Options, etc.)
- Redis-backed rate limiting for authentication endpoints
- Password strength enforcement
- TOTP-based multi-factor authentication with backup codes
- One-time use password reset tokens
- Resource ownership validation to prevent IDOR issues
- Regular security dependency updates

### Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design for tablets and smartphones
- Accessible design following WCAG guidelines

## Deployment Patterns

### Development
- Docker Compose with SQLite database
- Hot-reloading for template and code changes
- Debug mode enabled for detailed error messages

### Testing
- Automated testing with pytest
- CI/CD integration for test automation
- Test database with sample data fixtures

### Production
- PostgreSQL database for production workloads
- Redis for session management, rate limiting, and task queue
- Gunicorn workers for request handling
- Nginx for static file serving and SSL termination

## External Dependencies

### Third-Party Services
- Email service (SMTP) for notifications
- Time synchronization for accurate MFA
- Browser support for modern JavaScript features

### System Requirements
- Minimum 1GB RAM for application container
- 10GB storage for database and uploaded files
- Network connectivity for email notifications

## Configuration Management

Application configured through:
1. Environment variables
2. Configuration files (config.py)
3. Database settings
4. Feature flags for controlled rollout

## Security Features

### Authentication
- Password hashing with Werkzeug
- Multi-factor authentication (TOTP) with backup codes
- Admin capability to reset MFA for users
- Rate limiting on login attempts (10 per minute)

### Access Control
- Role-based permissions (admin vs. regular users)
- Resource ownership validation
- Complete mediation of all requests

### Data Protection
- Input validation and sanitization
- CSRF protection on all forms
- Comprehensive audit logging
- Secure file storage for evidence files 