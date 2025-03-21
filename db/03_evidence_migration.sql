-- Evidence table migration
-- Creates the table for storing evidence records

-- Check if evidence table exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'evidence') THEN
        CREATE TABLE evidence (
            evidenceid SERIAL PRIMARY KEY,
            controlid TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            filepath TEXT,
            filetype TEXT,
            filesize BIGINT,
            uploadedby TEXT NOT NULL,
            uploaddate TEXT NOT NULL,
            expirationdate TEXT,
            status TEXT NOT NULL DEFAULT 'Current',
            FOREIGN KEY (controlid) REFERENCES controls(controlid) ON DELETE CASCADE
        );
        
        CREATE INDEX idx_evidence_controlid ON evidence(controlid);
        CREATE INDEX idx_evidence_uploaddate ON evidence(uploaddate);
        CREATE INDEX idx_evidence_expirationdate ON evidence(expirationdate);
        CREATE INDEX idx_evidence_status ON evidence(status);
        
        RAISE NOTICE 'Created evidence table';
    ELSE
        RAISE NOTICE 'Evidence table already exists';
    END IF;
END $$; 