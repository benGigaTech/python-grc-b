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