#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database to be ready..."
python -c "
import sys
import time
import psycopg2

# Maximum number of retries
max_retries = 30
retry_interval = 2  # seconds

for i in range(max_retries):
    try:
        conn = psycopg2.connect(
            dbname='cmmc_db',
            user='cmmc_user',
            password='password',
            host='db',
            port='5432'
        )
        conn.close()
        print('Database is ready!')
        sys.exit(0)
    except psycopg2.OperationalError:
        print(f'Waiting for database... {i+1}/{max_retries}')
        time.sleep(retry_interval)

print('Could not connect to database after maximum retries')
sys.exit(1)
"

# Check if the database is empty (no users)
echo "Checking if database needs to be seeded..."
DB_EMPTY=$(python -c "
import psycopg2

try:
    conn = psycopg2.connect(
        dbname='cmmc_db',
        user='cmmc_user',
        password='password',
        host='db',
        port='5432'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    result = cursor.fetchone()
    conn.close()
    
    if result[0] == 0:
        print('1')  # Database is empty
    else:
        print('0')  # Database has users
except Exception as e:
    # If there's an error (like the table doesn't exist), we should seed
    print('1')
")

# Initialize the database if needed
if [ "$DB_EMPTY" = "1" ]; then
    echo "Database is empty or tables don't exist. Initializing database..."
    python /app/seed_db.py
    echo "Database initialization complete!"
else
    echo "Database already has data. Skipping initialization."
fi

# Start the main process
exec "$@" 