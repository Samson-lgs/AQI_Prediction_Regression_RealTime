import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from backend.routes import api_bp
from config.settings import CITIES
import logging

# Configure logging based on environment
log_level = logging.DEBUG if os.getenv('FLASK_DEBUG', '0') == '1' else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    # Enable CORS for frontend (allow Render frontend origin explicitly and GET/OPTIONS)
    frontend_origin = os.getenv('FRONTEND_ORIGIN', '*')
    CORS(
        app,
        resources={r"/api/*": {"origins": frontend_origin}},
        supports_credentials=False,
        methods=["GET", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
        max_age=3600
    )
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/styles.css')
    def send_styles():
        return send_from_directory('../frontend', 'styles.css')
    
    @app.route('/script.js')
    def send_script():
        return send_from_directory('../frontend', 'script.js')
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting Flask application...")
    app.run(debug=True, port=5000, host='0.0.0.0')