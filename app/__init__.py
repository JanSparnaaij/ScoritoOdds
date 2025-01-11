from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import subprocess
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")
print(f"Loaded SECRET_KEY from .env: {os.getenv('SECRET_KEY')}")

# Ensure browsers are installed
try:
    subprocess.run(["playwright", "install"], check=True)
except Exception as e:
    print(f"Error installing Playwright browsers: {e}")

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Explicitly set SECRET_KEY from the environment
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    print(f"Explicitly set SECRET_KEY: {app.config['SECRET_KEY']}")

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


