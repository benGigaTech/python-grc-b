@echo off
echo Starting test containers...
docker compose -f docker-compose.test.yml up -d

echo Waiting for database to be ready...
timeout /t 5

echo Running tests...
docker compose -f docker-compose.test.yml exec web pytest -v

echo Stopping test containers...
docker compose -f docker-compose.test.yml down
