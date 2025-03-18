#!/usr/bin/env python3
"""
Test authentication for the CMMC Tracker application.
This script verifies that the default admin and user credentials work correctly.
"""

import psycopg2
from werkzeug.security import check_password_hash

def test_authentication():
    """Test authentication for the default users"""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='cmmc_db',
            user='cmmc_user',
            password='password',
            host='db',
            port='5432'
        )
        cursor = conn.cursor()
        
        # Get user credentials
        cursor.execute("SELECT username, password FROM users WHERE username = 'admin'")
        admin_result = cursor.fetchone()
        
        cursor.execute("SELECT username, password FROM users WHERE username = 'user'")
        user_result = cursor.fetchone()
        
        # Check admin password
        print("Testing password for user 'admin':")
        admin_password_matches = check_password_hash(admin_result[1], 'adminpassword')
        print(f"Result: {'SUCCESS' if admin_password_matches else 'FAILED'}\n")
        
        # Check user password
        print("Testing password for user 'user':")
        user_password_matches = check_password_hash(user_result[1], 'userpassword')
        print(f"Result: {'SUCCESS' if user_password_matches else 'FAILED'}")
        
        cursor.close()
        conn.close()
        
        # Return overall result
        return admin_password_matches and user_password_matches
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_authentication() 