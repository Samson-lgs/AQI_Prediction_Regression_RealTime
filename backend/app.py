from flask import Flask, render_template
from backend.routes import api_bp
from config.settings import CITIES
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html', cities=CITIES)
    
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
    app.run(debug=True, port=5000)