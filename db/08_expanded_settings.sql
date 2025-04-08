-- Expanded Settings Migration
-- Adds settings for evidence lifecycle, email subjects, footer text, and favicon

DO $$ 
BEGIN
    -- Check if settings table exists before attempting inserts
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'settings') THEN
        
        -- Insert Evidence Settings (if they don't exist)
        INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES
        ('evidence.default_validity_days', '365', 'integer', 'Default validity period (in days) for newly uploaded evidence'),
        ('evidence.enable_auto_expiration', 'true', 'boolean', 'Automatically mark evidence as expired based on upload date and validity period')
        ON CONFLICT (setting_key) DO NOTHING;

        -- Insert Notification Settings (if they don't exist)
        INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES
        ('notification.email_subject_prefix', '[CMMC Tracker]', 'string', 'Prefix added to the subject line of all notification emails')
        ON CONFLICT (setting_key) DO NOTHING;

        -- Insert Application Branding Settings (if they don't exist)
        INSERT INTO settings (setting_key, setting_value, setting_type, description) VALUES
        ('app.footer_text', '© 2025 CMMC Compliance Tracker. All rights reserved.', 'string', 'Custom text displayed in the application footer'),
        ('app.favicon_url', '/static/img/favicon.ico', 'string', 'URL to the browser favicon image')
        ON CONFLICT (setting_key) DO NOTHING;

        RAISE NOTICE 'Inserted default values for expanded settings (evidence, notification, app branding) if they did not already exist.';
        
    ELSE
        RAISE NOTICE 'Settings table does not exist. Skipping insertion of expanded settings.';
    END IF;
END $$;