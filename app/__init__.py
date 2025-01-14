from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from redis import Redis

import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Configure Redis with the self-signed certificate
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = Redis.from_url(
        redis_url,
        ssl=True,
        ssl_cert_reqs="required",
        ssl_ca_certs=r"C:\Users\JanSparnaaijDenofDat\source\repos\ScoritoOdds\certificate.txt"
    )

    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_CLIENT"] = redis_client

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    return app
