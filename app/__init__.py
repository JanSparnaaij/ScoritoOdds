from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import subprocess
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = ["SECRET_KEY", "DATABASE_URL"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"Environment variable {var} is not set")

# Ensure Playwright browsers are installed
try:
    subprocess.run(["playwright", "install"], check=True)
    print("Playwright browsers installed successfully.")
except Exception as e:
    print(f"Warning: Could not install Playwright browsers: {e}")

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache(config={
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
})

def setup_logging(app):
    """Configure application logging."""
    if not app.debug:
        handler = RotatingFileHandler("app.log", maxBytes=100000, backupCount=3)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Explicitly set SECRET_KEY
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Set up logging
    setup_logging(app)

    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
