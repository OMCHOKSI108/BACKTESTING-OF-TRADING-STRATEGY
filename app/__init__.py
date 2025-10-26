from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv
import logging
import os
import time
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a')
    ]
)

# Security headers configuration
csp = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
    'font-src': "'self' https://fonts.gstatic.com",
    'img-src': "'self' data: https:",
    'connect-src': "'self' https://api.github.com"
}

def create_app(config_name=None):
    load_dotenv()
    app = Flask(__name__)

    # Load configuration
    from app.config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Validate configuration
    try:
        config_class.validate_config()
    except ValueError as e:
        app.logger.error(f"Configuration validation failed: {e}")
        raise

    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    # Security headers (only in production, but don't force HTTPS in containers)
    if os.environ.get('FLASK_ENV') == 'production':
        # Don't force HTTPS in container environments (let reverse proxy handle it)
        force_https = not os.environ.get('DOCKER_ENV', '').lower() == 'true'
        Talisman(app, content_security_policy=csp, force_https=force_https)

    # Request logging middleware
    @app.before_request
    def log_request_info():
        g.start_time = time.time()
        app.logger.info(f'{request.method} {request.url} - {get_remote_address()}')

    @app.after_request
    def log_response_info(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            app.logger.info('.2f')
        return response

    # Global error handlers
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        app.logger.warning(f'HTTP {e.code}: {e.description} - {request.url}')
        return jsonify({
            'success': False,
            'error': e.description,
            'code': e.code
        }), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.error(f'Unexpected error: {str(e)} - {request.url}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 500
        }), 500

    # Health check endpoint
    @app.route('/health')
    @limiter.exempt
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0'
        })

    # Register blueprints with rate limiting
    from app.routes.main import main_bp
    from app.routes.strategies import strategies_bp
    from app.routes.data_routes import data_bp
    from app.routes.strategy_routes import strategy_bp
    from app.routes.report_routes import report_bp
    from app.routes.performance_routes import performance_bp
    from app.routes.candle_routes import candle_bp
    from app.routes.ai_routes import ai_bp

    # Apply rate limits to blueprints
    limiter.limit("10 per minute")(ai_bp)  # Stricter limit for AI endpoints

    app.register_blueprint(main_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(candle_bp)
    app.register_blueprint(ai_bp, url_prefix='/api/ai')

    app.logger.info("Flask application initialized successfully")
    return app
