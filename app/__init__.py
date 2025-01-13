from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from dotenv import load_dotenv
from app.celery_worker import celery

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache(config={"CACHE_TYPE": "RedisCache"})

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    # Register blueprints after app is fully initialized
    with app.app_context():
        from app.routes import main_bp, auth_bp
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')

    # Attach Flask app context to Celery
    celery.conf.update(app.config)

    return app
