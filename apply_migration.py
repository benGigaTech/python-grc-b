#!/usr/bin/env python
"""
apply_migration.py - Applies SQL migration scripts to the database
Run this script to execute SQL migration files

Usage:
    python apply_migration.py [filename.sql]
    
If no filename is provided, all .sql files in the db directory will be executed.
"""

import os
import sys
import time
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def get_db_connection():
    """Connect to the application database"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("Successfully connected to the database")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection failed (attempt {attempt+1}/{max_retries}). Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to the database after {max_retries} attempts: {e}")
                raise

def apply_migration_file(filepath):
    """Apply a single SQL migration file to the database"""
    try:
        with open(filepath, 'r') as f:
            sql_script = f.read()
            
        migration_name = os.path.basename(filepath)
        logger.info(f"Applying migration: {migration_name}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if migration has already been applied
        cursor.execute(
            "SELECT COUNT(*) FROM migration_history WHERE migration_name = %s",
            (migration_name,)
        )
        
        # If table doesn't exist yet, psycopg2 will raise an exception
        try:
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Migration {migration_name} has already been applied, skipping")
                cursor.close()
                conn.close()
                return
        except psycopg2.Error:
            # Migration_history table probably doesn't exist yet
            logger.info("Migration history table doesn't exist yet, will be created")
        
        # Execute the SQL script
        cursor.execute(sql_script)
        
        # Try to record this migration in the tracking table
        try:
            cursor.execute(
                "INSERT INTO migration_history (migration_name, applied_by) VALUES (%s, %s)",
                (migration_name, os.environ.get('USER', 'system'))
            )
        except psycopg2.Error as e:
            # This might fail if we're running the migration that creates the migration_history table
            logger.warning(f"Could not record migration in history table: {e}")
        
        conn.commit()
        logger.info(f"Migration applied successfully: {migration_name}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error applying migration {os.path.basename(filepath)}: {e}")
        raise

def main():
    """Main function to apply migrations"""
    # Check if a specific migration file was specified
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
        if os.path.exists(migration_file):
            apply_migration_file(migration_file)
        else:
            logger.error(f"Migration file not found: {migration_file}")
            sys.exit(1)
    else:
        # Apply all SQL files in the db directory
        db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
        if not os.path.exists(db_dir):
            logger.error(f"Database directory not found: {db_dir}")
            sys.exit(1)
            
        # Apply migration_tracking.sql first if it exists
        tracking_file = os.path.join(db_dir, 'migration_tracking.sql')
        if os.path.exists(tracking_file):
            apply_migration_file(tracking_file)
        
        # Then apply all other migration files
        migration_files = [
            f for f in os.listdir(db_dir) 
            if f.endswith('.sql') and f != 'init.sql' and f != 'migration_tracking.sql'
        ]
        
        if not migration_files:
            logger.info("No migration files found to apply")
            return
            
        for migration_file in sorted(migration_files):
            apply_migration_file(os.path.join(db_dir, migration_file))
            
    logger.info("All migrations completed successfully")

if __name__ == "__main__":
    main() 