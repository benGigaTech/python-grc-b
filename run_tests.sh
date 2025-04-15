#!/bin/bash
set -e

# Start the test containers
echo "Starting test containers..."
docker compose -f docker-compose.test.yml up -d

# Wait for the database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run the tests
echo "Running tests..."
docker compose -f docker-compose.test.yml exec web pytest -v

# Stop the test containers
echo "Stopping test containers..."
docker compose -f docker-compose.test.yml down
