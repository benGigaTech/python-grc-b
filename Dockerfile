# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Make the start script executable
RUN chmod +x /app/start.sh

# Make port 80 available outside the container
EXPOSE 80

# Set Python path
ENV PYTHONPATH=/app:/app/cmmc_tracker

# Run the start script
CMD ["/app/start.sh"]