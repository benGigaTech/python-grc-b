-- Migration tracking table
-- This table keeps track of which migrations have been applied

-- Check if migration_history table exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'migration_history') THEN
        CREATE TABLE migration_history (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            applied_by VARCHAR(255)
        );
        
        CREATE INDEX idx_migration_name ON migration_history(migration_name);
        CREATE INDEX idx_applied_at ON migration_history(applied_at);
        
        RAISE NOTICE 'Created migration_history table';
    ELSE
        RAISE NOTICE 'Migration_history table already exists';
    END IF;
END $$; 