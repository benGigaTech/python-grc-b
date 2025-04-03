# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Install system dependencies needed by python-magic and psql client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Make scripts executable
RUN chmod +x /app/start.sh
RUN chmod +x /app/docker-entrypoint.sh

# Make port 80 available outside the container
EXPOSE 80

# Set Python path
ENV PYTHONPATH=/app:/app/cmmc_tracker

# Set entrypoint and default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["/app/start.sh"]