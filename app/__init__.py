from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

# Validate environment variables
REQUIRED_ENV_VARS = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
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
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL"),
})

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Test Redis connection
    try:
        cache.cache._client.ping()
        print("Redis connection successful!")
    except Exception as e:
        print(f"Redis connection failed: {e}")

    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
