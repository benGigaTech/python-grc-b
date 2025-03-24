-- 04_mfa_migration.sql
-- Add MFA capabilities to the users table

DO $$ 
BEGIN
    -- Check if mfa_enabled column exists in users table
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'mfa_enabled'
    ) THEN
        -- Add column for enabling/disabling MFA
        ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT false;
    END IF;

    -- Check if mfa_secret column exists in users table
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'mfa_secret'
    ) THEN
        -- Add column for storing the TOTP secret key
        ALTER TABLE users ADD COLUMN mfa_secret TEXT;
    END IF;

    -- Check if mfa_backup_codes column exists in users table
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'mfa_backup_codes'
    ) THEN
        -- Add column for storing backup codes (JSON array format)
        ALTER TABLE users ADD COLUMN mfa_backup_codes TEXT;
    END IF;

    RAISE NOTICE 'MFA migration completed successfully.';
END $$; 