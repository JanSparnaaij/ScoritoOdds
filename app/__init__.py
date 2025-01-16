from flask import Flask
from flask_migrate import Migrate
from redis import Redis, ConnectionError
from app.models import db
from app.routes import main_bp, auth_bp
import os
import time

# Initialize extensions
migrate = Migrate()

def initialize_redis():
    """Initialize Redis with retries."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    for attempt in range(5):  # Retry up to 5 times
        try:
            return Redis.from_url(
                redis_url,
                ssl_cert_reqs="required",
                ssl_ca_certs="/certificate.pem",
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
        except ConnectionError as e:
            if attempt < 4:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise e

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize Redis
    global redis_client
    redis_client = initialize_redis()
    app.redis_client = redis_client

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
