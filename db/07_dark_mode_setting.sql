-- Dark mode setting migration
-- Adds dark mode setting to application settings

-- Check if settings table exists before attempting to add new setting
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'settings') THEN
        -- Check if the setting already exists
        IF NOT EXISTS (SELECT 1 FROM settings WHERE setting_key = 'app.enable_dark_mode') THEN
            -- Insert dark mode setting
            INSERT INTO settings (setting_key, setting_value, setting_type, description) 
            VALUES ('app.enable_dark_mode', 'false', 'boolean', 'Enable dark mode as the default theme');
            
            RAISE NOTICE 'Added dark mode setting to settings table';
        ELSE
            RAISE NOTICE 'Dark mode setting already exists';
        END IF;
    ELSE
        RAISE NOTICE 'Settings table does not exist';
    END IF;
END $$; 