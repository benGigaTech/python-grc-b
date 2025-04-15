# Decision Log: CMMC Compliance Tracker

This log records significant decisions made during the project lifecycle, including rationale and implications.

---

[2025-04-04 12:11:18] - Initialized Decision Log file.

---

[2025-04-04 13:32:41] - **Expanded Settings System Design**
*   **Decision:** Add new global settings for evidence lifecycle (default validity days, auto-expiration toggle), email subject prefix, app footer text, and app favicon URL.
*   **Rationale:** Leverages the existing `settings` table structure and `settings.py` service, minimizing new code and maintaining consistency with the established pattern. Requires only adding rows to the table and updating the admin UI.
*   **Implications:** Requires a new database migration script (`db/08_expanded_settings.sql`) to insert default values. Requires updates to `cmmc_tracker/app/templates/admin_settings.html` and the corresponding route in `cmmc_tracker/app/routes/admin.py`. Relevant services/templates consuming these settings will need modification.
*   **Decision:** Defer complex email template customization and per-user notification preferences.
*   **Rationale:** Per-user preferences require a different data model (likely a separate table linked to users). Template customization is a larger feature. Deferring keeps the current task focused.
*   **Implications:** Functionality related to these deferred items will not be available in this iteration. Placeholders or simple flags might be added to global settings if needed for future integration points (e.g., `notification.use_custom_templates`).

---

[2025-04-05 10:18:45] - **Evidence Lifecycle Settings Validation**
*   **Decision:** Implement both client-side and server-side validation for the `evidence.default_validity_days` setting to ensure it's a positive integer.
*   **Rationale:** Prevents invalid values that could cause calculation errors when determining evidence expiration dates. Client-side validation provides immediate feedback, while server-side validation ensures data integrity even if client validation is bypassed.
*   **Implications:** Improves robustness of the evidence lifecycle feature and prevents potential bugs from invalid settings. Requires changes to both the admin settings template and the settings route handler.
*   **Decision:** Add clear user feedback when evidence expiration dates cannot be calculated due to invalid settings.
*   **Rationale:** Improves user experience by providing actionable information when automatic expiration cannot be applied, rather than silently failing.
*   **Implications:** Users will be aware when they need to contact an administrator to fix settings issues, and administrators will have better visibility into configuration problems.
*   **Decision:** Document a future enhancement for automatically updating evidence status when it expires.
*   **Rationale:** The current implementation only sets expiration dates at upload time but doesn't automatically change the status when that date is reached. A scheduled task would complement the auto-expiration setting.
*   **Implications:** Provides a clear path for future development and ensures the feature can be properly completed in a subsequent iteration.

---

[2025-05-15 14:30:22] - **Testing Framework Implementation**
*   **Decision:** Implement a pytest-based testing framework with unit, integration, and functional test categories.
*   **Rationale:** A structured testing framework is essential for ensuring code quality, catching regressions, and facilitating future development. Pytest provides a modern, flexible testing infrastructure with powerful fixtures and parametrization capabilities.
*   **Implications:** Requires creating test fixtures, setting up a test database, and implementing initial tests for core functionality. Will improve code quality and reduce regressions in the long term.
*   **Decision:** Use Docker Compose for the test environment with a separate database container.
*   **Rationale:** Isolates the test environment from development and production, preventing test data from affecting real data. Docker Compose provides a consistent, reproducible environment for testing.
*   **Implications:** Requires creating a docker-compose.test.yml file and updating the docker-entrypoint.sh script to use environment variables for database connection details.
*   **Decision:** Implement test fixtures for application, client, and database initialization.
*   **Rationale:** Fixtures provide a consistent way to set up test prerequisites and clean up afterward. They reduce code duplication and ensure tests start with a known state.
*   **Implications:** Requires creating a conftest.py file with fixture definitions and updating tests to use these fixtures.
*   **Decision:** Use test markers to categorize tests by type and functionality.
*   **Rationale:** Markers allow running specific subsets of tests, making it easier to focus on particular areas during development or debugging.
*   **Implications:** Requires adding marker decorators to test functions and documenting available markers.

---

[2025-05-20 09:45:33] - **Docker Container Name Resolution Enhancement**
*   **Decision:** Enhance the database connection service to automatically handle Docker container name resolution in testing environments.
*   **Rationale:** Docker Compose generates container names that include the project name and service name (e.g., `python-grc-b-db_test-1`), which can cause connection issues when tests reference the service name directly (e.g., `db_test`). This enhancement provides a fallback mechanism that tries the Docker-generated container name if the initial connection fails.
*   **Implications:** Improves test reliability across different environments without requiring manual configuration changes. Tests can continue to use the logical service names while the connection service handles the resolution behind the scenes.
*   **Decision:** Implement the fallback only for testing environments to avoid unnecessary connection attempts in production.
*   **Rationale:** The issue primarily affects testing environments where container names are more likely to vary. Production environments typically use stable, well-defined hostnames.
*   **Implications:** The database service now includes additional error handling and connection retry logic, but only when `TESTING` is set to `True` in the Flask configuration.
*   **Decision:** Update documentation to reflect this enhancement.
*   **Rationale:** Users should be aware of this feature when troubleshooting connection issues in testing environments.
*   **Implications:** Documentation in README.md and memory-bank files has been updated to include information about this enhancement.

---

[2025-04-15 12:15:00] - **Chunked Upload Implementation for Large Evidence Files**
*   **Decision:** Implement a chunked upload mechanism for handling large evidence files.
*   **Rationale:** Previous approach of increasing Gunicorn timeout to 120s was only a partial solution. Large file uploads were still causing timeouts and memory issues, especially on slower connections. A chunked upload approach breaks files into smaller pieces, uploads them incrementally, and reassembles them on the server.
*   **Implications:** Allows users to upload much larger files (up to 50MB, increased from 16MB) without timeouts, with the added benefit of progress tracking.
*   **Decision:** Create a dedicated service (`chunked_upload.py`) and blueprint (`chunked_upload_bp`) for handling chunked uploads.
*   **Rationale:** Separating the chunked upload logic into its own service and routes maintains clean separation of concerns and makes the code more maintainable.
*   **Implications:** Adds new endpoints for creating upload sessions, uploading chunks, and completing uploads. Requires updating the evidence routes to handle both regular and chunked uploads.
*   **Decision:** Use client-side JavaScript with the Fetch API to handle chunked uploads.
*   **Rationale:** Modern browsers support the Fetch API and File API, which make it easy to slice files into chunks and upload them asynchronously. This approach provides better user experience with progress tracking.
*   **Implications:** Adds JavaScript code to the add_evidence.html template for detecting large files and handling chunked uploads. Requires updating the CSP configuration to allow fetch API calls.
*   **Decision:** Set threshold of 5MB for automatic chunked uploads.
*   **Rationale:** Files smaller than 5MB can be uploaded efficiently using the standard form submission. Larger files benefit from chunking to prevent timeouts.
*   **Implications:** Small files continue to use the simpler upload process, while large files automatically use the chunked approach, providing a seamless experience for users.