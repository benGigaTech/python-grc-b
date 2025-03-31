-- Settings table migration
-- Creates the table for storing application settings

-- Check if settings table exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'settings') THEN
        CREATE TABLE settings (
            setting_id SERIAL PRIMARY KEY,
            setting_key VARCHAR(255) NOT NULL UNIQUE,
            setting_value TEXT,
            setting_type VARCHAR(50) NOT NULL,
            description TEXT,
            last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(255)
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_settings_key ON settings(setting_key);
        
        -- Insert default settings
        INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES
        -- Application Settings
        ('app.name', 'CMMC Compliance Tracker', 'string', 'Application name displayed in the UI'),
        ('app.logo_url', '/static/img/logo.png', 'string', 'URL to the application logo image'),
        ('app.enable_registration', 'true', 'boolean', 'Allow user self-registration'),
        
        -- Security Settings
        ('security.max_login_attempts', '5', 'integer', 'Maximum failed login attempts before account lockout'),
        ('security.lockout_duration_minutes', '30', 'integer', 'Duration in minutes for account lockout after failed attempts'),
        ('security.require_mfa', 'false', 'boolean', 'Require MFA for all users'),
        
        -- Notification Settings
        ('notification.send_task_reminders', 'true', 'boolean', 'Send email reminders for upcoming tasks'),
        ('notification.reminder_days_before', '3', 'integer', 'Days before due date to send task reminders'),
        ('notification.email_from', 'noreply@example.com', 'string', 'From email address for notifications');
        
        RAISE NOTICE 'Created settings table with default values';
    ELSE
        RAISE NOTICE 'Settings table already exists';
    END IF;
END $$; 