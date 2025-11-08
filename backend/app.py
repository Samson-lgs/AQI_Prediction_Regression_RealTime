import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
    """Create and configure Flask application with all features"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Disable strict trailing slash requirement
    app.url_map.strict_slashes = False
    
    # Enable CORS for frontend (always send headers, even on errors/preflight)
    CORS(
        app,
        resources={
            r"/api/*": {"origins": "*"},
            r"/socket.io/*": {"origins": "*"},
        },
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "OPTIONS"],
        send_wildcard=True,
        always_send=True,
    )
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["500 per day", "100 per hour"],  # Increased for development
        storage_uri=os.getenv('REDIS_URL', 'memory://'),
        strategy="fixed-window"
    )
    
    # Apply rate limiting to API routes
    @limiter.request_filter
    def exempt_health_check():
        """Exempt health checks and cities endpoint from rate limiting"""
        try:
            # Exempt health endpoints and critical city list endpoint
            exempt_paths = ['/health', '/api/v1/health', '/api/v1/cities']
            return request.path in exempt_paths
        except Exception:
            return False
    
    logger.info("Rate limiter initialized")
    
    # Register enhanced API routes (with Swagger docs)
    try:
        from backend.api_routes import api_bp
        app.register_blueprint(api_bp)
        logger.info("Enhanced API routes registered with Swagger documentation at /api/v1/docs")
    except Exception as e:
        logger.warning(f"Could not load enhanced API routes: {e}, falling back to basic routes")
        from backend.routes import api_bp as basic_api_bp
        app.register_blueprint(basic_api_bp)
    
    # Disable WebSocket support for production stability
    # (Can be re-enabled later with compatible eventlet/gunicorn versions)
    app.socketio = None
    logger.info("WebSocket support disabled for stability")
    
    # Disable Redis cache for production stability on free tier
    logger.warning("Redis cache disabled - running without caching")
    
    # Root health check for backward compatibility
    @app.route('/health')
    @limiter.exempt
    def health():
        return {'status': 'ok', 'message': 'AQI Backend API is running'}, 200
    
    # API root endpoint
    @app.route('/')
    def api_root():
        return {
            'message': 'AQI Prediction API',
            'version': '1.0',
            'docs': '/api/v1/docs',
            'health': '/api/v1/health',
            'cities': '/api/v1/cities'
        }, 200
    
    # Cache stats endpoint
    @app.route('/api/v1/cache/stats')
    @limiter.exempt
    def cache_stats():
        try:
            from backend.cache_manager import get_cache_info
            return get_cache_info(), 200
        except Exception as e:
            return {'error': str(e)}, 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        return {'error': 'Rate limit exceeded', 'message': str(error)}, 429
    
    logger.info("Flask application created successfully")
    logger.info("=" * 70)
    logger.info("AQI Prediction System - Enhanced Backend")
    logger.info("=" * 70)
    logger.info("Features enabled:")
    logger.info("  ✓ RESTful API with Swagger docs (/api/v1/docs)")
    logger.info("  ✗ WebSocket real-time updates (disabled for stability)")
    logger.info("  ✗ Redis caching (disabled for free tier)")
    logger.info("  ✓ Rate limiting (500/day, 100/hour)")
    logger.info("  ✓ /api/v1/cities endpoint exempt from rate limits")
    logger.info("  ✓ CORS enabled for all origins")
    logger.info("=" * 70)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    logger.info("Starting Flask application on http://0.0.0.0:5000")
    logger.info("Starting with standard WSGI (production mode)")
    app.run(debug=True, port=5000, host='0.0.0.0')