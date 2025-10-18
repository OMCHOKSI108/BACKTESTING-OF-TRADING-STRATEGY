from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.strategies import strategies_bp
    from app.routes.data_routes import data_bp
    from app.routes.strategy_routes import strategy_bp
    from app.routes.report_routes import report_bp
    from app.routes.performance_routes import performance_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(performance_bp)

    return app
