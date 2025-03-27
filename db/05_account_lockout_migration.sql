-- 05_account_lockout_migration.sql
-- Add account lockout functionality to the users table

-- Check if columns exist before adding them to avoid errors
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'failed_login_attempts'
    ) THEN
        -- Add column for tracking failed login attempts
        ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
        RAISE NOTICE 'Added failed_login_attempts column to users table';
    ELSE
        RAISE NOTICE 'failed_login_attempts column already exists';
    END IF;

    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'account_locked_until'
    ) THEN
        -- Add column for tracking when account will be unlocked
        ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMPTZ DEFAULT NULL;
        RAISE NOTICE 'Added account_locked_until column to users table';
    ELSE
        RAISE NOTICE 'account_locked_until column already exists';
    END IF;
END $$;

-- Add to migrations tracking table if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'migrations'
    ) THEN
        INSERT INTO migrations (filename, applied_at)
        VALUES ('05_account_lockout_migration.sql', NOW());
        RAISE NOTICE 'Updated migrations tracking table';
    END IF;
END $$; 