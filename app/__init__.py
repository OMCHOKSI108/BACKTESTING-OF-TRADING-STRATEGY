from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    from app.routes.main import main_bp
    from app.routes.strategies import strategies_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(strategies_bp)

    return app
