"""
seed_db.py - Initialize and seed the PostgreSQL database for CMMC Compliance Tracker
Run this script on first-time setup to create database tables and populate initial data

Usage:
    docker compose exec web python seed_db.py

This script replaces migrate.py for initializing a fresh PostgreSQL database.
"""

import os
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta, timezone
import logging
import sys

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

# Path to controls JSON file - use absolute path
CONTROLS_JSON_FILE = os.environ.get('CONTROLS_JSON_FILE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cmmc_controls.json'))

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
            logger.info("Database connection successful")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                import time
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise

def check_db_initialized():
    """Check if database is already initialized by checking for users table with data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('users', 'controls', 'tasks', 'auditlogs')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if len(existing_tables) < 4:
            logger.info(f"Found {len(existing_tables)} of 4 required tables. Database needs initialization.")
            cursor.close()
            conn.close()
            return False
            
        # Check if user data exists
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        if user_count > 0:
            logger.info(f"Database already contains {user_count} users. Skipping initialization.")
            return True
        else:
            logger.info("Tables exist but no users found. Need to populate with data.")
            return False
            
    except psycopg2.Error as e:
        logger.info(f"Database structure check failed: {e}. Database needs initialization.")
        return False

def create_tables():
    """Create database tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Creating tables...")
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                userid SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                isadmin INTEGER NOT NULL DEFAULT 0,
                email VARCHAR(255),
                resettoken VARCHAR(255),
                tokenexpiration TIMESTAMP
            )
        ''')
        
        # Controls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS controls (
                controlid VARCHAR(20) PRIMARY KEY,
                controlname VARCHAR(255) NOT NULL,
                controldescription TEXT,
                nist_sp_800_171_mapping VARCHAR(255),
                policyreviewfrequency VARCHAR(50),
                lastreviewdate DATE,
                nextreviewdate DATE
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                taskid SERIAL PRIMARY KEY,
                controlid VARCHAR(20) NOT NULL REFERENCES controls(controlid),
                taskdescription TEXT NOT NULL,
                assignedto VARCHAR(50) NOT NULL,
                duedate DATE,
                status VARCHAR(50) NOT NULL,
                confirmed INTEGER DEFAULT 0,
                reviewer VARCHAR(50),
                last_notification TIMESTAMP
            )
        ''')
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auditlogs (
                logid SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                username VARCHAR(50) NOT NULL,
                action VARCHAR(50) NOT NULL,
                objecttype VARCHAR(50) NOT NULL,
                objectid VARCHAR(50) NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        logger.info("Tables created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def load_controls_from_json():
    """Load CMMC controls from JSON file"""
    try:
        if not os.path.exists(CONTROLS_JSON_FILE):
            logger.error(f"Controls JSON file not found: {CONTROLS_JSON_FILE}")
            return []
            
        with open(CONTROLS_JSON_FILE, 'r') as f:
            data = json.load(f)
            
        # Handle both array and single object formats
        if isinstance(data, dict):
            controls_data = [data]
        else:
            controls_data = data
            
        logger.info(f"Loaded {len(controls_data)} controls from JSON file")
        return controls_data
        
    except Exception as e:
        logger.error(f"Error loading controls from JSON: {e}")
        return []

def seed_users():
    """Seed admin and regular users if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()[0] > 0
        
        if not admin_exists:
            logger.info("Creating admin user...")
            admin_password = generate_password_hash('adminpassword')
            cursor.execute('''
                INSERT INTO users (username, password, isadmin, email)
                VALUES (%s, %s, %s, %s)
            ''', ('admin', admin_password, 1, 'admin@example.com'))
            
            # Add audit log for admin creation
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute('''
                INSERT INTO auditlogs (timestamp, username, action, objecttype, objectid, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (now, 'SYSTEM', 'Create User', 'User', '1', 'Initial admin user created during database seeding'))
            
            logger.info("Admin user created")
            
        else:
            logger.info("Admin user already exists")
        
        # Add a regular user if they don't exist
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'user'")
        user_exists = cursor.fetchone()[0] > 0
        
        if not user_exists:
            logger.info("Creating regular user...")
            regular_password = generate_password_hash('userpassword')
            cursor.execute('''
                INSERT INTO users (username, password, isadmin, email)
                VALUES (%s, %s, %s, %s)
            ''', ('user', regular_password, 0, 'user@example.com'))
            
            # Add audit log for user creation
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute('''
                INSERT INTO auditlogs (timestamp, username, action, objecttype, objectid, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (now, 'SYSTEM', 'Create User', 'User', '2', 'Regular user created during database seeding'))
            
            logger.info("Regular user created")
        else:
            logger.info("Regular user already exists")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error seeding users: {e}")
        raise

def import_controls():
    """Import controls from JSON file"""
    try:
        controls_data = load_controls_from_json()
        
        if not controls_data:
            logger.error("No controls loaded from JSON file. Make sure your file exists and is properly formatted.")
            return
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if controls already exist
        cursor.execute("SELECT COUNT(*) FROM controls")
        controls_exist = cursor.fetchone()[0] > 0
        
        if controls_exist:
            logger.info("Controls already exist in the database. Skipping import.")
            conn.close()
            return
        
        logger.info(f"Importing {len(controls_data)} controls...")
        
        # Import controls
        for control in controls_data:
            try:
                cursor.execute('''
                    INSERT INTO controls (
                        controlid, 
                        controlname, 
                        controldescription, 
                        nist_sp_800_171_mapping, 
                        policyreviewfrequency
                    ) VALUES (%s, %s, %s, %s, %s)
                ''', (
                    control.get("ControlID", ""),
                    control.get("ControlName", ""),
                    control.get("ControlDescription", ""),
                    control.get("NIST_SP_800_171_Mapping", ""),
                    "Annual"  # Default review frequency
                ))
                
                # Add audit log
                now = datetime.now(timezone.utc).isoformat()
                cursor.execute('''
                    INSERT INTO auditlogs (
                        timestamp, 
                        username, 
                        action, 
                        objecttype, 
                        objectid, 
                        details
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    now,
                    'SYSTEM',
                    'Create Control',
                    'Control',
                    control.get("ControlID", ""),
                    f"Control imported during database seeding: {control.get('ControlName', '')}"
                ))
                
            except psycopg2.Error as e:
                logger.error(f"Error importing control {control.get('ControlID', '')}: {e}")
        
        # Add review dates for a subset of controls
        today = date.today()
        
        # Set some controls as recently reviewed
        cursor.execute('''
            UPDATE controls 
            SET lastreviewdate = %s, nextreviewdate = %s 
            WHERE controlid IN (SELECT controlid FROM controls LIMIT 20)
        ''', (
            (today - timedelta(days=30)).isoformat(),
            (today + timedelta(days=335)).isoformat()
        ))
        
        # Set some controls as due for review soon
        cursor.execute('''
            UPDATE controls 
            SET lastreviewdate = %s, nextreviewdate = %s 
            WHERE controlid IN (SELECT controlid FROM controls OFFSET 20 LIMIT 5)
        ''', (
            (today - timedelta(days=350)).isoformat(),
            (today + timedelta(days=15)).isoformat()
        ))
        
        # Set some controls as overdue for review
        cursor.execute('''
            UPDATE controls 
            SET lastreviewdate = %s, nextreviewdate = %s 
            WHERE controlid IN (SELECT controlid FROM controls OFFSET 25 LIMIT 3)
        ''', (
            (today - timedelta(days=400)).isoformat(),
            (today - timedelta(days=35)).isoformat()
        ))
        
        logger.info("Added review dates to sample controls")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully imported controls from {CONTROLS_JSON_FILE}\n")
        
    except Exception as e:
        logger.error(f"Error importing controls: {e}")
        raise

def create_sample_tasks():
    """Create sample tasks for demonstration"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if tasks already exist
        cursor.execute("SELECT COUNT(*) FROM tasks")
        tasks_exist = cursor.fetchone()[0] > 0
        
        if tasks_exist:
            logger.info("Tasks already exist in the database. Skipping sample task creation.")
            conn.close()
            return
            
        logger.info("Creating sample tasks...")
        
        today = date.today()
        
        # Get some control IDs to assign tasks to
        cursor.execute("SELECT controlid FROM controls LIMIT 15")
        control_ids = [row[0] for row in cursor.fetchall()]
        
        if not control_ids:
            logger.warning("No controls found to assign tasks to.")
            conn.close()
            return
        
        # Create some open tasks
        for i, control_id in enumerate(control_ids[:5]):
            task_due_date = (today + timedelta(days=10 + i)).isoformat()
            cursor.execute('''
                INSERT INTO tasks (
                    controlid, taskdescription, assignedto, duedate, status, confirmed
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                control_id,
                f"Review and update documentation for {control_id}",
                "user",
                task_due_date,
                "Open",
                0
            ))
        
        # Create some tasks pending confirmation
        for i, control_id in enumerate(control_ids[5:8]):
            task_due_date = (today + timedelta(days=5 + i)).isoformat()
            cursor.execute('''
                INSERT INTO tasks (
                    controlid, taskdescription, assignedto, duedate, status, confirmed
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                control_id,
                f"Implement controls specified in {control_id}",
                "user",
                task_due_date,
                "Pending Confirmation",
                0
            ))
        
        # Create some completed tasks
        for i, control_id in enumerate(control_ids[8:12]):
            task_due_date = (today - timedelta(days=5 + i)).isoformat()
            cursor.execute('''
                INSERT INTO tasks (
                    controlid, taskdescription, assignedto, duedate, status, confirmed, reviewer
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                control_id,
                f"Update risk assessment for {control_id}",
                "user",
                task_due_date,
                "Completed",
                1,
                "admin"
            ))
        
        # Create some overdue tasks
        for i, control_id in enumerate(control_ids[12:]):
            task_due_date = (today - timedelta(days=3 + i)).isoformat()
            cursor.execute('''
                INSERT INTO tasks (
                    controlid, taskdescription, assignedto, duedate, status, confirmed
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                control_id,
                f"Complete security assessment for {control_id}",
                "admin",
                task_due_date,
                "Open",
                0
            ))
        
        # Add audit logs for task creation
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute('''
            INSERT INTO auditlogs (
                timestamp, username, action, objecttype, objectid, details
            ) VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            now,
            'SYSTEM',
            'Create Tasks',
            'Task',
            '0',
            'Sample tasks created during database seeding'
        ))
        
        conn.commit()
        logger.info("Sample tasks created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating sample tasks: {e}")
        raise

def main():
    """Initialize and seed the database"""
    try:
        logger.info("Starting database initialization...")
        
        # Check if database is already initialized
        if check_db_initialized():
            logger.info("Database already initialized. Skipping.")
            return
        
        # Create tables
        create_tables()
        
        # Seed users
        seed_users()
        
        # Import controls
        import_controls()
        
        # Create sample tasks
        create_sample_tasks()
        
        logger.info("Database initialization complete!")
        logger.info("Default admin credentials: username=admin, password=adminpassword")
        logger.info("Default user credentials: username=user, password=userpassword")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())