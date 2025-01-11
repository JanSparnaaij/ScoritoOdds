from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from playwright.__main__ import main as playwright_main
from dotenv import load_dotenv
import os

# Ensure browsers are installed
try:
    playwright_main(['install'])
except Exception as e:
    print(f"Error installing Playwright browsers: {e}")

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()

def create_app():
    # Load environment variables from .env
    load_dotenv()

    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
