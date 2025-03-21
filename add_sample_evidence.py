#!/usr/bin/env python
"""
add_sample_evidence.py - Add sample evidence records to the database for testing

Run this script after applying migrations to populate the evidence table with test data.
"""

import os
import logging
import psycopg2
from datetime import datetime, timedelta
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'cmmc_db')
DB_USER = os.environ.get('DB_USER', 'cmmc_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')

# Sample evidence data
SAMPLE_EVIDENCE = [
    {
        "title": "Access Control Policy",
        "description": "Organizational policy document detailing access control procedures and requirements",
        "filetype": "application/pdf",
        "filesize": 1024 * 1024 * 2,  # 2MB
        "uploadedby": "admin",
        "expirationdate": (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
        "status": "Current"
    },
    {
        "title": "System Configuration Baseline",
        "description": "Configuration baseline for all organization systems",
        "filetype": "application/xlsx",
        "filesize": 1024 * 512,  # 512KB
        "uploadedby": "admin",
        "expirationdate": (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'),
        "status": "Current"
    },
    {
        "title": "Security Assessment Report",
        "description": "Annual security assessment results and findings",
        "filetype": "application/pdf",
        "filesize": 1024 * 1024 * 5,  # 5MB
        "uploadedby": "user",
        "expirationdate": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
        "status": "Current"
    },
    {
        "title": "Security Training Completion Records",
        "description": "Records of employee security awareness training completion",
        "filetype": "application/pdf",
        "filesize": 1024 * 768,  # 768KB
        "uploadedby": "user",
        "expirationdate": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        "status": "Expiring Soon"
    },
    {
        "title": "Historical Risk Assessment",
        "description": "Previous year's risk assessment document",
        "filetype": "application/pdf",
        "filesize": 1024 * 1024 * 3,  # 3MB
        "uploadedby": "admin",
        "expirationdate": (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
        "status": "Expired"
    }
]

def add_sample_evidence():
    """Add sample evidence records to the database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # First, check if the evidence table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'evidence'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.error("❌ Evidence table does not exist in the database")
            logger.error("Please run the migrations first: python apply_migration.py")
            return
        
        # Check if there are any controls to associate evidence with
        cursor.execute("SELECT controlid FROM controls LIMIT 10")
        control_ids = cursor.fetchall()
        
        if not control_ids:
            logger.error("❌ No controls found in the database")
            logger.error("Please run seed_db.py first to populate the controls table")
            return
        
        # Flatten the control_ids list
        control_ids = [control[0] for control in control_ids]
        
        # Get current timestamp for upload dates
        now = datetime.now().strftime('%Y-%m-%d')
        
        # Add sample evidence for each control
        sample_count = 0
        for i, evidence in enumerate(SAMPLE_EVIDENCE):
            # Select a random control ID
            control_id = random.choice(control_ids)
            
            # Generate a filepath
            filepath = f"/uploads/{control_id}/{now.replace('-', '')}_{evidence['title'].replace(' ', '_')}.{evidence['filetype'].split('/')[-1]}"
            
            # Insert the evidence record
            cursor.execute("""
                INSERT INTO evidence (
                    controlid, title, description, filepath, filetype, filesize,
                    uploadedby, uploaddate, expirationdate, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                control_id,
                evidence['title'],
                evidence['description'],
                filepath,
                evidence['filetype'],
                evidence['filesize'],
                evidence['uploadedby'],
                now,
                evidence['expirationdate'],
                evidence['status']
            ))
            sample_count += 1
        
        conn.commit()
        logger.info(f"✅ Added {sample_count} sample evidence records to the database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error adding sample evidence: {e}")

if __name__ == "__main__":
    add_sample_evidence() 