# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Set environment variables
ENV PYTHONPATH=/app

# Run with gunicorn from the correct directory
WORKDIR /app/cmmc_tracker
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "run:app"]