"""Entry point for the CMMC Tracker application."""

import os
import sys

# Add the parent directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the create_app function
from app import create_app

# Create the application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Run the application
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 80)))