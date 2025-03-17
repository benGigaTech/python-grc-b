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
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

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
                    'Control imported from JSON file during database seeding'
                ))
                
            except Exception as e:
                logger.warning(f"Error importing control {control.get('ControlID', 'unknown')}: {e}")
                # Continue with next control
        
        # Add review dates to three random controls
        cursor.execute("SELECT controlid FROM controls ORDER BY RANDOM() LIMIT 3")
        random_controls = [row[0] for row in cursor.fetchall()]
        
        if len(random_controls) >= 3:
            today = date.today()
            
            # One control with review in the future
            next_review = today + timedelta(days=30)
            last_review = today - timedelta(days=335)
            cursor.execute('''
                UPDATE controls 
                SET lastreviewdate = %s, nextreviewdate = %s
                WHERE controlid = %s
            ''', (last_review, next_review, random_controls[0]))
            
            # One control with review soon
            next_review = today + timedelta(days=7)
            last_review = today - timedelta(days=358)
            cursor.execute('''
                UPDATE controls 
                SET lastreviewdate = %s, nextreviewdate = %s
                WHERE controlid = %s
            ''', (last_review, next_review, random_controls[1]))
            
            # One control past due
            next_review = today - timedelta(days=15)
            last_review = today - timedelta(days=380)
            cursor.execute('''
                UPDATE controls 
                SET lastreviewdate = %s, nextreviewdate = %s
                WHERE controlid = %s
            ''', (last_review, next_review, random_controls[2]))
            
            logger.info("Added review dates to sample controls")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully imported controls from {CONTROLS_JSON_FILE}")
        
    except Exception as e:
        logger.error(f"Error importing controls: {e}")
        raise

def create_sample_tasks():
    """Create sample tasks for demonstration purposes"""
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
        
        # Get 3 random control IDs
        cursor.execute("SELECT controlid FROM controls ORDER BY RANDOM() LIMIT 3")
        control_ids = [row[0] for row in cursor.fetchall()]
        
        if not control_ids:
            logger.warning("No controls found in database. Cannot create sample tasks.")
            conn.close()
            return
        
        logger.info("Creating sample tasks...")
        
        today = date.today()
        
        # Sample tasks to create
        sample_tasks = [
            {
                "controlid": control_ids[0] if len(control_ids) > 0 else None,
                "taskdescription": "Review access control policies and ensure compliance",
                "assignedto": "user",
                "duedate": today + timedelta(days=15),
                "status": "Open",
                "confirmed": 0,
                "reviewer": "admin"
            },
            {
                "controlid": control_ids[0] if len(control_ids) > 0 else None,
                "taskdescription": "Document current access control implementation",
                "assignedto": "user",
                "duedate": today - timedelta(days=10),
                "status": "Open",
                "confirmed": 0,
                "reviewer": "admin"
            },
            {
                "controlid": control_ids[1] if len(control_ids) > 1 else control_ids[0],
                "taskdescription": "Update system security plan",
                "assignedto": "user",
                "duedate": today - timedelta(days=30),
                "status": "Completed",
                "confirmed": 1,
                "reviewer": "admin"
            }
        ]
        
        for i, task in enumerate(sample_tasks):
            if task["controlid"]:
                cursor.execute('''
                    INSERT INTO tasks (
                        controlid, 
                        taskdescription, 
                        assignedto, 
                        duedate, 
                        status, 
                        confirmed, 
                        reviewer
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING taskid
                ''', (
                    task["controlid"],
                    task["taskdescription"],
                    task["assignedto"],
                    task["duedate"],
                    task["status"],
                    task["confirmed"],
                    task["reviewer"]
                ))
                
                task_id = cursor.fetchone()[0]
                
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
                    'Create Task', 
                    'Task', 
                    str(task_id),
                    'Sample task created during database seeding'
                ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Sample tasks created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample tasks: {e}")
        raise

def main():
    """Main function to initialize the database"""
    try:
        logger.info("Starting database initialization...")
        
        # First check database connection
        try:
            conn = get_db_connection()
            conn.close()
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.info("Make sure the database is running and environment variables are correctly set")
            return 1
        
        # Create tables
        create_tables()
        
        # Seed users
        seed_users()
        
        # Import controls from JSON
        import_controls()
        
        # Create sample tasks
        create_sample_tasks()
        
        logger.info("Database initialization complete!")
        logger.info("Default admin credentials: username=admin, password=adminpassword")
        logger.info("Default user credentials: username=user, password=userpassword")
        
        return 0
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())