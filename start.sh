#!/bin/bash
set -e

echo "Waiting for database to be ready..."
for i in $(seq 1 30); do
    python -c "import psycopg2; psycopg2.connect(dbname='cmmc_db', user='cmmc_user', password='password', host='db', port='5432')" && break || echo "Waiting for database... attempt $i/30"
    sleep 2
done

echo "Checking if database needs to be initialized..."
python /app/seed_db.py

echo "Applying any pending database migrations..."
python /app/apply_migration.py

echo "Starting the application..."
cd /app/cmmc_tracker
exec gunicorn --bind 0.0.0.0:80 --workers 4 run:app 