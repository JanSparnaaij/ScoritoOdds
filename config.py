import os
import redis

class Config:
    # General Flask Config
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")

    # Database Configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    SQLALCHEMY_DATABASE_URI = (
        DATABASE_URL.replace("postgres://", "postgresql://")  # Handle Heroku's PostgreSQL URL
        if DATABASE_URL
        else "sqlite:///site.db"  # Fallback for local development
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis Caching
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_OPTIONS = {
        "connection_class": redis.StrictRedis,
        "ssl_ca_certs": os.getenv("SSL_CERT_PATH", "/certificate.pem"),  # Path to your certificate
        "ssl_cert_reqs": "CERT_OPTIONAL",  # Validate the certificate
    }

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    result_backend = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        "visibility_timeout": 3600,
        "ssl": {
            "ssl_cert_reqs": "CERT_OPTIONAL",  # Ensure this is correct
            "ssl_ca_certs": "/certificate.pem",  # Path to your certificate
        },
    }
    result_backend_transport_options = {
        "ssl_cert_reqs": "CERT_OPTIONAL",
        "ssl_ca_certs": "/certificate.pem",
    }
