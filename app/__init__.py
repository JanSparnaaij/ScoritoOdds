from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import subprocess
from dotenv import load_dotenv
import os
from app.tasks import celery

# Load environment variables
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = ["SECRET_KEY"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"Environment variable {var} is not set")

# Ensure Playwright browsers are installed
try:
    subprocess.run(["playwright", "install"], check=True)
except Exception as e:
    print(f"Warning: Could not install Playwright browsers: {e}")

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache(config={
    "CACHE_TYPE": "SimpleCache",  # Use SimpleCache for now
    "CACHE_DEFAULT_TIMEOUT": 3600,  # Cache timeout (1 hour)
})

def create_app():
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

    # Test SimpleCache functionality
    try:
        cache.set("test_key", "test_value")
        if cache.get("test_key") == "test_value":
            print("SimpleCache is working!")
        else:
            print("SimpleCache setup failed!")
    except Exception as e:
        print(f"Error testing SimpleCache: {e}")

    return app
