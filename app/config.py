import os
import secrets
from datetime import timedelta


class Config:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY", secrets.token_hex(32))

    # Session Security
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    # Rate Limiting
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # API Keys (with validation)
    FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
    CURRENCY_LAYER_API_KEY1 = os.environ.get("CURRENCY_LAYER_API_KEY1")
    CURRENCY_LAYER_API_KEY2 = os.environ.get("CURRENCY_LAYER_API_KEY2")
    CURRENCY_LAYER_API_KEY3 = os.environ.get("CURRENCY_LAYER_API_KEY3")

    # Google Search API (optional)
    GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")

    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    JSON_SORT_KEYS = False

    # CORS Settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:8501,http://localhost:8000").split(",")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "app.log")

    # AI Agent Settings
    USE_CRAWL4AI = os.environ.get("USE_CRAWL4AI", "true").lower() == "true"
    AI_REQUEST_TIMEOUT = int(os.environ.get("AI_REQUEST_TIMEOUT", "30"))
    MAX_AI_RETRIES = int(os.environ.get("MAX_AI_RETRIES", "3"))

    # Data Settings
    MAX_DATA_POINTS = int(os.environ.get("MAX_DATA_POINTS", "10000"))
    CACHE_TTL_HOURS = int(os.environ.get("CACHE_TTL_HOURS", "24"))

    @staticmethod
    def validate_config():
        """Validate critical configuration settings"""
        required_keys = ['SECRET_KEY']
        for key in required_keys:
            if not getattr(Config, key, None):
                raise ValueError(f"Required configuration {key} is not set")

        # Validate API keys format (basic check) - warn if not set but don't fail
        api_keys = ['FINNHUB_API_KEY', 'GEMINI_API_KEY', 'ALPHA_VANTAGE_API_KEY']
        for key in api_keys:
            value = getattr(Config, key, None)
            if value and not isinstance(value, str):
                raise ValueError(f"API key {key} must be a string")
            elif not value:
                print(f"WARNING: {key} not set - some features may be limited")

        # Validate CORS origins format
        cors_origins = getattr(Config, 'CORS_ORIGINS', [])
        if isinstance(cors_origins, str):
            cors_origins = cors_origins.split(',')
        for origin in cors_origins:
            origin = origin.strip()
            if origin and not (origin.startswith('http://') or origin.startswith('https://')):
                raise ValueError(f"Invalid CORS origin format: {origin}")

        # Validate database URI format (basic check)
        db_uri = getattr(Config, 'SQLALCHEMY_DATABASE_URI', '')
        if db_uri and not (db_uri.startswith('sqlite:///') or db_uri.startswith('postgresql://')):
            print(f"WARNING: Database URI format may be invalid: {db_uri}")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])
