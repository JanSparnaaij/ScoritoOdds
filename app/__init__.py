from flask import Flask
from flask_migrate import Migrate
from redis import Redis, ConnectionError, ConnectionPool
from app.models import db
from app.routes import main_bp, auth_bp
import os
import time
import logging

# Initialize extensions
migrate = Migrate()
logger = logging.getLogger(__name__)

def initialize_redis():
    """Initialize Redis with retries and proper SSL configuration."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ssl_cert_path = os.getenv("SSL_CERT_PATH", "/certificate.pem")

    # Parse SSL configuration only for rediss:// URLs
    ssl_options = {}
    if redis_url.startswith("rediss://"):
        ssl_options = {
            "ssl_cert_reqs": "CERT_OPTIONAL",  # Change to 'CERT_REQUIRED' if stricter validation is needed
            "ssl_ca_certs": ssl_cert_path,
        }

    # Use a connection pool for SSL
    pool = ConnectionPool.from_url(redis_url, **ssl_options)

    for attempt in range(5):
        try:
            logger.info(f"Attempting Redis connection, attempt {attempt + 1}...")
            return Redis(connection_pool=pool)
        except ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}")
            if attempt < 4:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error("Exceeded maximum retries for Redis connection.")
                raise e

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize Redis
    app.redis_client = initialize_redis()

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
