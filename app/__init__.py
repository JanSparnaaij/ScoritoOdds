from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.celery_worker import celery
import os
from redis import Redis

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Configure Redis with SSL options if REDIS_URL is provided
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        redis_client = Redis.from_url(redis_url, ssl_cert_reqs=None)
        app.config["CACHE_TYPE"] = "RedisCache"
        app.config["CACHE_REDIS_CLIENT"] = redis_client

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Register blueprints
    from app.routes import main_bp, auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Attach Flask app context to Celery
    celery.conf.update(app.config)

    return app
