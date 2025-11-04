import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from backend.routes import api_bp
from config.settings import CITIES
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/css/<path:path>')
    def send_css(path):
        return send_from_directory('../frontend', path)
    
    @app.route('/js/<path:path>')
    def send_js(path):
        return send_from_directory('../frontend', path)
    
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