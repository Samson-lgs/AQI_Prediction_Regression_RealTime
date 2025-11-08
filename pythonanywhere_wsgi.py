#!/usr/bin/env python3
"""
WSGI Configuration for PythonAnywhere Deployment

INSTRUCTIONS:
1. Copy this file content
2. Go to PythonAnywhere Web tab
3. Click on WSGI configuration file
4. Replace content with this file
5. Change YOUR_USERNAME to your actual PythonAnywhere username
6. Save and reload the web app
"""

import sys
import os

# ============================================================================
# CONFIGURATION - CHANGE THIS!
# ============================================================================
USERNAME = 'YOUR_USERNAME'  # ← CHANGE THIS to your PythonAnywhere username!
# ============================================================================

# Add project directory to Python path
project_home = f'/home/{USERNAME}/AQI_Prediction_Regression_RealTime'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(project_home, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded environment variables from {env_path}")
    else:
        print(f"⚠ Warning: .env file not found at {env_path}")
except ImportError:
    print("⚠ Warning: python-dotenv not installed, skipping .env loading")

# Set environment defaults if not provided
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

# Import and create Flask application
try:
    from backend.app import create_app
    application = create_app()
    print("✓ Flask application created successfully")
except Exception as e:
    print(f"✗ Error creating Flask application: {e}")
    raise

# For debugging - remove in production if needed
if __name__ == '__main__':
    application.run()
