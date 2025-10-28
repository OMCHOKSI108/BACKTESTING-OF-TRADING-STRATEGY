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

# Security headers configuration - more restrictive CSP
csp = {
    'default-src': "'self'",
    'script-src': "'self' https://cdn.jsdelivr.net https://code.jquery.com https://unpkg.com",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
    'font-src': "'self' https://fonts.gstatic.com",
    'img-src': "'self' data: https:",
    'connect-src': "'self' https://api.github.com https://generativelanguage.googleapis.com https://www.googleapis.com",
    'frame-src': "'none'",
    'object-src': "'none'",
    'base-uri': "'self'",
    'form-action': "'self'"
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

    # Prefer Redis-backed storage for rate-limiting when available
    redis_url = os.environ.get('REDIS_URL')
    limiter_kwargs = dict(key_func=get_remote_address, default_limits=["100 per day", "20 per hour", "5 per minute"]) 
    if redis_url:
        # Only enable Redis storage if the redis client dependency is available
        try:
            import redis as _redis_check  # noqa: F401
            limiter_kwargs['storage_uri'] = redis_url
        except Exception:
            app.logger.warning("REDIS_URL is set but 'redis' package is not installed - falling back to in-memory limiter storage")

    limiter = Limiter(app=app, **limiter_kwargs)

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
        payload = {
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0'
        }
        # If Redis configured, check connectivity
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            try:
                import redis as redis_lib
                r = redis_lib.from_url(redis_url, socket_connect_timeout=2)
                pong = r.ping()
                payload['redis'] = 'ok' if pong else 'unreachable'
            except Exception as e:
                payload['redis'] = f'error: {str(e)}'

        return jsonify(payload)

    @app.route('/health/redis')
    @limiter.exempt
    def health_redis():
        # Detailed redis health using cache module when available
        try:
            from app.services import cache as _cache

            info = _cache.cache_redis_health()
            return jsonify({"redis": info})
        except Exception as e:
            return jsonify({"redis": {"enabled": False, "error": str(e)}}), 500

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
