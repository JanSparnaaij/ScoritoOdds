from flask import Flask
from flask_migrate import Migrate
from redis import Redis
from app.models import db
from app.routes import main_bp, auth_bp
import os

# Initialize extensions
migrate = Migrate()

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Configure Redis with the self-signed certificate
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = Redis.from_url(
        redis_url,
        ssl_cert_reqs="required",
        ssl_ca_certs="/certificate.pem"
    )

    # expose client
    app.redis_client = redis_client

    # Initialize extensions
    db.init_app(app)
    print("DB initialized with app")
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
