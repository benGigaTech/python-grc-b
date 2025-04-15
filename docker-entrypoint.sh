#!/bin/bash
set -e
# set -x # Enable debug output (print commands) - Commented out after debugging

# Log file path within the container
LOG_FILE="/app/entrypoint.log"
echo "Docker Entrypoint started at $(date)" > "$LOG_FILE"

# Function to log messages to both stdout and the log file
log_message() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Database connection details from environment variables
DB_HOST=${DB_HOST:-"db"}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"cmmc_db"}
DB_USER=${DB_USER:-"cmmc_user"}
DB_PASSWORD=${DB_PASSWORD:-"password"}
export PGPASSWORD="$DB_PASSWORD"

# Function to execute SQL command using psql
run_psql() {
    psql -v ON_ERROR_STOP=1 --host "$DB_HOST" --port "$DB_PORT" --dbname "$DB_NAME" --username "$DB_USER" "$@"
}

# Wait for the database to be ready
log_message "Waiting for database to be ready..."
max_retries=30
retry_interval=2
retries=0
# Simpler loop condition check
while ! run_psql -c "\q" && [ $retries -lt $max_retries ]; do
    retries=$((retries+1))
    log_message "Waiting for database... attempt $retries/$max_retries"
    sleep $retry_interval
done

# Check if loop finished due to success or timeout
if ! run_psql -c "\q" > /dev/null 2>&1; then # Final check after loop
    log_message "Could not connect to database after $max_retries attempts. Exiting."
    exit 1
fi
log_message "Database is ready!"

# --- Database Migration Logic ---
log_message "Starting database migrations..."

MIGRATION_DIR="/app/db"
APPLIED_BY="docker-entrypoint"

# Ensure migration_history table exists (Run 02_migration_tracking.sql unconditionally)
MIGRATION_TRACKING_SCRIPT="$MIGRATION_DIR/02_migration_tracking.sql"
if [ -f "$MIGRATION_TRACKING_SCRIPT" ]; then
    log_message "Ensuring migration tracking table exists..."
    run_psql -f "$MIGRATION_TRACKING_SCRIPT"
    if [ $? -ne 0 ]; then
        log_message "Error ensuring migration tracking table exists. Exiting."
        exit 1
    fi
else
    log_message "Warning: Migration tracking script $MIGRATION_TRACKING_SCRIPT not found."
fi

# Apply pending migrations
shopt -s nullglob # Prevent error if no files match
for migration_file in "$MIGRATION_DIR"/0*.sql; do
    migration_name=$(basename "$migration_file")

    # Skip the tracking script itself in this loop
    if [ "$migration_name" == "02_migration_tracking.sql" ]; then
        continue
    fi

    log_message "Checking migration: $migration_name"

    # Check if migration is already applied
    applied_count=$(run_psql -tAc "SELECT COUNT(*) FROM migration_history WHERE migration_name = '$migration_name'")

    if [ $? -ne 0 ]; then
        log_message "Error checking migration history for $migration_name. Exiting."
        exit 1
    fi

    if [ "$applied_count" -eq 0 ]; then
        log_message "Applying migration: $migration_name..."
        # Apply the migration file
        run_psql -f "$migration_file"
        migration_exit_code=$?

        if [ $migration_exit_code -eq 0 ]; then
            # Record the migration in history table on success
            run_psql -c "INSERT INTO migration_history (migration_name, applied_by) VALUES ('$migration_name', '$APPLIED_BY')"
            if [ $? -ne 0 ]; then
                 log_message "Error recording migration $migration_name in history. Manual check required!"
                 # Decide if this should be a fatal error
            else
                 log_message "Successfully applied and recorded: $migration_name"
            fi
        else
            log_message "Error applying migration: $migration_name. Exiting."
            exit 1 # Exit immediately on migration failure
        fi
    else
        log_message "Migration already applied: $migration_name"
    fi
done
shopt -u nullglob # Turn off nullglob

log_message "Database migrations complete!"
# --- End Migration Logic ---

# --- Optional Full Database Seed ---
# Check if full seeding is requested via environment variable
if [ "${RUN_FULL_SEED}" = "true" ] || [ "${RUN_FULL_SEED}" = "yes" ] || [ "${RUN_FULL_SEED}" = "1" ]; then
    log_message "RUN_FULL_SEED is set to true. Running full database seed..."
    # Ensure seed_db.py exists before trying to run it
    if [ -f "/app/seed_db.py" ]; then
        python /app/seed_db.py >> "$LOG_FILE" 2>&1
        seed_exit_code=$?
        log_message "Seed script (seed_db.py) finished with exit code $seed_exit_code"
        if [ $seed_exit_code -ne 0 ]; then
            log_message "Warning: seed_db.py reported an error. Check script logs."
        fi
    else
        log_message "Warning: RUN_FULL_SEED is true, but /app/seed_db.py not found."
    fi
else
    log_message "RUN_FULL_SEED not set to true. Skipping full database seed."
fi
# --- End Optional Full Seed ---

# Start the main process (e.g., Flask app)
log_message "Starting application (exec $@)..."
exec "$@"