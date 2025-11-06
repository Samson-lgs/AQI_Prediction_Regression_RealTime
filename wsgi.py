"""
Gunicorn entry point for Render deployment
This file is in the root directory to ensure proper imports
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and create the Flask app
from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    # For local testing
    app.run(host='0.0.0.0', port=5000, debug=True)
