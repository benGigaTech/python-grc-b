# Database Migrations

This directory contains SQL migration scripts for the CMMC Compliance Tracker database.

## Migration Structure

- `01_init.sql` - Initial database schema creation script
- `02_migration_tracking.sql` - Creates the table used to track applied migrations
- `03_evidence_migration.sql` - Adds the evidence table for storing compliance evidence files

## File Naming Convention

Migration files follow a numbered sequence format to ensure they are executed in the correct order:

1. `01_init.sql` - Always runs first to set up base tables
2. `02_migration_tracking.sql` - Creates the migration tracking infrastructure
3. `03_evidence_migration.sql` and onwards - Feature-specific migrations

This numbering is essential when running in Docker, as PostgreSQL executes scripts in the `docker-entrypoint-initdb.d` directory in alphabetical order.

## Applying Migrations

Migrations can be applied using the `apply_migration.py` script:

```bash
# Apply all migrations
python apply_migration.py

# Apply a specific migration
python apply_migration.py db/evidence_migration.sql
```

When running in Docker:

```bash
# Apply all migrations
docker compose exec web python apply_migration.py

# Apply a specific migration
docker compose exec web python apply_migration.py db/evidence_migration.sql
```

## Migration Tracking

The system automatically tracks applied migrations in the `migration_history` table. This ensures that migrations are only applied once, even if the migration script is run multiple times.

## Creating New Migrations

To create a new migration:

1. Create a new SQL file in this directory with a descriptive name (e.g., `add_email_notifications.sql`)
2. Include proper error handling and idempotent operations in your SQL script
3. Use the following pattern for table creation:

```sql
-- Check if table exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'your_table_name') THEN
        CREATE TABLE your_table_name (
            -- column definitions
        );
        
        -- indexes, constraints, etc.
        
        RAISE NOTICE 'Created your_table_name table';
    ELSE
        RAISE NOTICE 'your_table_name table already exists';
    END IF;
END $$;
```

This ensures that migrations can be safely re-run without errors.

## Best Practices

1. Always make migrations idempotent (can be run multiple times without error)
2. Include proper error handling in SQL scripts
3. Use descriptive names for migration files
4. Document migrations in this README file
5. Test migrations in a development environment before applying to production 