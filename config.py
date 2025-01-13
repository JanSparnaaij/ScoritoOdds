import os

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
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")  # Redis URL fallback

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")  # Celery broker (Redis)
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")  # Celery result backend
