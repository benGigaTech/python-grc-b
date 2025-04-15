# Testing Strategy: CMMC Compliance Tracker

This document outlines the testing approach for the CMMC Compliance Tracker application, including test categories, environment setup, and best practices.

## Test Categories

The application uses a pytest-based testing framework with the following categories:

### Unit Tests

- Located in `tests/unit/`
- Focus on testing individual functions and methods in isolation
- Mock external dependencies (database, file system, etc.)
- Fast execution, no external dependencies
- Examples: utility functions, model methods, service functions

### Integration Tests

- Located in `tests/integration/`
- Test interactions between components
- Use real database connections with test data
- Verify database operations, route handlers, and service interactions
- Examples: API endpoints, database operations, authentication flows

### Functional Tests

- Located in `tests/functional/`
- End-to-end tests that simulate user interactions
- Test complete workflows from the user's perspective
- Examples: user registration, control management, evidence upload

## Test Environment

The application uses Docker Compose for testing to ensure a consistent, isolated environment:

### Docker Compose Configuration

- Defined in `docker-compose.test.yml`
- Includes web application, PostgreSQL database, and Redis services
- Uses separate volumes for test data
- Environment variables configured for testing

### Database Setup

- Test database (`cmmc_test_db`) created automatically
- Schema migrations applied during container startup
- Test data seeded as needed for specific tests
- Database connection pooling with automatic container name resolution

## Test Fixtures

The application uses pytest fixtures to set up test prerequisites:

### Key Fixtures

- `app`: Flask application instance with test configuration
- `client`: Flask test client for making requests
- `init_database`: Initialize database with test data
- `auth_client`: Authenticated client with test user session

## Best Practices

### Writing Tests

1. **Isolation**: Each test should be independent and not rely on the state from other tests
2. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification phases
3. **Descriptive Names**: Use clear test names that describe the behavior being tested
4. **Parametrization**: Use pytest's parametrize feature for testing multiple scenarios
5. **Fixtures**: Use fixtures for common setup and teardown operations

### Running Tests

1. **Start Test Environment**:
   ```
   docker compose -f docker-compose.test.yml up -d
   ```

2. **Run All Tests**:
   ```
   docker compose -f docker-compose.test.yml exec web pytest -v tests/
   ```

3. **Run Specific Test Categories**:
   ```
   # Run only unit tests
   docker compose -f docker-compose.test.yml exec web pytest -v tests/unit/

   # Run only integration tests
   docker compose -f docker-compose.test.yml exec web pytest -v tests/integration/

   # Run only functional tests
   docker compose -f docker-compose.test.yml exec web pytest -v tests/functional/
   ```

4. **Run Tests with Markers**:
   ```
   # Run only tests for models
   docker compose -f docker-compose.test.yml exec web pytest -v -m models

   # Run only tests for utilities
   docker compose -f docker-compose.test.yml exec web pytest -v -m utils
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure the test database container is running
   - Check that the database host in tests matches the service name in docker-compose.test.yml
   - The database service now automatically tries to connect using the Docker container name format (e.g., `python-grc-b-db_test-1`) if the initial connection fails

2. **Test Data Issues**:
   - Ensure tests properly set up and tear down test data
   - Use the `init_database` fixture for consistent database state
   - Avoid dependencies between tests

3. **Authentication Issues**:
   - Use the `auth_client` fixture for tests requiring authentication
   - Ensure test users have the appropriate permissions

## Continuous Integration

The application is designed to support continuous integration workflows:

1. **Automated Test Runs**: Tests can be executed automatically on code changes
2. **Test Reports**: Test results can be collected and reported
3. **Coverage Analysis**: Code coverage can be measured to identify untested code

## Future Enhancements

1. **Browser Testing**: Add Selenium or Playwright tests for UI testing
2. **Performance Testing**: Add load and performance tests
3. **Security Testing**: Add automated security scanning
4. **API Testing**: Add comprehensive API test suite when the API is implemented
