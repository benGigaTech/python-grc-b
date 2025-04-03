#!/bin/bash
set -e

# Database waiting and migrations are handled by docker-entrypoint.sh

echo "Starting the application..."
cd /app/cmmc_tracker
exec gunicorn --bind 0.0.0.0:80 --workers 4 run:app 