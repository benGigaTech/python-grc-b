# CMMC Compliance Tracker Tests

This directory contains tests for the CMMC Compliance Tracker application.

## Test Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for component interactions
- `functional/`: Functional tests for complete workflows

## Running Tests

### Using Docker

```bash
# Run all tests
./run_tests.bat

# Run specific test categories
docker compose -f docker-compose.test.yml exec web pytest -v tests/unit
docker compose -f docker-compose.test.yml exec web pytest -v tests/integration
docker compose -f docker-compose.test.yml exec web pytest -v tests/functional

# Run tests with specific markers
docker compose -f docker-compose.test.yml exec web pytest -v -m "unit and models"
docker compose -f docker-compose.test.yml exec web pytest -v -m "integration and auth"

# Run tests with coverage report
docker compose -f docker-compose.test.yml exec web pytest --cov=cmmc_tracker --cov-report=term --cov-report=html
```

### Test Database

The tests use a separate test database (`cmmc_test_db`) to avoid affecting the development or production database. The test database is automatically set up with minimal test data in the `conftest.py` file.

### Test Environment

The test environment is defined in `docker-compose.test.yml`, which includes:

- A web service for running the application
- A db_test service for the test database
- Environment variables specific to testing

The test environment uses the same Dockerfile as the development environment but with different configuration settings. The `docker-entrypoint.sh` script has been updated to use environment variables for database connection details, allowing it to connect to the test database service named `db_test` instead of the development database service named `db`.

## Test Markers

The following markers are available for categorizing tests:

- `unit`: Unit tests
- `integration`: Integration tests
- `functional`: Functional tests
- `models`: Tests for models
- `routes`: Tests for routes
- `services`: Tests for services
- `utils`: Tests for utilities
- `auth`: Tests for authentication
- `controls`: Tests for controls
- `tasks`: Tests for tasks
- `evidence`: Tests for evidence
- `admin`: Tests for admin functionality
- `reports`: Tests for reports
- `slow`: Tests that are slow to run

## Test Fixtures

The `conftest.py` file defines several fixtures that can be used in tests:

- `app`: Creates a Flask application instance for testing
- `client`: Creates a test client for making requests to the application
- `init_database`: Initializes the test database with minimal test data

These fixtures can be used in tests by including them as parameters in the test function:

```python
def test_example(app, client, init_database):
    # Test code using the fixtures
    pass
```

## Writing Tests

### Unit Tests

Unit tests should test individual components in isolation, mocking any dependencies.

```python
@pytest.mark.unit
@pytest.mark.models
def test_user_creation():
    """Test creating a User object."""
    user = User(
        id=1,
        username='test_user',
        password_hash=generate_password_hash('password'),
        is_admin=0
    )

    assert user.id == 1
    assert user.username == 'test_user'
    assert user.is_admin == 0
    assert user.check_password('password')
```

### Integration Tests

Integration tests should test the interaction between components.

```python
@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.auth
def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data
```

### Functional Tests

Functional tests should test complete workflows from the user's perspective.

```python
@pytest.mark.functional
@pytest.mark.tasks
def test_task_creation_workflow(client, init_database):
    """Test the complete workflow of creating and managing a task."""
    # Step 1: Admin logs in
    response = client.post(
        '/login',
        data={'username': 'admin', 'password': 'adminpassword'},
        follow_redirects=True
    )
    assert response.status_code == 200

    # Step 2: Admin creates a new task
    # ...
```

## Troubleshooting

### Common Test Issues

1. **Database Connection Errors**:
   - Ensure the test database container is running (`docker compose -f docker-compose.test.yml ps`)
   - Check that the database host in docker-entrypoint.sh matches the service name in docker-compose.test.yml
   - Verify that tests are using the app context when accessing the database
   - For database-dependent tests, use the `init_database` fixture
   - Skip tests that require complex database setup with `@pytest.mark.skip`

2. **Application Context Errors**:
   - Errors like "Working outside of application context" indicate that you're trying to access Flask's `g` object or other context-dependent features outside of an application context
   - Use `with app.app_context():` to create an application context in tests
   - Ensure that fixtures that need application context are properly set up

3. **Import Errors**:
   - Ensure PYTHONPATH is set correctly in docker-compose.test.yml
   - Check for circular imports
   - Use relative imports within the test directory

4. **Test Data Issues**:
   - Ensure test data is properly initialized in fixtures
   - Use unique identifiers for test data to avoid conflicts
   - Clean up test data after tests to avoid affecting other tests
